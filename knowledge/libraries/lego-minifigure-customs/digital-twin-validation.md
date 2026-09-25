# Digital Twin Validation

## Trust hierarchy
1. measured physical sample for manufacturing-critical dimensions;
2. authoritative manufacturer/process specification for machine constraints;
3. validated digital geometry;
4. catalog metadata;
5. community measurement;
6. AI inference.

## Geometry validation
For each high-use base part:
- obtain canonical digital geometry;
- measure several physical samples where possible;
- align scan/photo/measurement landmarks;
- compare bounding dimensions;
- compare connector geometry;
- compare intended UV print surface;
- record mould variant and sample provenance.

## Template validation
A template is production-approved only after:
- 100% scale verification,
- physical ruler/caliper check,
- sacrificial-part print,
- edge/safe-zone inspection,
- repeated jig placement test,
- white/CMYK registration test where relevant.

## Connector validation
A connector is approved only for named resin/process profiles and mating-part variants. Approval does not transfer automatically to a new resin or printer.

## AI validation
AI-generated geometry must never silently replace canonical geometry. Candidate meshes are compared against digital-twin constraints and any functional interfaces are replaced by validated parametric features.

## Versioning
Any physical discovery that changes a dimension creates a new twin/template/connector revision and records supersession rather than editing history invisibly.
