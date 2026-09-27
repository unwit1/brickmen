# Minifigure Customs Knowledge Ontology

The Knowledge Engine should normalize incoming information into linked collector, reference, manufacturing and commercial entities.

## Identity and reference entities

- Character
- Incarnation
- SourceWork
- SourceAppearance
- OutfitDesign
- Theme
- Franchise
- Continuity
- ReferenceAsset

Canonical identity chain:
Character -> Incarnation/Continuity -> SourceAppearance -> OutfitDesign -> FigureRelease

## Collector and market entities

- Maker
- MakerAlias
- FigureRelease
- ComponentRelease
- ProductCodeAlias
- Collaboration
- Edition
- ReleaseEvent
- Vendor
- VendorListing
- PriceObservation
- CompatibilityObservation
- QualityObservation
- CollectionState
- WishlistEntry
- DesignCandidate

FigureRelease -> ComponentRelease -> MarketObservation

## Part and manufacturing entities

- PartDesign
- Element
- MoldVariant
- DecoratedPart
- MinifigureAssembly
- Color
- Material
- Finish
- Artwork
- PrintSurface
- Template
- CharacterDesign
- Pose
- CameraPreset
- RenderAsset
- UVPrintProfile
- Jig
- JigCavity
- Printer
- InkSet
- RIPProfile
- Primer
- Varnish
- Resin
- ResinPrintProfile
- Connector
- FitCoupon
- Supplier
- Batch
- Experiment
- Defect
- QCResult
- Product
- Source
- RightsRecord

## Important relationships

Character HAS_INCARNATION Incarnation
Incarnation APPEARS_AS SourceAppearance
SourceAppearance DEPICTS OutfitDesign
FigureRelease REPRESENTS Character
FigureRelease REFERENCES SourceAppearance
FigureRelease IMPLEMENTS OutfitDesign
Maker PRODUCES FigureRelease
FigureRelease CONTAINS ComponentRelease
FigureRelease HAS_CODE ProductCodeAlias
FigureRelease SOLD_AS VendorListing
VendorListing OBSERVED_AS PriceObservation
FigureRelease REVIEWED_BY QualityObservation
ComponentRelease TESTED_BY CompatibilityObservation
CollectionState TRACKS FigureRelease or ComponentRelease
DesignCandidate DERIVED_FROM collection gap, SourceAppearance or missing commercial variant
ReferenceAsset SUPPORTS SourceAppearance or FigureRelease claim

PartDesign HAS_VARIANT MoldVariant
Element REALIZES PartDesign
DecoratedPart DECORATES PartDesign
PartDesign MADE_OF Material
PartDesign AVAILABLE_IN Color
MinifigureAssembly CONTAINS PartDesign
Artwork TARGETS PrintSurface
Template MAPS PrintSurface
Jig HOLDS PartDesign
UVPrintProfile USES Jig
UVPrintProfile USES InkSet
UVPrintProfile TARGETS Material
Connector MATES_WITH PartDesign
ResinPrintProfile VALIDATES Connector
Batch USES Artwork
Batch USES UVPrintProfile
QCResult EVALUATES Batch
RenderAsset DERIVED_FROM PartDesign
RenderAsset CONDITIONS GenerationRequest
Source SUPPORTS every factual assertion

## Provenance classes

official_lego
purist_custom
altered_official
hybrid_custom
third_party_original
replica_ko
alternate_figure_system
unknown

Preserve the source's own label such as custom, bootleg, compatible, clone or KO separately from this normalized field.

## Confidence

authoritative
manufacturer
catalog-high
community-corroborated
empirical-user-validated
inferred
unverified

## Version applicability

Every technical, market, compatibility or status fact that can change must support valid_from, valid_to, source_date/observed_at and last_verified.

Prices are observations, not attributes. Quality and compatibility are release/batch/source observations, not timeless maker attributes.

## AI retrieval policy

A design-generation model should receive only the relevant slice:
1. target character/source appearance,
2. target part geometry,
3. target colors/materials,
4. style grammar,
5. target manufacturing profile,
6. applicable constraints,
7. validated reference assets,
8. prior validated experiments.

A collector/research model should receive only the relevant character/release/component/source crosswalk plus current or requested historical market observations.

Do not dump the entire library into the prompt.


## Figure architecture extension

Non-standard bodies require first-class architecture entities rather than additional labels on `PartDesign`.

Add:
- FigureArchitecture — normalized component/joint/connector system independent of character and maker label.
- FigureArchitectureObservation — evidence that a release/component belongs or may belong to an architecture.
- BodyStyleProfile — architecture- and optionally maker-specific visual/sculptural grammar.
- ArchitectureSurfaceSchema — semantic decoration/UV/keep-out surfaces for one body architecture.
- StyleTransferPair — paired evidence for translating the same character/appearance between architectures.
- ArchitectureDigitalTwin — validated neutral body/component geometry, landmarks, articulation sweeps and render presets.

Relationships:

```
FigureRelease USES_ARCHITECTURE FigureArchitecture
ComponentRelease BELONGS_TO_ARCHITECTURE FigureArchitecture
FigureArchitecture HAS_COMPONENT PartDesign
FigureArchitecture HAS_JOINT Connector
FigureArchitecture HAS_STYLE_PROFILE BodyStyleProfile
FigureArchitecture HAS_SURFACE_SCHEMA ArchitectureSurfaceSchema
FigureArchitecture HAS_DIGITAL_TWIN ArchitectureDigitalTwin
FigureArchitectureObservation SUPPORTS architecture assignment
StyleTransferPair MAPS BodyStyleProfile/architecture to another architecture
```

