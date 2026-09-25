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
