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
| `critical_features` | P0 identity essentials, P1 important details, P2 optional details; each cites existing reference IDs. State which side a feature belongs to. |
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

The existing indexer covers patterned minifigure components. The renderer accepts indexed standalone part records with source path/hash/reference identity; arbitrary-part catalog acquisition still needs a broader indexer. LDView is a local prerequisite. Source hash mismatches/missing files produce failures. Derived IDs and filenames include render settings; the manifest supplies sample IDs consumed by the reference builder. The library revision is a user declaration covering dependency files; the renderer verifies the indexed top-level part hash, not every dependency. LDraw evidence remains a community reconstruction. Real LDView rendering and physical fit require separate validation.

## 4. Split before training or evaluating

```powershell
python tools/knowledge/build_minifigure_training_splits.py --input <derived-assets.jsonl> --output <assignments.jsonl> --group-field outfit_design_id
```

For independent parts use a canonical part-design/mold identity field; for harder benchmarks use character/theme/mask family as already described in the training curriculum. Resolve missing identities first. `--allow-fallback` is an explicitly flagged exploratory mode.

The v2 splitter joins requested groups, identical `sha256`, shared `source_reference_asset_id`/`derived_asset_id`, and reviewed `duplicate_cluster_id` relationships transitively. It avoids treating perceptual similarity as proven identity. Freeze and version assignments: newly discovered links between groups can merge components and change splits. More occurrences within the same existing group do not change its split. Rebuild v1 assignments before comparing evaluation results.

## 5. Evaluate the actual output

Use `data/ai-evaluation-metrics.json` for geometry, artwork and multiview measures. Record source fidelity, official likeness and production feasibility separately. Evaluate P0 features individually; a missing essential feature fails even if an average score looks good. Use matched reference roles and repeat important runs; retain failed outputs to avoid selecting only a lucky result.

Correct the smallest faulty region. Keep part geometry, colors and accepted features locked. Record the changed fields and measured failure in the existing control protocol's revision/result records. A prompt compiler is not an image scorer: silhouette IoU, landmarks, surface containment and feature presence still require actual measurements or review.

For print art, provide a `production_template` reference, production process, dimensions/aspect and template boundaries before compilation; the declared target type must match the output contract. Move to calibrated surface templates and vector masters; apply safe areas, keep-outs and measured minimum features. For new parts, replace concept connectors with engineered connectors and test clearance/fit. For production, require the existing output contract, dated calibration, prototype evidence, frozen revisions and human approval. The preflight exposes these requirements but does not certify their completion.

## Known capability limits

No automatic full-assembly CAD scene generation, UV reprojection, empirical color calibration, model training/inference, output contract certification or physical proof is implemented by this workflow. Catalog/source-appearance resolution and most crosswalks require review. Manufacturing metadata placeholders are tracked in `data/capability-backlog.json` as `specification_pending`, not usable schemas. Follow `development-state.md` to implement the next gap without introducing a parallel schema or ingestion stack.
