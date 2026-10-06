# Reusable generation workflow

This is the operational entry point for minifigures and standalone parts. Existing specialist documents remain the authorities for geometry, decoration grammar, templates, colors, resin fit and UV calibration. The brief compiler checks metadata and local attachment hashes. It does not generate images, identify a part from pixels, measure geometry or approve manufacturing.

## 1. Create one brief

From the Brickmen repository:

```powershell
python tools/knowledge/compile_generation_brief.py --init minifigure --output-dir work/my-design
# Or use --init part for a helmet, accessory, brick or other independent part.
```

The scaffold is intentionally incomplete. Complete `brief.json` before compiling. The packet comes directly from `data/chatgpt-control-generation-schema.json`; the wrapper adds a brief ID, target kind, output contract, required views, required part slots, unknowns and unresolved conflicts.

| Field | What to provide |
| --- | --- |
| `target_identity` | Exact incarnation, outfit and source appearance, or the revision of an original part specification. Separate different costumes/expressions; do not silently blend references. |
| `references` | Unique reference ID, semantic role, provenance ID and explicit view. Add `local_path` and `sha256` for local attachment verification. Relative paths resolve against the brief's directory. Metadata-only references generate warnings and still need attachment/review. |
| `critical_features` | P0 identity essentials, P1 important details, P2 optional details; each cites existing reference IDs. Evidence defaults to appearance; use evidence_kind geometry or production for those claims. Geometry alone cannot support an appearance feature. State which side a feature belongs to. |
| `structural_locks` | Named geometry profile/revision, pose, camera view, and canonical parts. Each part identifies `slot`, `namespace`, `part_id`, `color_id`, `geometry_revision`. Preserve mold variants and catalog namespaces. IDs are declared choices, not automatically verified catalog crosswalks. |
| `required_part_slots` | The actual architecture. The minifigure scaffold starts with head, torso, hips/legs, two arms and two hands. Adapt it explicitly for short legs, peg legs, alternative bodies, armor, headgear or extra accessories. A standalone part starts with `primary`. |
| `required_views` | Evidence required for this job. The default is front/rear/left/right. Add top/interior/interface views for relevant parts. Narrow the list only when the deliverable explicitly has that scope. The compiler checks declarations, not visual orientation. |
| `official_style` | Relevant existing style profile, era/theme and analogue samples. Keep physical factory style distinct from game/film style; supply actual analogue references. Profiles in this corpus are research descriptions, not calibrated statistical thresholds. |
| `mask_translation` | Explicitly choose head print, existing headgear plus print, new part plus print, hybrid, or not applicable. Determine shape versus decoration before generation. |
| `transformation`, `allowed_changes`, `forbidden_changes` | Preserve by default; enumerate the intended changes and avoid contradictions. |
| `rendering` | View, projection, lighting, background and framing. The view must agree with the structural camera lock. |
| `unknowns` | Unseen seams, uncertain colors or unmeasured dimensions. Unknowns remain visible warnings and must not become invented facts. Required fields/views cannot be waived by listing them here. |
| `output_contract` | Select from the existing output-contract file. `concept_render` is for assemblies; `part_render` for independent parts. Print art, resin concepts and production packages retain their specialist requirements. |

Use a `geometry_template` reference for every target and an `identity_primary` reference for minifigures. Include exact source references and style analogues separately. Avoid many redundant front images when the rear is missing. The compiler does not dereference provenance records or assert that a reference supports a claimed feature; that remains a reviewer responsibility.

## 2. Compile and review

```powershell
python tools/knowledge/compile_generation_brief.py --input work/my-design/brief.json --output-dir work/my-design/compiled
```

`preflight.json` contains errors, warnings, declared output requirements, an unreviewed feature checklist, attachment hashes, and hashes of the brief and policy inputs. An incomplete/conflicted brief exits with code 2 and produces no prompt; a failed rerun removes the previous `prompt.txt`. Success means `ready_for_metadata_review`, not verified visual accuracy. Resolve warnings or retain their limitations explicitly before generation.

Use `prompt.txt` and the same role-labelled references with the chosen provider. Archive the preflight, actual workflow/model revision, seed if exposed, reference hashes, output hashes and reviewer decisions. Do not invent provider metadata. Local attachment paths in the prompt are locators: the user or model runner must attach the actual files; the compiler does not upload them.

## 3. Build reference coverage

```powershell
python tools/knowledge/build_minifigure_reference_sets.py --input <derived-assets.jsonl> --output <reference-sets.jsonl>
# Use --target-kind part for independent part views.
```

Each DerivedAsset requires `sample_id`, `derived_asset_id`, and `source_reference_asset_id`. Add known authority, view, component type, confidence, resolution and content hash. Zero confidence remains zero; omitted confidence contributes no claimed certainty. Invalid/nonfinite confidence fails. Scores rank available evidence; they cannot resolve incompatible releases or prove identity.

Known conflicts belong in `unresolved_conflicts`. They are preserved but excluded from preferred slots. Exact byte duplicates within a role lose redundant alternate slots while all occurrence IDs remain. Unknown/side views cannot complete a front slot. Missing views are reported explicitly. Film/game/structured-pattern evidence retains its separate role rather than being counted as a physical view.

Local LDraw reconstruction recipe:

```powershell
python tools/knowledge/index_ldraw_minifig_patterns.py --ldraw-root <library> --output-dir <indexed>
python tools/knowledge/render_ldraw_pattern_training_views.py --manifest <indexed/ldraw_minifig_patterns.jsonl> --ldraw-root <library> --ldview <LDView-executable> --library-revision <archive-sha256-or-commit> --output-dir <render-run>
python tools/knowledge/build_minifigure_reference_sets.py --input <render-run/render_manifest.jsonl> --output <part-reference-sets.jsonl> --target-kind part
```

