# PAct Arbitrary-Input Wrapper

Brickmen wraps PAct without patching the upstream checkout:

- `tools/geometry/provider_wrappers/run_pact_arbitrary_input.py`

## Why a wrapper is necessary

The verified upstream `infer_imgs.py` currently parses `--data_dir`, but then constructs:

`ImageConditioned_dataset("assets/real_world_examples")`

directly.

Brickmen therefore redirects only the dataset constructor in the running Python process. The upstream script, model pipeline, inference code, and export code remain unchanged.

## Input contract

PAct's current real-world dataset loader expects a case directory containing:

- `*_processed.png` — RGBA image;
- matching `*_mask.exr` — semantic part-label mask at the upstream boundary.

The Brickmen wrapper:
1. converts the supplied image to RGBA PNG;
2. accepts either the native semantic EXR or a lossless integer-label PNG/TIFF;
3. stages both into an isolated output-local case directory;
4. for PNG/TIFF only, redirects the exact staged mask read in-process while preserving PAct's expected `*_mask.exr` filename contract;
5. redirects PAct's hardcoded dataset root to that directory;
6. runs upstream `infer_imgs.py` with `--save_glb --export_arti_objects`.

The mask must still follow PAct's semantic-label convention. Raster convenience masks use background `0` and contiguous positive part labels `1..N`. Brickmen does not silently reinterpret labels or accept arbitrary colored visualization masks.

## Expected outputs

PAct's Singapore-style exporter writes an `object.json` articulation manifest and, when GLB export succeeds, part meshes such as:

`glb/part_<id>.glb`

Brickmen's generic provider runner classifies those as generated component candidates while preserving the upstream part IDs.

## Authority

PAct output remains generated visual/articulation evidence. It cannot overwrite validated Brickmen skeletons, hardware, contact regions, or manufacturing interfaces automatically.
