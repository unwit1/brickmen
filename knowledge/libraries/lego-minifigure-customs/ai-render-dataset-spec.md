# AI Render Dataset Specification

## Objective
Create a geometry-grounded dataset that teaches models what minifigure-scale objects actually look like and provides deterministic controls for generation.

## Record unit
One record = one exact assembly + pose + camera + material configuration.

Required metadata:
- assembly_id and revision
- exact constituent part IDs across local/LDraw/BrickLink/Rebrickable/LEGO identifiers when known
- geometry source, license, source revision and hash
- color crosswalk IDs
- material family and finish
- pose transforms per rigid part
- camera transform, projection, focal length or orthographic scale
- light transforms/intensities
- renderer/version
- color-management configuration
- random seed where relevant
- render dimensions
- all derived-pass filenames

## Canonical outputs
Produce:
- beauty RGB
- clay
- albedo/base color
- depth
- world normal
- camera normal
- silhouette/alpha
- edge/canny derivative
- object/part segmentation
- material segmentation
- position pass where supported
- UV reference
- unlit artwork pass
- shadow-only reference
- dimensions/axes diagnostic

Blender supports depth, normal, object index and material index passes; these should be exported losslessly for control data.

## Cameras
Every base asset should have reproducible orthographic front, back, left, right, top and bottom views plus standardized 3/4 catalog views. Perspective renders are useful for concepts; orthographic renders are authoritative for silhouette comparison and artwork transfer.

## PBR material records
Represent digital plastic with explicit base color, roughness, specular/IOR behavior, transmission/alpha where relevant, normal detail and finish. glTF's metallic-roughness model is a useful portable baseline: minifigure plastics are dielectrics rather than metals, while metallic-looking molded/printed finishes need separate appearance treatment.

## Training/conditioning partitions
Keep distinct:
1. geometry truth set — deterministic unmodified geometry;
2. appearance set — colors/materials/lighting;
3. decoration set — validated printed graphics;
4. concept set — AI-created candidates;
5. production-approved set — physically manufactured and photographed results.

Never allow unverified AI outputs to become geometry truth.

## Reference-image strategy
For character adaptation, combine an image-reference adapter with geometry controls. IP-Adapter provides image guidance; ControlNet provides structural guidance such as depth and edges. Keep identity/costume reference separate from geometric constraints.

## Multi-view consistency
Prefer one textured 3D source rendered into all views. If AI must generate views, condition every view on the corresponding deterministic depth/normal/silhouette and the same character reference bundle. Record model, checkpoint, adapters, weights, prompt, seed and postprocessing.

## Evaluation
Automated checks should include:
- silhouette IoU against geometry mask,
- landmark displacement,
- segmentation consistency,
- color difference against target swatches,
- left/right symmetry where expected,
- forbidden geometry detector,
- print-zone containment,
- multi-view feature correspondence.

Human review remains required before manufacturing.

## Sources
https://docs.blender.org/manual/en/latest/render/layers/passes.html
https://www.khronos.org/gltf/pbr
https://huggingface.co/docs/diffusers/using-diffusers/controlnet
https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter
