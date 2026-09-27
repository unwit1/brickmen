# PAct Semantic Mask Editor

Brickmen includes a standalone local editor for authoring PAct semantic part-label masks:

- `tools/geometry/build_pact_semantic_mask_editor.py`

Example:

```bash
python -m tools.geometry.build_pact_semantic_mask_editor \
  data/generation-conditioning/brickmen-giant-official-cad-v0.json \
  -o /tmp/giant-pact-mask-editor.html
```

Open the HTML locally, load the source image, then paint Brickmen component labels.

## Output

The editor exports:
- a lossless grayscale PNG where the pixel value is the semantic label ID;
- a JSON legend mapping label IDs back to Brickmen component-slot IDs.

For example, a Giant editor may assign:
- 0 = background;
- 1 = torso_shell;
- later labels = arm/hand/head/lower-body slots in the architecture's component-plan order.

The exact legend is embedded in the editor and exported alongside the mask.

## Privacy / provenance

The HTML does not embed a source image.

The selected local image exists only in the browser tab through a local object URL. The exported legend records that the mask is operator-authored and not automatically semantically validated.

## PAct compatibility

The Brickmen PAct wrapper accepts the exported lossless PNG and redirects the exact staged mask read to the integer label image while retaining PAct's expected `*_mask.exr` discovery filename.

This removes the need for a separate EXR authoring tool without changing PAct's internal semantic mask contract.
