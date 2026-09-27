# Particulate Semantic Mapping and Architecture Comparison

After Particulate critic ingestion, Brickmen can:

1. propose predicted-part IDs → Brickmen component-slot mappings from per-part geometry;
2. choose/review one mapping candidate;
3. transform Particulate predicted axes into the Brickmen-mm frame;
4. compare the inferred hierarchy to the architecture's explicit joint-component bindings.

Tools:
- `tools/geometry/propose_particulate_semantic_mapping.py`
- `tools/geometry/compare_particulate_to_body_architecture.py`

The comparison reports:
- expected vs predicted inter-component graph edges;
- missing/extra critic edges;
- expected Brickmen joint for each matched edge;
- critic motion class;
- revolute-axis direction error;
- predicted axis-line distance to the Brickmen pivot;
- critic vs Brickmen revolute range span.

## Combined-slot joints

Architecture bindings explicitly identify joints such as Mid elbows or XL knees that currently live inside one combined generated component.

Those joints are **not** treated as missing critic component edges, because the current generated component graph cannot physically represent them as separate bodies.

## Authority

This is adversarial/auxiliary evidence.

A close critic match can increase confidence that a generated shape expresses the intended articulation graph. A disagreement can surface a design or generation problem.

Neither result automatically changes the canonical Brickmen skeleton or mechanical interface.
