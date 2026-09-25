# Owned-Reference Accuracy and False-Positive-Resistant Image Generation

Research snapshot: 2026-09-24

## Scope

This subsystem is for images, characters, designs and people that the user owns, created, commissioned, licensed, has permission to use, or that are otherwise lawful to transform.

The objective is **maximum reference fidelity without depending on hosted-service false positives**.

Do not build provider-safeguard evasion tricks. Prefer self-hosted/open-weight inference where the user controls the workflow and can enforce their own rights/provenance checks.

## Core design decision

Hosted image products often put an external policy/moderation layer in front of generation. A prompt can be rejected even when the user's reference is original or authorized because the service cannot reliably know ownership.

A self-hosted model changes the architecture:

owned reference
-> local provenance/rights check
-> local preprocessing
-> local reference conditioning / edit model
-> local structural controls
-> optional local LoRA/personality adapter
-> generated candidate
-> business/IP review
-> minifigure translation pipeline

This is not a bypass of a provider safeguard. It is choosing a model deployment where the user controls the input-rights workflow instead of delegating it to a hosted moderation heuristic.

## Rights/provenance bundle

Every business-generation request should carry a small machine-readable provenance bundle:

- asset_id
- source_type: user_photo | user_art | commissioned | licensed | public_domain | original_character | other
- creator_or_rightsholder
- user's_right_basis
- acquisition_date
- source_file_sha256
- reference_image_ids
- consent_required
- consent_verified
- commercial_use_allowed
- trademark_or_publicity_review
- notes

This has two benefits:
1. it gives Agent OS a positive reason to route the job into the local business pipeline;
2. it creates an audit trail showing why the reference was treated as authorized.

Do not use vague prompt text like "not copyrighted" as the only evidence.

## Reference-fidelity hierarchy

For an existing reference image, prefer direct image editing over text-to-image.

Accuracy ranking for most character/product conversion tasks:

1. masked/local image editing of the actual reference;
2. multi-reference image editing;
3. reference adapter + structural conditioning;
4. subject/character LoRA + structural conditioning;
5. DreamBooth/full fine-tune for difficult recurring subjects;
6. pure text-to-image.

Text-only regeneration throws away too much information.

## Recommended editing architecture

### Qwen-Image-Edit (Apache-2.0)

The original Qwen-Image-Edit checkpoint is Apache-2.0 and designed to combine:
- semantic control through Qwen2.5-VL;
- appearance control through the VAE;
- local edits;
- object insertion/removal;
- pose and style changes while preserving unrelated regions.

Primary sources:
- https://qwenlm.github.io/blog/qwen-image-edit/
- https://huggingface.co/Qwen/Qwen-Image-Edit

Business relevance:
- permissive model license;
- self-hostable;
- particularly attractive for "keep this exact character but convert it to a minifigure design" workflows;
- high storage/VRAM footprint must be benchmarked.

Do not confuse it with Qwen-Image-2.1. As of 2026-09-20, Qwen-Image-2.1 uses a **non-commercial research license** unless a separate commercial license is obtained.

### HiDream-E1.1 (MIT model/code)

HiDream-E1.1 is a local instruction-based image editor with dynamic resolution and an explicit refinement-strength parameter controlling edit-vs-refine balance. The HiDream code/models are MIT licensed.

Primary:
https://github.com/HiDream-ai/HiDream-E1

Important license stack:
HiDream's reference implementation downloads Meta Llama 3.1 8B Instruct for text/instruction processing. Llama 3.1 has its own community license and Acceptable Use Policy. Review the whole dependency chain rather than assuming "MIT repo" means every dependency is MIT.

Useful behavior:
- low refine strength can reduce unwanted creative drift;
- instruction-based editing is better than full regeneration when source fidelity matters.

### Stable Diffusion 3.5 / SDXL ecosystem

Stable Diffusion remains one of the strongest **controllability ecosystems** because it supports:
- IP-Adapter reference images;
- ControlNet canny/depth/pose;
- LoRA;
- DreamBooth;
- inpainting;
- masked-loss training;
- mature ComfyUI and Diffusers workflows.

Stability AI's current Community License covers SD3.5 core models and permits commercial use for individuals/organizations below USD $1M annual revenue; larger commercial users require enterprise terms.

Sources:
- https://stability.ai/license
- https://stability.ai/core-models
- https://github.com/Stability-AI/sd3.5
- https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter
- https://huggingface.co/docs/diffusers/using-diffusers/controlnet

This is currently the safest general recommendation for a small commercial pipeline when maximum controllability and fine-tuning matter more than one-shot edit quality.

### HiDream-I1