The existing indexer keeps its default minifigure-pattern selection and asset IDs. Add `--catalog patterned_parts` for description-selected patterns across part families (`ldraw_part_patterns.jsonl`), or `--catalog all_parts` for all declared standalone parts and shortcuts (`ldraw_parts.jsonl`). Repeat `--part 3001.dat --part 3626c.dat` to index only those paths relative to `parts/` without scanning the full library. Broader modes exclude primitive/subpart/undeclared files using the [LDraw header types](https://www.ldraw.org/article/398.html). Pattern selection is a description heuristic, not a verified decoration annotation. Records preserve LDraw namespace, exact filename ID, declared type and explicit category; absent categories stay unknown. These IDs do not establish LEGO design IDs or mold crosswalks. Header metadata and source hashes come from the same captured bytes.

For one front preview per selected part, pass `--ldview <executable> --library-revision <archive-sha256-or-commit>` to the indexer. It delegates to the same renderer in `physical_like` mode and links only newly verified outputs through `render_manifest`; missing images or changed dependencies fail with a nonzero exit. Both tools accept `--lighting unlit` for decoration/color inspection without simulated lighting; the default is `lit`. The renderer's repeatable `--view front --view rear` option selects canonical views; omitting it renders all views. Header names cannot select output directories. Metadata indexing alone needs no renderer or imaging dependency.

LDView is a local prerequisite for rendering. Source hash mismatches/missing files produce failures. Derived IDs and filenames include render settings; the manifest supplies sample IDs consumed by the reference builder. The library revision is a user declaration covering dependency files; the renderer verifies the indexed top-level hash and recursively binds every resolved dependency through the existing geometry ingester. Missing or external dependencies fail; an optional dependencies_sha256 pin rejects changed children.

Renderer v8 binds external PNG TEXMAP assets, including quoted names, PLANAR/CYLINDRICAL/SPHERICAL declarations and comment-wrapped subfile dependencies. It validates images, rejects ambiguous lookup locations, and repeats inventory after rendering to catch changed bytes or newly introduced shadow files. `geometry_dependencies` contains CAD files, `appearance_dependencies` contains textures and color configuration, and `render_dependencies` contains the complete snapshot. The conservative all-branches ingestion mode is dependency discovery, not a textured OBJ exporter. Snapshot v2 and renderer revisions intentionally change derived IDs; rebuild older manifests and dependency pins. The grammar and texture search prefix follow the [ratified TEXMAP specification](https://www.ldraw.org/texmap-spec.html).

Rendered records carry structured geometry/pattern media, part namespace and ID. Reference builder v3 also recognizes older LDraw-render processor markers, so missing or contradictory media cannot promote a render into a physical appearance slot. `physical_like` is a rendering profile, not a physical-evidence claim. Rebuild older ReferenceSets to apply this corrected classification; their IDs change with the builder version. Physical front/rear/side roles remain missing until corresponding appearance evidence is supplied.

The pinned 2026-10-06 library indexed 24,858 standalone parts/shortcuts and produced 24 verified views for brick 3001, torso 973, head 3626c and patterned head 3626cp01. Visual inspection found triangular shading patches on the patterned head. High-quality lighting and disabling specular highlights did not eliminate them; unlit rendering removed the patch in the inspected view. Renderer v8 explicitly pins lighting, specular, smoothing and flat-shading flags in each configuration. This offers a neutral inspection mode; it does not correct the underlying CAD normals or establish photographic color accuracy. Experiment hashes and limitations are recorded in the autonomous frontier.

Training-rights status considers every geometry/texture dependency; an open top-level file cannot override an unknown dependency license. For assets without a source-header license, indexed records may provide `dependency_licenses`, keyed by library-relative path, with `license`, exact `sha256` and `provenance_id`. Conflicting headers or stale declarations fail. These are evidence declarations, not legal verification. Unknown or unsupported license strings remain `requires_permission`.

`geometry_revision` identifies the complete captured render-input snapshot, while `library_revision` remains a user declaration. The renderer selects this library, isolates saved preferences, disables primitive substitution, stud textures and automatic cropping, pins LDConfig.ldr, and explicitly enables texture mapping with fixed filtering. Only newly produced PNGs at the requested size enter the manifest; changed geometry/configuration bytes invalidate that source. Execution failures and a 120-second per-image timeout become reported failures. GLOSSMAP assets are inventoried but remain blocked pending verified renderer support; embedded MPD/DATA assets and nested TEXMAP blocks are also blocked. These settings follow the [official LDView help](https://github.com/tcobbs/ldview/blob/master/Help.html). LDraw evidence remains a community reconstruction.

The 2026-10-06 real smoke experiments used the verified official [LDView 4.7 portable release](https://github.com/tcobbs/ldview/releases/tag/v4.7). Synthetic PLANAR, CYLINDRICAL and SPHERICAL surfaces rendered visible red/blue texture colors, then magenta/blue after changing only the texture. Pixels, image hashes and dependency revisions changed; part source hashes remained unchanged. Compact evidence and release hashes are in `data/autonomous-state.json`. To repeat, set `BRICKMEN_LDVIEW_EXECUTABLE` to a local executable and run `python -m pytest tests/test_index_ldraw_parts.py -q`; the three real smoke tests skip when the executable is not configured. This establishes texture execution and change detection on those synthetic surfaces, not full UV-coordinate accuracy, real-part likeness or physical fit.

## 4. Split before training or evaluating

```powershell
python tools/knowledge/build_minifigure_training_splits.py --input <derived-assets.jsonl> --output <assignments.jsonl> --group-field outfit_design_id
```

For independent parts use a canonical part-design/mold identity field; for harder benchmarks use character/theme/mask family as already described in the training curriculum. Resolve missing identities first. `--allow-fallback` is an explicitly flagged exploratory mode.

The v2 splitter joins requested groups, identical `sha256`, shared `source_reference_asset_id`/`derived_asset_id`, and reviewed `duplicate_cluster_id` relationships transitively. It avoids treating perceptual similarity as proven identity. Freeze and version assignments: newly discovered links between groups can merge components and change splits. More occurrences within the same existing group do not change its split. Rebuild v1 assignments before comparing evaluation results.

## 5. Evaluate the actual output

Use `data/ai-evaluation-metrics.json` for geometry, artwork and multiview measures. Record source fidelity, official likeness and production feasibility separately. Evaluate P0 features individually; a missing essential feature fails even if an average score looks good. Use matched reference roles and repeat important runs; retain failed outputs to avoid selecting only a lucky result.

### Measure registered outputs

Use the existing metrics with reviewed binary masks rather than asking the evaluator to infer foreground or alignment:

```powershell
python tools/knowledge/evaluate_generation_output.py --request work/my-design/evaluation.json --output work/my-design/evaluation-report.json
```

A minimal request is:

```json
{
  "schema": "brickmen-generation-evaluation/v1",
  "registration_status": "reviewed",
  "alignment_id": "camera-and-crop-v1",
  "assets": {
    "reference_silhouette": {"local_path": "reference-mask.png", "sha256": "exact-file-sha256"},
    "candidate_silhouette": {"local_path": "output-mask.png", "sha256": "exact-file-sha256"}
  },
  "landmarks": {
    "reference": {"left_eye": [100, 120], "right_eye": [160, 120]},
    "candidate": {"left_eye": [101, 120], "right_eye": [160, 122]}
  },
  "thresholds": {"silhouette_iou": 0.95, "landmark_max_error": 0.01}
}
```

Threshold values above are illustrative, not measured LEGO acceptance limits. Omit thresholds to record measurements without pass/fail. Masks must be single-channel black/white (0/255), share the exact pixel grid, and identify the same camera, object view and crop. Preserve their derivation from the actual output/reference hashes and the registration review in run provenance. The evaluator verifies supplied mask bytes; it cannot establish that a hand-supplied mask depicts the intended object. Landmarks are optional, must use the exact same labels, and are normalized by the image diagonal; maximum error exposes a displaced feature that the average could hide.

For decoration, supply `art_mask` and `safe_zone`, plus `keepout_mask` when applicable, using the same asset shape. Containment counts art outside the safe zone and art overlapping any keep-out; empty art cannot pass. Silhouette inputs are optional for a print-only measurement. No automatic resizing, segmentation or missing-landmark inference occurs.

The report binds request, metric registry and input hashes, and distinguishes technical checks from unreviewed semantic features and unvalidated manufacturing/fit. Review P0 details, part IDs, colors, left/right orientation, hidden surfaces and official likeness separately, even when silhouette overlap is perfect. A blocked rerun replaces a stale successful report.

Evaluator processor v2 also accepts optional `provenance` with `source_images` (each role has `local_path` and `sha256`) and a byte-pinned `registration` JSON file. Include `candidate`, plus `reference` for silhouette comparison and `production_template` for print containment. The registration uses schema `brickmen-registration-evidence/v1`, the same `alignment_id`, a named `reviewer`, nonempty `review_notes`, and `mask_derivation.method`. Its `source_images` must pin each original `image_sha256` and `original_dimensions_px`; `mask_sha256`, `pixel_grid` and `landmarks` must match the exact measurement request. The evaluator checks the image bytes, dimensions, registration bytes and these bindings. It reports `verified_byte_bindings_as_declared`; requests without this provenance remain `masks_only`. Neither status verifies segmentation, correspondence or a reviewer's judgment. Any explicit resolution normalization belongs in the reviewed derivation record; the evaluator itself still never resizes inputs.

The first actual reconstruction experiment (2026-10-06, LDraw 3626cp01 neutral front) measured 0.995929 silhouette IoU after declared whole-canvas resolution normalization, yet failed the flat-color constraint: the generator added shading and returned 1254×1254 instead of the requested 512×512. A targeted exact-palette revision still failed flat color and reduced silhouette IoU to 0.991908. Both original outputs, masks, registration, exact prompts and individual feature reviews were retained; the compact [experiment record](data/generation-accuracy-head-experiment-v1.json) binds them. Use the existing unlit CAD renderer when exact geometry and flat color must be preserved. This one-view experiment demonstrates why geometry metrics and constraint review remain separate; it does not validate physical likeness, hidden surfaces, production or general model accuracy.

Correct the smallest faulty region. Keep part geometry, colors and accepted features locked. Record the changed fields and measured failure in the existing control protocol's revision/result records. A prompt compiler is not an image scorer: silhouette IoU, landmarks, surface containment and feature presence still require actual measurements or review.

For print art, provide a `production_template` reference, production process, positive physical dimensions_mm (width and height), resolved template boundaries and output.template_revision before compilation. The production reference must declare scale_status calibrated, calibration_provenance_id and the matching template_revision. These declarations remain subject to evidence and physical proof; the declared target type must match the output contract. Move to calibrated surface templates and vector masters; apply safe areas, keep-outs and measured minimum features. For new parts, replace concept connectors with engineered connectors and test clearance/fit. For production, require the existing output contract, dated calibration, prototype evidence, frozen revisions and human approval. The preflight exposes these requirements but does not certify their completion.

## Relationship to the existing runtime

This brief compiler does not itself perform CAD generation, model inference, UV reprojection or physical calibration. The repository already contains [LDraw hierarchy ingestion](ldraw-geometry-ingestion.md), [body skeleton generation](body-skeleton-system.md), [provider execution](body-generation-provider-runner.md), [geometry validation bundles](body-generation-validation-bundle.md) and [resumable generator continuation](body-generation-generator-continuation.md). Reuse those tools; do not create a second geometry stack based on this preflight interface.

Catalog/source-appearance claims still require evidence and review, and digital validity does not establish physical fit. The fieldless manufacturing descriptors consolidated in `data/capability-backlog.json` remain `specification_pending`; other current repository specifications and completed benchmarks are governed by their existing validators. Canonical continuation priorities are in [AUTONOMOUS_STATE.md](../../../AUTONOMOUS_STATE.md).

## Review cohort and promotion evidence

The ongoing Fortnite review plan uses `data/semantic-review-batches/fortnite-first-review-queue-v1.jsonl.gz`, an exact compressed snapshot of the queue from commit `75915c3`. Its decompressed SHA-256 remains `743293e2e74eda8f9db78dd13340fb4f525965d84d24b50fb82dfdb4f75e502b`. The live ingestion queue can change priorities without changing the reviewed cohort or batch identities. Start a separately versioned plan to review a new live cohort; do not silently regenerate existing batches from new rankings.

Blind second-review preparation preserves prior source/LEGO byte hashes and evidence scope without copying semantic annotations. Materialization refuses changed bytes. Comparisons and training promotion require matching exact evidence and scope across the reviewers and adjudicator; missing hashes or conflicting snapshots cannot become canonical supervision. The promotion tool rechecks this rule even when a supplied queue row claims eligibility.

The compact submission builder checks each decision hash against every supplied item/template pin. For locally acquired bundles, set `review_bundle_source` to `local_exact_byte_materialization` and compile against the hash-populated materialized batch. Both image pins are required; local provenance does not invent GitHub workflow or artifact IDs. Historical unpinned batches remain reproducible, with `legacy_unbound_hashes` reported in the summary. Retain exact image bytes separately for later blind review: a URL and hash can detect changed media but cannot recover the original bytes.

Progress v2 normalizes reviewer IDs with the same helper used for adjudication, promotion and blind-review preparation. It counts independently double-reviewed pairs only when distinct declared reviewers share exact image hashes and observed scope, and separately exposes pairs blocked by missing or conflicting evidence. Different IDs alone cannot establish a genuinely independent review process; verify that separately.

When live media changes, keep the original pins. Materializer v3 enforces both item and template hashes/URLs and can reuse the existing exact-media archive: supply `--archive-manifest <media-manifest.json> --archive-root <extracted-archive-root>`. Every requested pair/role must match its archived URL, declared hash and confined local path. Archived bytes are hashed again; absent, corrupted, conflicting or escaping entries fail without a network fallback. The source archive may belong to an earlier review pass, so it can serve a genuinely independent blind batch with the same pair/byte identities. Failed CLI reruns remove stale output batch/manifest files, while overlapping input/output paths are rejected before cleanup. Build the existing review UI from the recovered materialized batch; archive reuse supplies evidence only and never copies semantic labels or creates training eligibility.
