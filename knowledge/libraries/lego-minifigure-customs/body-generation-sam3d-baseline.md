# SAM 3D Objects Visual-Baseline Wrapper

Brickmen has a thin wrapper around SAM 3D Objects' published image+mask Python API:

- `tools/geometry/provider_wrappers/run_sam3d_objects_baseline.py`

The wrapper intentionally follows the public quick-start boundary:
- loads `notebook/inference.py`;
- creates `Inference(checkpoints/hf/pipeline.yaml, compile=False)`;
- uses `load_image` + `load_mask`;
- runs image+binary-mask inference;
- saves `output["gs"]` as a Gaussian PLY;
- records pose/translation/scale fields when returned.

It does **not** enable internal mesh postprocessing.

Therefore this provider is a visual/reconstruction baseline and its public quick-start output does not enter Brickmen triangle-mesh topology, keep-out or articulation collision validation.

A future SAM 3D triangle-mesh adapter should be added only if the mesh-postprocessing interface is separately verified and supported well enough to avoid relying on unstable internals.
