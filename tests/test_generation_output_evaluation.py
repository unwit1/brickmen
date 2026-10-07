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
    assert report["provenance_status"] == "masks_only"
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


def bound_request(tmp_path):
    req = request(tmp_path)
    images, pins = {}, {}
    for role, color in (("reference", "red"), ("candidate", "blue")):
        path = tmp_path / f"{role}-image.png"
        Image.new("RGB", (2, 2), color).save(path)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        images[role] = {"local_path": path.name, "sha256": sha}
        pins[role] = {"image_sha256": sha, "original_dimensions_px": [2, 2]}
    req["provenance"] = {"source_images": images}
    registration = {"schema": "brickmen-registration-evidence/v1", "alignment_id": req["alignment_id"],
                    "reviewer": "synthetic-test-reviewer", "review_notes": ["Synthetic provenance fixture, not segmentation truth."],
                    "mask_derivation": {"method": "supplied synthetic masks"}, "source_images": pins,
                    "pixel_grid": [2, 2], "mask_sha256": {role: asset["sha256"] for role, asset in req["assets"].items()},
                    "landmarks": None}
    pin_registration(tmp_path, req, registration)
    return req, registration


def pin_registration(tmp_path, req, registration):
    path = tmp_path / "registration.json"
    path.write_text(json.dumps(registration))
    req["provenance"]["registration"] = {"local_path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def test_source_and_registration_bytes_are_bound_without_semantic_promotion(tmp_path):
    req, _ = bound_request(tmp_path)
    result = evaluate(req, tmp_path)
    assert result["provenance_status"] == "verified_byte_bindings_as_declared"
    assert result["source_image_sha256"] == {role: asset["sha256"] for role, asset in req["provenance"]["source_images"].items()}
    assert result["registration_evidence_sha256"] == req["provenance"]["registration"]["sha256"]
    assert result["semantic_features"] == "unreviewed"
    assert result["physical_fit"] == "unvalidated"


def test_native_dimensions_are_checked_independently_of_registered_mask_grid(tmp_path):
    req, registration = color_request(tmp_path, size=(3, 2))
    req["candidate_dimensions_px"] = [2, 2]
    registration["candidate_dimensions_px"] = [2, 2]
    pin_registration(tmp_path, req, registration)
    report = evaluate(req, tmp_path)
    assert report["pixel_grid"] == [2, 2]
    assert report["measurements"]["silhouette_iou"] == 1
    assert report["flat_color_regions"][0]["match_fraction"] == 1
    assert report["native_candidate_dimensions_px"] == [3, 2]
    assert report["status"] == "technical_checks_failed"
    dimension_check = next(c for c in report["checks"] if c.get("constraint") == "candidate_dimensions_px")
    assert dimension_check["passed"] is False
    req["candidate_dimensions_px"] = registration["candidate_dimensions_px"] = [3, 2]
    pin_registration(tmp_path, req, registration)
    assert evaluate(req, tmp_path)["status"] == "technical_checks_passed"


def test_native_dimensions_do_not_require_flat_color_sampling(tmp_path):
    req, registration = bound_request(tmp_path)
    req["candidate_dimensions_px"] = registration["candidate_dimensions_px"] = [2, 2]
    pin_registration(tmp_path, req, registration)
    report = evaluate(req, tmp_path)
    assert report["status"] == "technical_checks_passed"
    assert report["native_candidate_dimensions_px"] == [2, 2]
    assert "flat_color_regions" not in report
    assert report["semantic_features"] == "unreviewed"


@pytest.mark.parametrize("dimensions", [None, [], [2], [2, 2, 2], [True, 2], [2.0, 2], [0, 2], [2, -1]])
def test_native_dimensions_require_positive_integer_pair(tmp_path, dimensions):
    req, registration = bound_request(tmp_path)
    req["candidate_dimensions_px"] = registration["candidate_dimensions_px"] = dimensions
    pin_registration(tmp_path, req, registration)
    with pytest.raises(ValueError, match="two positive integer"):
        evaluate(req, tmp_path)


def test_native_dimensions_require_matching_registration_and_original_bytes(tmp_path):
    req = request(tmp_path)
    req["candidate_dimensions_px"] = [2, 2]
    with pytest.raises(ValueError, match="byte-bound"):
        evaluate(req, tmp_path)
    req, registration = bound_request(tmp_path)
    req["candidate_dimensions_px"] = [2, 2]
    with pytest.raises(ValueError, match="dimensions constraint differs"):
        evaluate(req, tmp_path)
    registration["candidate_dimensions_px"] = [3, 2]
    pin_registration(tmp_path, req, registration)
    with pytest.raises(ValueError, match="dimensions constraint differs"):
        evaluate(req, tmp_path)


def test_cli_rejects_wrong_native_size_despite_passing_registered_silhouette(tmp_path):
    req, registration = color_request(tmp_path)
    req["candidate_dimensions_px"] = registration["candidate_dimensions_px"] = [2, 2]
    pin_registration(tmp_path, req, registration)
    path, output = tmp_path / "request.json", tmp_path / "report.json"
    path.write_text(json.dumps(req))
    command = [sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "tools/knowledge/evaluate_generation_output.py"),
               "--request", str(path), "--output", str(output)]
    assert subprocess.run(command, capture_output=True).returncode == 2
    assert json.loads(output.read_text())["status"] == "technical_checks_failed"