HiDream-I1 generation models are MIT licensed and self-hostable. They are useful as a general generator, but for reference conversion the E1 editor is normally more relevant.

Primary:
https://github.com/HiDream-ai/HiDream-I1

### HunyuanImage-2.1

HunyuanImage-2.1 is a strong 2K text-to-image model with FP8 support around a 24GB-GPU target, but it has a custom Tencent community license and territory restrictions. The public license currently excludes the EU, UK and South Korea from the defined Territory.

This makes it a poor default choice for a globally deployable business stack unless the business's location/use fits the license and legal review approves it.

Primary:
https://github.com/Tencent-Hunyuan/HunyuanImage-2.1
https://huggingface.co/tencent/HunyuanImage-2.1

### FLUX.1/2 dev

FLUX dev models are technically attractive for reference/multi-reference workflows. FLUX.2-dev advertises single- and multi-reference editing without fine-tuning.

However, the **dev weights are non-commercial** under the current FLUX dev license unless a commercial license is separately obtained. Do not use FLUX dev as the default production model for the user's business.

Primary:
https://huggingface.co/black-forest-labs/FLUX.2-dev
https://huggingface.co/black-forest-labs/FLUX.2-dev/blob/main/LICENSE.md

## Local orchestration surface

### ComfyUI

ComfyUI is a strong local workflow host because it supports:
- SDXL
- SD3.5
- Flux
- Qwen Image
- Hunyuan Image 2.1
- HiDream
- reusable node graphs/subgraphs
- local API
- partial graph re-execution
- model offloading/quantization support

Primary:
https://github.com/Comfy-Org/ComfyUI

For Agent OS, prefer programmatically versioned workflows rather than manually edited graphs with no provenance.

## Reference-conditioning methods

### IP-Adapter

IP-Adapter adds image-prompt conditioning through decoupled cross-attention. Diffusers exposes an explicit adapter scale: higher values force closer adherence to the image reference.

Use:
- source-character appearance;
- costume/colors;
- prop or object identity;
- official minifigure-style analogue as a second reference where supported.

Primary:
https://github.com/tencent-ailab/IP-Adapter
https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter

Do not crank the reference weight blindly. Benchmark identity fidelity against editability.

### ControlNet

ControlNet should carry **structure**, not identity.

Useful controls:
- canny/lineart: exact contour and costume boundaries;
- depth: 3D silhouette/pose;
- pose: body configuration;
- normal maps: minifigure geometry;
- segmentation: exact color/part regions.

Primary:
https://huggingface.co/docs/diffusers/using-diffusers/controlnet

Best conceptual split:
- IP/reference adapter = what it looks like;
- ControlNet/template = where everything must go;
- text/structured prompt = what is allowed to change.

### InstantID / PhotoMaker / PuLID / ConsistentID

For user-owned portraits or authorized real people, specialized identity-preservation methods can outperform generic IP-Adapter.

InstantID:
single-image, tuning-free identity preservation.
https://github.com/instantX-research/InstantID

PhotoMaker V2:
supports multiple identity reference images and improved identity fidelity; integrates with ControlNet/IP-Adapter.
https://github.com/TencentARC/PhotoMaker

PuLID:
SDXL and FLUX-family identity customization, optimized for editability and identity similarity.
https://github.com/ToTheBeginning/PuLID

ConsistentID:
fine-grained facial-ID conditioning using face parsing and identity information.
https://github.com/JackAILab/ConsistentID

These tools are primarily **human-face identity methods**. They are not the main solution for masks, robots, creatures or fully fictional nonhuman characters.

### StoryMaker

StoryMaker preserves face plus clothing, hairstyle and body consistency across scenes and accepts multiple portraits. It may be useful for a business character/mascot photographed or illustrated from several angles.

Primary:
https://github.com/FireRedTeam/StoryMaker

## Character LoRA

For an original character used repeatedly in the business, train a dedicated LoRA rather than repeatedly forcing one reference image through a generic model.

LoRA advantages:
- small adapter file;
- lower compute than full fine-tuning;
- versionable per character;
- can be combined with structural controls;
- useful for recurring clothes/masks/body proportions.

Diffusers documents LoRA as lightweight and memory-efficient, and current sd-scripts supports SDXL, SD3/3.5, FLUX.1, HunyuanImage-2.1 and other current architectures.

Sources:
- https://huggingface.co/docs/diffusers/training/lora
- https://github.com/kohya-ss/sd-scripts

## DreamBooth

DreamBooth updates a model from a few example images and can provide stronger subject binding than lightweight image prompting, but is heavier and easier to overfit.

