from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "build_fortnite_semantic_review_ui.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_fortnite_semantic_review_ui",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def batch() -> dict:
    pair_id = "fortnitepair-test"
    return {
        "schema": "fortnite-semantic-review-work-batch/v1",
        "processor_version": "fortnite-semantic-review-work-batch/v1",
        "batch_id": "batch-test",
        "mode": "first_review",
        "offset": 0,
        "limit": 1,
        "min_priority_score": 6.0,
        "selected_records": 1,
        "reviewer_id": "unassigned",
        "reviewer_type": "human",
        "items": [
            {
                "translation_pair_id": pair_id,
                "review_priority_score": 10,
                "lego_image_resolution": "direct_pair",
                "source_image_url": "https://example.test/source.png",
                "lego_image_url": "https://example.test/lego.png",
                "measurement_signals": [
                    {
                        "signal": "palette_reduction",
                        "region": "torso",
                        "value": -2,
                    }
                ],
                "measurement_signal_policy": (
                    "Signals only prioritize review and must not be copied into semantic "
                    "labels without direct visual evidence."
                ),
                "review_template": {
                    "schema": "fortnite-semantic-review/v1",
                    "review_id": None,
                    "translation_pair_id": pair_id,
                    "reviewer": {
                        "reviewer_type": "human",
                        "reviewer_id": "unassigned",
                        "model_id": None,
                        "model_revision": None,
                        "review_role": "reviewer",
                    },
                    "evidence": {
                        "source_image_url": "https://example.test/source.png",
                        "lego_image_url": "https://example.test/lego.png",
                        "source_image_sha256": None,
                        "lego_image_sha256": None,
                        "evidence_scope": "front_pair",
                        "claims_unobserved_surfaces": False,
                    },
                    "annotations": {
                        "regions": {
                            "head": [],
                            "torso": [],
                            "lower_body": [],
                            "accessory_or_silhouette": [],
                        },
                        "identity_critical_features": [],
                        "mask_headgear_route": None,
                        "expression_translation": None,
                    },
                    "limitations": [],
                    "measurement_signal_refs": [
                        {
                            "signal": "palette_reduction",
                            "region": "torso",
                            "value": -2,
                            "role": "review_prioritization_only",
                        }
                    ],
                    "review_status": "draft",
                    "adjudicates_review_ids": [],
                    "created_at": None,
                    "provenance": [],
                },
            }
        ],
        "policy": [],
    }


def test_valid_batch_builds_standalone_review_html() -> None:
    tool = load_tool()
    value = batch()

    html = tool.build_review_html(value)

    assert "Brickmen Semantic Review" in html
    assert "https://example.test/source.png" in html
    assert "https://example.test/lego.png" in html
    assert "localStorage" in html
    assert "Export JSONL" in html
    assert "claims_unobserved_surfaces=false" in html
    assert "Measurement signals" in html
    assert "prioritization only" in html


def test_materialized_batch_prefers_local_exact_media() -> None:
    tool = load_tool()
    value = batch()
    item = value["items"][0]
    item["source_image_local_asset"] = "media/source--abc.png"
    item["lego_image_local_asset"] = "media/lego--def.png"
    item["source_image_sha256"] = "a" * 64
    item["lego_image_sha256"] = "b" * 64

    html = tool.build_review_html(value)

    assert "loadReviewedImages(item)" in html
    assert "await verifyImageBytes(bytes,item,role)" in html
    assert "sha256" in html
    assert "media/source--abc.png" in html
    assert "media/lego--def.png" in html


@pytest.mark.parametrize('mutation,error', [
    (lambda i:i.update(source_image_sha256='bad'),'invalid source evidence hash'),
    (lambda i:i['review_template']['evidence'].update(source_image_sha256='b'*64),'conflicting source evidence hashes'),
    (lambda i:i['review_template']['evidence'].update(source_image_url='https://example.test/other.png'),'conflicting source evidence URLs'),
    (lambda i:i.update(source_image_local_asset='../other.png'),'relative to the review folder'),
    (lambda i:i.update(source_image_local_asset='https://example.test/other.png'),'relative to the review folder'),
])
def test_conflicting_pins_and_escaping_media_paths_fail_before_build(mutation,error):
    value=batch();value['items'][0]['source_image_sha256']='a'*64
    mutation(value['items'][0])
    with pytest.raises(ValueError,match=error):load_tool().build_review_html(value)