def test_native_dimension_constraint_rejects_animation_without_color_constraint(tmp_path):
    req, registration = bound_request(tmp_path)
    path = tmp_path / "candidate-image.png"
    Image.new("RGBA", (2, 2), "red").save(path, save_all=True,
        append_images=[Image.new("RGBA", (2, 2), "blue")], duration=100, loop=0)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    req["provenance"]["source_images"]["candidate"]["sha256"] = sha
    registration["source_images"]["candidate"]["image_sha256"] = sha
    req["candidate_dimensions_px"] = registration["candidate_dimensions_px"] = [2, 2]
    pin_registration(tmp_path, req, registration)
    with pytest.raises(ValueError, match="single-frame"):
        evaluate(req, tmp_path)


def test_changed_candidate_cannot_reuse_old_registered_masks(tmp_path):
    req, _ = bound_request(tmp_path)
    path = tmp_path / req["provenance"]["source_images"]["candidate"]["local_path"]
    Image.new("RGB", (2, 2), "green").save(path)
    with pytest.raises(ValueError, match="source image candidate hash"):
        evaluate(req, tmp_path)
    req["provenance"]["source_images"]["candidate"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Registration source image pin differs"):
        evaluate(req, tmp_path)


@pytest.mark.parametrize("mutation,error", [
    (lambda r: r.update(alignment_id="other-camera"), "alignment_id differs"),
    (lambda r: r.update(mask_sha256={}), "mask pins or pixel grid"),
    (lambda r: r.update(pixel_grid=[3, 2]), "mask pins or pixel grid"),
    (lambda r: r.update(landmarks={"reference": {"eye": [0, 0]}, "candidate": {"eye": [0, 1]}}), "landmarks differ"),
    (lambda r: r.update(review_notes=[]), "requires reviewer"),
    (lambda r: r["source_images"]["candidate"].update(original_dimensions_px=[3, 2]), "source image pin differs"),
])
def test_registration_must_match_measured_evidence(tmp_path, mutation, error):
    req, registration = bound_request(tmp_path)
    mutation(registration)
    pin_registration(tmp_path, req, registration)
    with pytest.raises(ValueError, match=error):
        evaluate(req, tmp_path)


def test_missing_reference_source_or_changed_registration_is_rejected(tmp_path):
    req, _ = bound_request(tmp_path)
    del req["provenance"]["source_images"]["reference"]
    with pytest.raises(ValueError, match="missing a measured reference"):
        evaluate(req, tmp_path)
    req, _ = bound_request(tmp_path)
    (tmp_path / "registration.json").write_text("{}")
    with pytest.raises(ValueError, match="registration evidence hash"):
        evaluate(req, tmp_path)


def color_request(tmp_path, pixels=None, size=(3, 2)):
    req, registration = bound_request(tmp_path)
    path = tmp_path / "candidate-image.png"
    image = Image.new("RGBA", size, (153, 153, 153, 255))
    if pixels is not None:
        image.putdata(pixels)
    image.save(path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    req["provenance"]["source_images"]["candidate"]["sha256"] = sha
    registration["source_images"]["candidate"] = {"image_sha256": sha, "original_dimensions_px": list(size)}
    req["flat_color"] = {"interpretation": "decoded_rgba_bytes", "regions": [
        {"id": "plain-forehead", "box_px": [1, 0, 3, 2], "target_rgba": [153, 153, 153, 255],
         "max_channel_delta": 0, "minimum_match_fraction": 1}]}
    registration["flat_color"] = deepcopy(req["flat_color"])
    pin_registration(tmp_path, req, registration)
    req["assets"]["candidate_silhouette"] = deepcopy(req["assets"]["reference_silhouette"])
    registration["mask_sha256"] = {role: asset["sha256"] for role, asset in req["assets"].items()}
    pin_registration(tmp_path, req, registration)
    req["thresholds"] = {"silhouette_iou": 1}
    return req, registration


def test_native_color_roi_is_not_scaled_to_registered_mask_grid(tmp_path):
    req, _ = color_request(tmp_path, [(0, 0, 0, 0), (153, 153, 153, 255), (153, 153, 153, 255)] * 2)
    report = evaluate(req, tmp_path)
    assert report["pixel_grid"] == [2, 2]
    assert report["flat_color_candidate_dimensions_px"] == [3, 2]
    region = report["flat_color_regions"][0]
    assert region["sampled_pixels"] == region["matching_pixels"] == 4
    assert region["unique_rgba_values"] == 1
    assert report["status"] == "technical_checks_passed"
    assert report["semantic_features"] == "unreviewed"
    assert report["physical_fit"] == "unvalidated"


@pytest.mark.parametrize("bad_pixel", [(154, 153, 153, 255), (153, 153, 153, 254)])
def test_shading_or_interior_alpha_fails_even_when_silhouette_passes(tmp_path, bad_pixel):
    pixels = [(153, 153, 153, 255)] * 6
    pixels[1] = bad_pixel
    req, _ = color_request(tmp_path, pixels)
    report = evaluate(req, tmp_path)
    assert report["checks"][0]["passed"] is True
    assert report["checks"][1]["passed"] is False
    assert report["flat_color_regions"][0]["match_fraction"] == .75
    assert report["flat_color_regions"][0]["observed_max_channel_delta"] == 1
    assert report["status"] == "technical_checks_failed"


def test_color_tolerance_is_explicit_and_bound_to_registration(tmp_path):
    req, registration = color_request(tmp_path, [(154, 153, 153, 254)] * 6)
    req["flat_color"]["regions"][0]["max_channel_delta"] = 1
    with pytest.raises(ValueError, match="flat color regions differ"):
        evaluate(req, tmp_path)
    registration["flat_color"] = deepcopy(req["flat_color"])
    pin_registration(tmp_path, req, registration)
    assert evaluate(req, tmp_path)["status"] == "technical_checks_passed"


@pytest.mark.parametrize("mutation,error", [
    (lambda c: c.update(interpretation="physical_color"), "decoded_rgba_bytes"),
    (lambda c: c.update(regions=[]), "nonempty regions"),
    (lambda c: c["regions"][0].update(box_px=[0, 0, 0, 2]), "nonempty integer rectangle"),
    (lambda c: c["regions"][0].update(box_px=[0, 0, 4, 2]), "native candidate image"),
    (lambda c: c["regions"][0].update(box_px=[True, 0, 3, 2]), "integer rectangle"),
    (lambda c: c["regions"][0].update(target_rgba=[153, 153, 153, True]), "integer bytes"),
    (lambda c: c["regions"][0].update(max_channel_delta=True), "integer byte distance"),
    (lambda c: c["regions"][0].update(minimum_match_fraction=0), "finite in"),
    (lambda c: c["regions"][0].update(minimum_match_fraction=float("nan")), "finite in"),
    (lambda c: c["regions"][0].update(minimum_match_fraction=True), "finite in"),
    (lambda c: c["regions"].append(deepcopy(c["regions"][0])), "nonempty and unique"),
])
def test_invalid_native_color_regions_cannot_silently_pass(tmp_path, mutation, error):
    req, registration = color_request(tmp_path)
    mutation(req["flat_color"])
    registration["flat_color"] = deepcopy(req["flat_color"])
    pin_registration(tmp_path, req, registration)
    with pytest.raises(ValueError, match=error):
        evaluate(req, tmp_path)


def test_color_requires_original_image_and_reviewed_region_binding(tmp_path):
    req, registration = color_request(tmp_path)
    del req["provenance"]
    with pytest.raises(ValueError, match="byte-bound source image"):
        evaluate(req, tmp_path)
    req, registration = color_request(tmp_path)
    del registration["flat_color"]
    pin_registration(tmp_path, req, registration)
    with pytest.raises(ValueError, match="flat color regions differ"):
        evaluate(req, tmp_path)


def test_cli_color_failure_has_nonzero_exit_and_retains_measurements(tmp_path):
    req, _ = color_request(tmp_path, [(153, 153, 153, 254)] * 6)
    path, output = tmp_path / "request.json", tmp_path / "report.json"
    path.write_text(json.dumps(req))
    result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "tools/knowledge/evaluate_generation_output.py"),
                             "--request", str(path), "--output", str(output)], capture_output=True)
    assert result.returncode == 2
    report = json.loads(output.read_text())
    assert report["status"] == "technical_checks_failed"
    assert report["flat_color_regions"][0]["matching_pixels"] == 0


