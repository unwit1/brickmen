# Body Reference Review UI

Brickmen reference fitting now has a lightweight review/editor for pixel-based catalog or canonical-image annotations.

Build one reviewer:

```bash
python -m tools.geometry.build_body_reference_review_ui \
  knowledge/libraries/lego-minifigure-customs/data/reference-landmarks/alpha-af325-venom-front.json \
  -o /tmp/venom-review.html
```

The HTML is self-contained **except for the source image**.

## Deliberate source-image policy

The reviewer embeds:
- the annotation JSON;
- editor code;
- overlay controls.

It does **not** embed or copy the product/catalog image.

At review time, supply:
- an image URL; or
- a local relative path.

This keeps the Brickmen repo focused on derived/provenance-aware research records instead of mirroring third-party images.

## Reviewable data

The editor supports:
- dragging skeletal landmarks;
- adding/replacing missing landmarks;
- a dedicated provisional `chest` insertion;
- confidence and notes editing;
- body bounding-box corner editing;
- silhouette-pair endpoint editing;
- silhouette-pair vertical position editing;
- JSON copy/download.

The `chest` control exists because the current seed corpus cannot distinguish:
- `lower_torso_length_scale`;
- `upper_torso_length_scale`;

without an intermediate torso landmark.

## Export boundary

Exported records:
- preserve the original source/provenance fields;
- add a `review` record;
- remain `exclude_from_production_dimensions: true`;
- explicitly state that reviewed annotations are still non-production evidence.

Review improves visual/proportion supervision. It does not create connector dimensions, tolerances, friction targets, or manufacturing authority.
