# Body Generation Structural Guide Packs

External 3D providers generally accept images, masks, or model-specific parameters—not Brickmen's internal JSON directly.

Brickmen therefore has a source-image-free structural guide renderer:

- `tools/geometry/render_body_generation_guides.py`

Example:

```bash
python -m tools.geometry.render_body_generation_guides \
  data/generation-conditioning/brickmen-giant-official-cad-v0.json \
  /tmp/giant-guides \
  --sweeps data/articulation-sweeps/brickmen-giant-official-cad-v0.json
```

Outputs:
- `front.svg`
- `side.svg`
- `manifest.json`

## What the guides encode

- skeleton nodes and bones;
- visual shell envelopes;
- component-slot IDs;
- fixed mechanical reference/keep-out boxes;
- optional conservative articulation-sweep boxes.

The guides contain **no product/catalog source image**.

## Intended provider use

### Before generation
Use the guide pack to:
- plan part count;
- plan expected component labels;
- build masks or control renders;
- inspect whether the intended shell leaves room for joints/motion.

### After generation
Project returned meshes into the same frame and compare:
- part-to-slot mapping;
- shell envelope occupancy;
- joint-frame alignment;
- fixed-mm keep-out intersections;
- articulation-sweep intersections.

## Not a manufacturing drawing

The guide intentionally mixes authority classes visually:
- visual envelope controls;
- reference-only mechanical keep-outs;
- conservative motion sweeps.

The manifest remains non-production.

A provider output can visually align perfectly with a guide and still require:
- deterministic connector insertion;
- exact collision checks;
- DFM;
- physical force/torque/cycle validation.
