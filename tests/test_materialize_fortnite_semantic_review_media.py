from __future__ import annotations

import hashlib
import importlib.util
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "materialize_fortnite_semantic_review_media.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "materialize_fortnite_semantic_review_media",
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
        "batch_id": "batch-test",
        "items": [
            {
                "translation_pair_id": pair_id,
                "source_image_url": "https://fortnite-api.com/source.png",
                "lego_image_url": "https://fortnite-api.com/lego.png",
                "review_template": {
                    "schema": "fortnite-semantic-review/v1",
                    "translation_pair_id": pair_id,
                    "evidence": {
                        "source_image_url": "https://fortnite-api.com/source.png",
                        "lego_image_url": "https://fortnite-api.com/lego.png",
                        "source_image_sha256": None,
                        "lego_image_sha256": None,
                    },
                    "provenance": [],
                },
            }
        ],
    }


def test_materialization_hashes_exact_bytes_and_updates_review_evidence(
    tmp_path: Path,
) -> None:
    tool = load_tool()
    payloads = {
        "https://fortnite-api.com/source.png": b"source-image-bytes",
        "https://fortnite-api.com/lego.png": b"lego-image-bytes",
    }

    def fake_fetch(url: str):
        return payloads[url], "image/png", url

    output, manifest = tool.materialize_batch(
        batch(),
        tmp_path / "media",
        fetcher=fake_fetch,
    )

    item = output["items"][0]
    evidence = item["review_template"]["evidence"]
    source_sha = hashlib.sha256(payloads[item["source_image_url"]]).hexdigest()
    lego_sha = hashlib.sha256(payloads[item["lego_image_url"]]).hexdigest()

    assert evidence["source_image_sha256"] == source_sha
    assert evidence["lego_image_sha256"] == lego_sha
    assert item["source_image_sha256"] == source_sha
    assert item["lego_image_sha256"] == lego_sha
    assert item["source_image_local_asset"].startswith("media/")
    assert item["lego_image_local_asset"].startswith("media/")
    assert (tmp_path / item["source_image_local_asset"]).read_bytes() == payloads[
        item["source_image_url"]
    ]
    assert (tmp_path / item["lego_image_local_asset"]).read_bytes() == payloads[
        item["lego_image_url"]
    ]
    assert manifest["records"][0]["source"]["sha256"] == source_sha
    assert manifest["records"][0]["lego"]["sha256"] == lego_sha
    assert output["media_materialization"]["records"] == 1


def test_disallowed_review_media_host_is_rejected(tmp_path: Path) -> None:
    tool = load_tool()
    value = batch()
    value["items"][0]["source_image_url"] = "https://example.test/source.png"

    try:
        tool.materialize_batch(value, tmp_path / "media")
    except ValueError as exc:
        assert "host is not allowed" in str(exc)
    else:
        raise AssertionError("expected disallowed media host to fail")


def test_empty_batch_is_rejected(tmp_path: Path) -> None:
    tool = load_tool()

    try:
        tool.materialize_batch({"items": []}, tmp_path / "media")
    except ValueError as exc:
        assert "at least one review item" in str(exc)
    else:
        raise AssertionError("expected empty batch to fail")