Character identity does not imply architecture. A Hulk release can be a standard minifigure, short-leg minifigure, LEGO Giant, Alpha Toys 7 cm body, or another custom system.

Preserve the source's own label (`BigFig`, `midfig`, `mega fig`, `7CM`, `Giant`) independently from the normalized FigureArchitecture. Mechanical architecture is promoted only from component/joint evidence and, for manufacturing-critical claims, physical validation.

### CharacterBodyDesignSpec

Add:
- CharacterBodyDesignSpec — architecture-conditioned design handoff for a specific character/appearance.
- FigureArchitectureSelection — auditable candidate/selection record.
- BodyStyleProfileRegistryEntry — reusable descriptive style grammar attached to one or more architectures.

Relationships:

```
SourceAppearance PROPOSES_ARCHITECTURE FigureArchitectureSelection
FigureArchitectureSelection SELECTS FigureArchitecture
CharacterBodyDesignSpec TARGETS FigureArchitecture
CharacterBodyDesignSpec USES_STYLE BodyStyleProfile
CharacterBodyDesignSpec DESIGNS_COMPONENT PartDesign/GeneratedComponent
CharacterBodyDesignSpec USES_CONNECTOR Connector
CharacterBodyDesignSpec USES_SURFACE ArchitectureSurfaceSchema
```

The Knowledge Engine must resolve any legacy `BodyArchitecture` ID through the compatibility bridge before generation or manufacturing.


## Mold/tooling lineage extension

Custom/compatible bodies can cross brand boundaries through reused, remade, shared, or derived tooling. Maker identity is therefore not sufficient to identify exact body geometry.

Add:
- MoldFamily — a physically/tooling-related family of component geometry inside one FigureArchitecture.
- MoldRevision — a geometry/tooling revision within a MoldFamily.
- MoldEquivalenceObservation — evidence that two releases/components share, derive from, or do not share the same mold/tooling family.

Relationships:

```
FigureArchitecture HAS_MOLD_FAMILY MoldFamily
MoldFamily HAS_REVISION MoldRevision
ComponentRelease USES_MOLD_REVISION MoldRevision
MoldEquivalenceObservation COMPARES FigureRelease/ComponentRelease
```

Use cases:
- detect cross-brand reissues/remakes;
- transfer physical measurements only after mold equivalence is validated;
- avoid buying redundant physical samples;
- create hard-positive pairs for body recognition where paint/brand differ but geometry is the same;
- create hard negatives where the architecture is the same but tooling geometry differs.

A source statement such as "same mold" creates a candidate relationship, not manufacturing authority. Promote to validated equivalence only after corroborated catalog/component evidence or physical comparison.


## Body semantics, style compilation, and learned proposals

Add:
- CharacterBodyFeatureSpec — architecture-neutral semantic body intent for one Character/SourceAppearance.
- SurfaceMaterialProfile — reusable geometry/relief/print/finish grammar for materials such as rock, fur, metal and scales.
- StyleMappingRule — evidence-backed rule mapping a semantic feature into an architecture/style-specific representation.
- BodyStyleCompilation — auditable compilation from semantic features + architecture + style into CharacterBodyDesignSpec.
- JointProposal — non-authoritative joint/component hypothesis produced by learned articulation models.
- JointCartridge — deterministic replaceable mechanical interface/hardware module inside a FigureArchitecture.

Relationships:

```
SourceAppearance DESCRIBED_BY CharacterBodyFeatureSpec
CharacterBodyFeatureSpec COMPILED_WITH FigureArchitecture
FigureArchitecture USES_STYLE BodyStyleProfile
BodyStyleProfile APPLIES_RULE StyleMappingRule
SurfaceMaterialProfile GUIDES CharacterBodyDesignSpec
BodyStyleCompilation PRODUCES CharacterBodyDesignSpec
JointProposal PROPOSES_MATCH Connector / FigureArchitecture joint
FigureArchitecture USES_JOINT_CARTRIDGE JointCartridge
```

Three semantic levels must remain separate:
1. visual region — chest, bicep, rock plate, armor panel;
2. manufacturing component — torso, arm, hand, lower body;
3. mechanical interface — shoulder socket, wrist cartridge, neck connector.

Learned 3D segmentation/articulation may inform levels 1–2 and propose level-3 hypotheses, but manufacturing level-3 geometry remains deterministic and validated.


## Body skeleton extension

Add:
- BodySkeleton — normalized, parametric generation/alignment graph for one FigureArchitecture.
- SkeletonTopologyModule — reusable graph transform/addition for multi-arm, digitigrade, ball-joint, mechanical, integrated-head and overlay cases.
- EngineeringSkeleton — future physically reconciled skeleton with measured joint centers/axes.
- JointCartridge — remains the authority for actual fit-critical mechanical geometry.

Relationships:

```
FigureArchitecture HAS_BODY_SKELETON BodySkeleton
BodySkeleton MAY_APPLY SkeletonTopologyModule
BodySkeleton PROMOTES_TO EngineeringSkeleton
EngineeringSkeleton USES_JOINT JointCartridge
CharacterBodyDesignSpec FITS_TO BodySkeleton
```

Important distinction:
- landmark != joint;
- joint topology != connector geometry;
- normalized generation coordinate != manufacturing dimension.

The current Brickmen Broad/Mid/XL/Giant skeletons are generation skeletons only. They may guide shell generation and articulation planning but cannot authorize a printed pin/socket until a validated JointCartridge is assigned.
