---
name: map-motion
description: Animate map camera zooms, raised Thai provinces, glowing outlines and route reveals. Use for map explainers, province pop-up, lift, glow, camera keyframes and speech-synchronized geographic highlights.
---

# Map motion
Use scripts/map_video.py render --scene scenes/province_demo.json --out exports/province_demo.mp4.
Read scenes/province_demo.json for the configuration. Preview at --width 360 --height 640.
Select an actual province by name or ISO code. Calculate camera bounds from its geometry. Preserve coastlines, islands and holes.
Animate a camera push-in with eased acceleration. Dim surrounding areas, lift only the selected polygon, add a soft displaced shadow and warm glowing outline, then settle it down.
Default cue: begin camera about 0.25s before the spoken province name, peak lift on the name, hold 1–2s, return after the sentence.
The bundled renderer provides a single-province 2D lift demo, not true 3D extrusion. For multiple cues, render per-cue scenes and assemble; do not claim automatic speech alignment without measured timing.
For perspective 3D extrusion or globe flights use a separate 3D renderer/source and verify registration.
Produce separate map-only shots and annotated previews. Preserve source credit and mobile UI safe areas.
Avoid approximating Thai province shapes. Keep the base visible beneath the lifted shape.
