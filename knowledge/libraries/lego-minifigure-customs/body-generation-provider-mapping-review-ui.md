# Provider Mapping Review UI

Brickmen can render a standalone metadata-only reviewer for anonymous provider-part mapping proposals:

- `tools/geometry/build_body_provider_mapping_review_ui.py`

It embeds ranked mapping candidates, target/transformed AABBs, shared-transform metadata, assignment costs and ambiguity metadata. It does not embed generated mesh bytes or source/catalog images.

Each candidate is projected into:
- front X/Z view;
- side Y/Z view.

Blue boxes are Brickmen targets and orange dashed boxes are transformed provider parts.

The reviewer exports a small selection record. The selection is not the final mapping; the explicit promotion tool reruns structural output validation before creating that artifact.