def test_actual_browser_hash_helpers_reject_changed_bytes_and_stale_review_proof():
    node=shutil.which('node')
    if not node:pytest.skip('Node is needed to exercise browser WebCrypto helpers')
    page=load_tool().build_review_html(batch())
    helpers=page.split('// BEGIN MEDIA BINDING HELPERS')[1].split('// END MEDIA BINDING HELPERS')[0]
    data=b'exact synthetic image bytes';sha=hashlib.sha256(data).hexdigest()
    item=batch()['items'][0]
    for role in ('source','lego'):
        item[role+'_image_sha256']=sha.upper()
        item['review_template']['evidence'][role+'_image_sha256']=sha
    harness='import {webcrypto} from "node:crypto"; import assert from "node:assert/strict"; Object.defineProperty(globalThis,"crypto",{value:webcrypto});\n'+helpers
    harness+='\nconst item='+json.dumps(item)+'; const bytes=new TextEncoder().encode('+json.dumps(data.decode())+');\n'
    harness+='''
assert.equal(await verifyImageBytes(bytes,item,'source'),expectedMediaHash(item,'source'));
await assert.rejects(verifyImageBytes(new TextEncoder().encode('changed'),item,'source'),/differs from the reviewed version/);
const conflict=structuredClone(item);conflict.source_image_sha256='b'.repeat(64);
assert.throws(()=>expectedMediaHash(conflict,'source'),/Conflicting/);
const absent=structuredClone(item);delete absent.source_image_sha256;delete absent.review_template.evidence.source_image_sha256;
assert.throws(()=>expectedMediaHash(absent,'source'),/Materialize/);
const invalid=structuredClone(item);invalid.source_image_sha256='bad';
assert.throws(()=>expectedMediaHash(invalid,'source'),/Materialize/);
const hash=expectedMediaHash(item,'source');
const record={evidence:{source_image_sha256:hash,lego_image_sha256:hash},provenance:[]};
assert.equal(hasVerifiedProvenance(record,item),false);
record.provenance=[{source:'browser_verified_exact_media',processor_version:'fortnite-semantic-review-ui/v2',source_image_sha256:hash,lego_image_sha256:hash}];
assert.equal(hasVerifiedProvenance(record,item),true);
record.evidence.lego_image_sha256='b'.repeat(64);assert.equal(hasVerifiedProvenance(record,item),false);
record.evidence.lego_image_sha256=hash;record.provenance[0].processor_version='fortnite-semantic-review-ui/v1';assert.equal(hasVerifiedProvenance(record,item),false);
const edited=structuredClone(record);edited.annotations={regions:{head:[{feature:'changed face'}]}};
assert.notEqual(reviewedPayload(edited),reviewedPayload(record));
'''
    result=subprocess.run([node,'--input-type=module','-e',harness],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_generated_page_script_parses_after_rendering_and_navigation_preserves_edits():
    node=shutil.which('node')
    if not node:pytest.skip('Node is needed to parse generated JavaScript')
    page=load_tool().build_review_html(batch())
    script=page.split('<script>')[1].split('</script>')[0]
    result=subprocess.run([node,'--check','-'],input=script,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'if(!saveIfChanged())return' in script
    assert 'record.review_status="draft";record.created_at=null' in script
    assert 'JSON.parse(row.dataset.notes||"null")' in script


def test_batch_validation_rejects_missing_items() -> None:
    tool = load_tool()
    value = batch()
    value["items"] = []
    value["selected_records"] = 0

    try:
        tool.validate_batch(value)
    except ValueError as exc:
        assert "at least one item" in str(exc)
    else:
        raise AssertionError("expected empty batch to be rejected")


def test_batch_validation_rejects_record_count_drift() -> None:
    tool = load_tool()
    value = batch()
    value["selected_records"] = 2

    try:
        tool.validate_batch(value)
    except ValueError as exc:
        assert "selected_records" in str(exc)
    else:
        raise AssertionError("expected selected_records mismatch to be rejected")


def test_batch_validation_rejects_unobserved_surface_claims() -> None:
    tool = load_tool()
    value = batch()
    value["items"][0]["review_template"]["evidence"][
        "claims_unobserved_surfaces"
    ] = True

    try:
        tool.validate_batch(value)
    except ValueError as exc:
        assert "claims_unobserved_surfaces" in str(exc)
    else:
        raise AssertionError("expected hidden-surface claims to be rejected")


def test_script_json_prevents_script_breakout() -> None:
    tool = load_tool()
    encoded = tool._script_json({"x": "</script><!--"})

    assert "</script>" not in encoded
    assert "<!--" not in encoded
    assert json.loads(encoded) == {"x": "</script><!--"}
    assert "<" not in encoded


def test_checked_in_first_batch_builds_ui() -> None:
    tool = load_tool()
    root = Path(__file__).resolve().parents[1]
    batch_path = (
        root
        / "knowledge"
        / "libraries"
        / "lego-minifigure-customs"
        / "data"
        / "semantic-review-batches"
        / "fortnite-first-review-batch-0001.json"
    )
    import json

    value = json.loads(batch_path.read_text(encoding="utf-8"))
    html = tool.build_review_html(value)

    assert value["selected_records"] == 25
    assert value["batch_id"] in html
    assert html.count("review_prioritization_only") >= 25
