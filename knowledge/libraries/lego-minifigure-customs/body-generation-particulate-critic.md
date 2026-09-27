# Particulate Critic Ingestion

Brickmen can normalize Particulate's evaluation artifacts without adding NumPy as a core geometry-CI dependency:

- `tools/geometry/read_numeric_npz.py`
- `tools/geometry/ingest_particulate_critic.py`
- schema: `data/body-particulate-critic-report.schema.json`

The ingester reads Particulate's current `pred.npz` fields:
- `face_part_ids`;
- `motion_hierarchy`;
- `is_part_revolute`;
- `is_part_prismatic`;
- `revolute_plucker`;
- `revolute_range`;
- `prismatic_axis`;
- `prismatic_range`.

When `pred.obj` is supplied, it also derives a prediction-frame AABB for every inferred part from face membership.

Revolute Plücker coordinates are converted to the same axis/point interpretation used by upstream Particulate:
- direction = normalized first three Plücker values;
- point = cross(moment, direction).

## Authority

The normalized critic report remains auxiliary learned evidence.

Before comparing an inferred axis to Brickmen:
1. map inferred part IDs to Brickmen component slots;
2. register the Particulate prediction frame to Brickmen mm;
3. transform axes/points;
4. compare hierarchy/joint type/range;
5. retain disagreements rather than overwriting validated Brickmen records.