Use when:
- the character is recurring;
- LoRA/reference adapters cannot retain critical identity;
- the source set has varied views/lighting;
- the business can justify a dedicated checkpoint.

Primary:
https://huggingface.co/docs/diffusers/main/training/dreambooth

Prefer LoRA/DreamBooth-LoRA before a full DreamBooth checkpoint for maintainability.

## Dataset strategy for original characters

For each recurring character collect:
- front
- rear
- left/right
- 3/4
- neutral face
- important expressions
- mask/headgear on/off
- costume layers
- props
- clean flat/reference art
- consistent color reference

Do not train 40 near-identical front images. View diversity matters more.

Caption separately:
- stable identity attributes;
- changeable scene attributes.

Avoid captions that make temporary pose/background part of identity.

## Multiple references

When a model supports multiple reference images, assign semantic roles:

ref 1 = identity / face
ref 2 = costume front
ref 3 = costume back
ref 4 = mask/headgear
ref 5 = color/material reference
ref 6 = official-style minifigure analogue
ref 7 = target minifigure template/geometry

Do not simply concatenate ten random images.

Qwen-Image-2.1 supports up to ten references and explicit mask/circle annotations, but its current 2026 release is research-only for commercial purposes; use this capability for R&D unless separately licensed.

## Local edit loop for minifigure conversion

Recommended production loop:

1. ingest original/reference and rights metadata;
2. segment the subject;
3. create source feature sheet;
4. select exact official minifigure style profile;
5. render/select fixed minifigure geometry;
6. create canny/depth/normal/part masks;
7. run image editing/reference generation;
8. compare DINO/SigLIP visual similarity to source;
9. compare generated figure to official-style distributions;
10. inpaint incorrect regions only;
11. repeat until reference fidelity and official likeness pass thresholds;
12. convert to clean flat/vector template;
13. human business/IP review;
14. archive seed/model/workflow/references.

Do not regenerate the whole image for a wrong belt, eye, logo or mask. Local inpainting preserves more correct information.

## False-positive-resistant routing

Agent OS should route a job locally when:
- reference asset has confirmed provenance;
- hosted provider rejects or is unsuitable for an authorized transformation;
- exact visual identity is more important than a generic hosted generation;
- commercial licensing is compatible.

This is routing, not provider-policy evasion.

Record:
- provider attempted
- rejection category if known
- local model selected
- rights evidence
- output review status

Never rewrite prompts specifically to trick a hosted provider into misclassifying the same request.

## Model selection for this business

Current recommended order:

### Production default: SD3.5 / SDXL controllable local stack
Best combination of:
- commercial path for a small business;
- LoRA/DreamBooth maturity;
- IP-Adapter;
- ControlNet;
- inpainting;
- ComfyUI/Diffusers tooling.

### Editing challenger: Qwen-Image-Edit
Excellent candidate for reference-faithful local edits and Apache-2.0 licensing. Benchmark its hardware cost and minifigure transformation fidelity.

### Editing challenger: HiDream-E1.1
MIT model/code and strong instruction editing. Review the Llama 3.1 dependency/AUP in the complete deployment.

### Research benchmark: Qwen-Image-2.1
Very attractive multi-reference and RGBA/editing features, but current 2026 weights are non-commercial research-only without separate license.

### Commercial-license-required benchmark: FLUX.2-dev
Strong reference editing, but dev weights are non-commercial for production use.

### Conditional research: HunyuanImage-2.1
Strong image quality but custom territory/license terms make it unsuitable as an automatic global business default.

## Business deployment principle

Do not choose the model with the fewest safeguards.

Choose the model with:
- the clearest business-compatible license;
- local/self-hosted inference;
- strong reference preservation;
- structural conditioning;
- fine-tuning support;
- deterministic/versionable workflows;
- provenance and human review.

That gives more control **and** a cleaner business compliance story.


## ChatGPT control arm

ChatGPT image generation is the hosted control group for this research.

Every project-related ChatGPT image generation should use `chatgpt-image-control-group.md` and `data/chatgpt-control-generation-schema.json`.

The control arm receives the same:
- authorized reference package;
- semantic reference roles;
- exact target identity;
- P0/P1 feature priorities;
- transformation target;
- structural locks;
- official style profile;
- mask/headgear route;
- allowed/forbidden changes;
- evaluation rubric

used by local-model experiments.

Because ChatGPT may not expose seed or exact image-model revision, record those fields as unavailable rather than guessing. Repeat important benchmark conditions and evaluate variance/failure rate instead of selecting only the best result.

Prompt optimization is versioned. Each revision should change the smallest set of schema fields necessary to address a measured failure, so improvement can be attributed to a concrete prompt/schema hypothesis.