def test_materializer_refuses_changed_bytes_in_pinned_second_review(tmp_path):
    import pytest
    tool = load_tool()
    candidate = batch()
    candidate["items"][0]["review_template"]["evidence"]["source_image_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="exact evidence hash mismatch"):
        tool.materialize_batch(candidate, tmp_path, fetcher=lambda url: (b"changed image bytes", "image/png", url))
    assert not list(tmp_path.glob("*.png"))


def test_item_pin_is_enforced_and_cannot_conflict_with_template(tmp_path):
    tool = load_tool()
    value = batch()
    item = value['items'][0]
    item['source_image_sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='exact evidence hash mismatch'):
        tool.materialize_batch(value, tmp_path, fetcher=lambda url:(b'changed bytes','image/png',url))
    item['review_template']['evidence']['source_image_sha256'] = 'b' * 64
    def no_fetch(url): raise AssertionError('Conflicting pins must fail before network access')
    with pytest.raises(ValueError, match='conflicting item/template'):
        tool.materialize_batch(value, tmp_path, fetcher=no_fetch)


def preserved_batch(tmp_path):
    tool=load_tool()
    root=tmp_path/'archive'
    pinned,manifest=tool.materialize_batch(batch(),root/'media',fetcher=lambda url:(url.encode(),'image/png',url))
    return tool,pinned,manifest,root


def test_archived_exact_bytes_rebuild_blind_batch_without_network(tmp_path):
    tool,pinned,manifest,root=preserved_batch(tmp_path)
    pinned['batch_id']='different-independent-review-batch'
    pinned['items'][0]['review_template']['annotations']={'regions':{},'identity_critical_features':[]}
    def no_fetch(url):raise AssertionError('Archive reuse must not fetch mutable URLs')
    output,reused=tool.materialize_batch(pinned,tmp_path/'rebuilt/media',fetcher=no_fetch,archive_manifest=manifest,archive_root=root)
    for role in ('source','lego'):
        entry=reused['records'][0][role]
        assert entry['sha256']==manifest['records'][0][role]['sha256']
        assert entry['acquisition']=='verified_archive'
        assert (tmp_path/'rebuilt'/entry['local_asset']).read_bytes()==(root/manifest['records'][0][role]['local_asset']).read_bytes()
    assert output['items'][0]['review_template']['annotations']=={'regions':{},'identity_critical_features':[]}
    assert 'training_eligible' not in output


@pytest.mark.parametrize('mutation,error', [
    (lambda m:m['records'][0]['source'].update(url='https://fortnite-api.com/other.png'),'archived source URL'),
    (lambda m:m['records'][0]['source'].update(sha256='a'*64),'hash mismatch for archived'),
    (lambda m:m['records'][0]['source'].update(local_asset='../outside.png'),'escapes archive root'),
    (lambda m:m['records'][0].pop('source'),'archived source URL'),
    (lambda m:m['records'].append(copy.deepcopy(m['records'][0])),'Duplicate archive pair'),
])
def test_conflicting_or_unsafe_archives_fail_without_network(tmp_path,mutation,error):
    tool,pinned,manifest,root=preserved_batch(tmp_path)
    mutation(manifest)
    def no_fetch(url):raise AssertionError('Invalid archive must not fall back to network')
    with pytest.raises(ValueError,match=error):
        tool.materialize_batch(pinned,tmp_path/'rebuilt/media',fetcher=no_fetch,archive_manifest=manifest,archive_root=root)


def test_corrupted_archive_bytes_and_half_supplied_configuration_fail(tmp_path):
    tool,pinned,manifest,root=preserved_batch(tmp_path)
    (root/manifest['records'][0]['source']['local_asset']).write_bytes(b'corrupted')
    with pytest.raises(ValueError,match='exact evidence hash mismatch'):
        tool.materialize_batch(pinned,tmp_path/'rebuilt/media',archive_manifest=manifest,archive_root=root)
    with pytest.raises(ValueError,match='supplied together'):
        tool.materialize_batch(pinned,tmp_path/'rebuilt/media',archive_manifest=manifest)


def test_failed_archive_rerun_removes_stale_metadata_and_protects_input(tmp_path):
    tool,pinned,manifest,root=preserved_batch(tmp_path)
    source=tmp_path/'batch.json';source.write_text(json.dumps(pinned))
    archive=tmp_path/'archive.json';archive.write_text(json.dumps(manifest))
    output=tmp_path/'result.json';report=tmp_path/'manifest.json'
    command=[sys.executable,str(TOOL),'--batch',str(source),'--output-dir',str(tmp_path/'rebuilt/media'),'--output-batch',str(output),'--manifest',str(report),'--archive-manifest',str(archive),'--archive-root',str(root)]
    assert subprocess.run(command,capture_output=True).returncode==0
    (root/manifest['records'][0]['source']['local_asset']).write_bytes(b'changed')
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==2
    assert 'hash mismatch' in result.stderr
    assert not output.exists() and not report.exists()
    # The CLI must reject overlapping output and source evidence before cleanup.
    command[command.index('--output-batch')+1]=str(source)
    original=source.read_bytes()
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==2 and 'must not overwrite input' in result.stderr
    assert source.read_bytes()==original