def test_each_color_region_fails_individually_instead_of_averaging(tmp_path):
    req, registration = color_request(tmp_path, [(0, 0, 0, 0), (153, 153, 153, 255), (153, 153, 153, 255)] * 2)
    req["flat_color"]["regions"].append({"id": "bad-interior", "box_px": [0, 0, 1, 2],
        "target_rgba": [153, 153, 153, 255], "max_channel_delta": 0, "minimum_match_fraction": 1})
    registration["flat_color"] = deepcopy(req["flat_color"])
    pin_registration(tmp_path, req, registration)
    report = evaluate(req, tmp_path)
    assert [c["passed"] for c in report["checks"] if "region_id" in c] == [True, False]
    assert report["status"] == "technical_checks_failed"


@pytest.mark.parametrize("mode,accepted", [("RGB", True), ("P", False)])
def test_color_mode_is_explicit_and_rgb_has_opaque_alpha(tmp_path, mode, accepted):
    req, registration = color_request(tmp_path)
    path = tmp_path / "candidate-image.png"
    with Image.open(path) as original:
        original.convert(mode).save(tmp_path / "converted.png")
    path.write_bytes((tmp_path / "converted.png").read_bytes())
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    req["provenance"]["source_images"]["candidate"]["sha256"] = sha
    registration["source_images"]["candidate"]["image_sha256"] = sha
    pin_registration(tmp_path, req, registration)
    if accepted:
        assert evaluate(req, tmp_path)["flat_color_regions"][0]["observed_alpha_range"] == [255, 255]
    else:
        with pytest.raises(ValueError, match="single-frame RGB or RGBA"):
            evaluate(req, tmp_path)


