from copy import deepcopy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
import pytest

from tools.knowledge.evaluate_generation_output import VERSION, evaluate


def mask(tmp_path, name, values, size=(2, 2)):
    path = tmp_path / f"{name}.png"
    image = Image.new("L", size)
    image.putdata(values)
    image.save(path)
    return {"local_path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def request(tmp_path):
    return {"schema": VERSION, "registration_status": "reviewed", "alignment_id": "synthetic-grid-v1",
            "assets": {"reference_silhouette": mask(tmp_path, "ref", [255, 255, 0, 0]),
                       "candidate_silhouette": mask(tmp_path, "candidate", [255, 0, 255, 0])}}


def test_drift_and_named_landmarks_have_observable_errors(tmp_path):
    req = request(tmp_path)
    req["landmarks"] = {"reference": {"left_eye": [0, 0], "right_eye": [1, 0]},
                        "candidate": {"left_eye": [0, 1], "right_eye": [1, 0]}}
    req["thresholds"] = {"silhouette_iou": .9, "landmark_max_error": .1}
    report = evaluate(req, tmp_path)
    assert report["measurements"]["silhouette_iou"] == pytest.approx(1 / 3)
    assert report["measurements"]["landmark_error"] == pytest.approx(.5 / (8 ** .5))
    assert report["measurements"]["landmark_max_error"] == pytest.approx(1 / (8 ** .5))
    assert report["status"] == "technical_checks_failed"


def test_matching_silhouette_never_promotes_semantic_or_physical_accuracy(tmp_path):
    req = request(tmp_path)
    req["assets"]["candidate_silhouette"] = deepcopy(req["assets"]["reference_silhouette"])
    req["thresholds"] = {"silhouette_iou": 1}
    report = evaluate(req, tmp_path)
    assert report["status"] == "technical_checks_passed"
    assert report["semantic_features"] == "unreviewed"
    assert report["physical_fit"] == "unvalidated"
    assert evaluate({k: v for k, v in req.items() if k != "thresholds"}, tmp_path)["status"] == "measurements_only"


def test_keepout_is_checked_even_inside_safe_region(tmp_path):
    req = request(tmp_path)
    req["assets"] = {"art_mask": mask(tmp_path, "art", [255, 255, 255, 0]),
                     "safe_zone": mask(tmp_path, "safe", [255, 255, 0, 0]),
                     "keepout_mask": mask(tmp_path, "keepout", [0, 255, 0, 0])}
    report = evaluate(req, tmp_path)
    assert report["measurements"]["print_zone_containment"] == pytest.approx(1 / 3)
    assert report["measurements"]["art_outside_safe_zone_pixels"] == 2
    assert report["measurements"]["art_in_keepout_pixels"] == 1


@pytest.mark.parametrize("mutation,error", [
    (lambda r: r.update(registration_status="unknown"), "reviewed registration"),
    (lambda r: r["assets"]["candidate_silhouette"].update(sha256="stale"), "hash missing or mismatched"),
    (lambda r: r.update(thresholds={"silhouette_iou": True}), "finite values"),
    (lambda r: r.update(thresholds={"silhouette_iou": float("nan")}), "finite values"),
    (lambda r: r.update(thresholds={"landmark_error": .1}), "no measured input"),
    (lambda r: r.update(landmarks={"reference": {"eye": [0, 0]}, "candidate": {"nose": [0, 0]}}), "labels must match"),
    (lambda r: r.update(landmarks={"reference": {"eye": [0, 0]}, "candidate": {"eye": [2, 0]}}), "outside the registered image"),
])
def test_invalid_evidence_and_measurement_configuration_fail(tmp_path, mutation, error):
    req = request(tmp_path)
    mutation(req)
    with pytest.raises(ValueError, match=error):
        evaluate(req, tmp_path)


def test_grid_mismatch_and_antialiased_masks_are_not_silently_normalized(tmp_path):
    req = request(tmp_path)
    req["assets"]["candidate_silhouette"] = mask(tmp_path, "different-grid", [255], (1, 1))
    with pytest.raises(ValueError, match="exact registered pixel grid"):
        evaluate(req, tmp_path)
    req["assets"]["candidate_silhouette"] = mask(tmp_path, "gray", [255, 127, 0, 0])
    with pytest.raises(ValueError, match="nonbinary"):
        evaluate(req, tmp_path)


def test_missing_art_cannot_pass_containment(tmp_path):
    req = request(tmp_path)
    req["assets"] = {"art_mask": mask(tmp_path, "empty", [0] * 4), "safe_zone": mask(tmp_path, "safe", [255] * 4)}
    with pytest.raises(ValueError, match="absent design"):
        evaluate(req, tmp_path)


def test_failed_rerun_replaces_stale_success_report(tmp_path):
    req = request(tmp_path)
    path, output = tmp_path / "request.json", tmp_path / "report.json"
    path.write_text(json.dumps(req))
    command = [sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "tools/knowledge/evaluate_generation_output.py"), "--request", str(path), "--output", str(output)]
    assert subprocess.run(command, capture_output=True).returncode == 0
    path.write_text("{broken")
    assert subprocess.run(command, capture_output=True).returncode == 2
    assert json.loads(output.read_text())["status"] == "blocked"