def test_animated_image_cannot_pass_by_sampling_only_first_frame(tmp_path):
    req, registration = color_request(tmp_path)
    path = tmp_path / "candidate-image.png"
    Image.new("RGBA", (3, 2), (153, 153, 153, 255)).save(path, save_all=True,
        append_images=[Image.new("RGBA", (3, 2), "red")], duration=100, loop=0)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    req["provenance"]["source_images"]["candidate"]["sha256"] = sha
    registration["source_images"]["candidate"]["image_sha256"] = sha
    pin_registration(tmp_path, req, registration)
    with pytest.raises(ValueError, match="single-frame RGB or RGBA"):
        evaluate(req, tmp_path)


@pytest.mark.parametrize("role", ["mask", "candidate", "registration"])
def test_cli_cannot_replace_original_evidence_with_report(tmp_path, role):
    req, _ = color_request(tmp_path)
    asset = req["assets"]["reference_silhouette"] if role == "mask" else (
        req["provenance"]["registration"] if role == "registration" else req["provenance"]["source_images"]["candidate"])
    output = tmp_path / asset["local_path"]
    original = output.read_bytes()
    path = tmp_path / "request.json"
    path.write_text(json.dumps(req))
    result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "tools/knowledge/evaluate_generation_output.py"),
                             "--request", str(path), "--output", str(output)], capture_output=True)
    assert result.returncode == 2
    assert b"must not overwrite an evidence input" in result.stderr
    assert output.read_bytes() == original
