---
name: studio-wall-lights
description: Add blue and red practical-style wall lights behind artwork and monitors in talking-head footage. Use for coloured background lighting with a neutral face and protected screens, or the project-wide Blue/red wall lights option in a Vibha production plan.
---

# Blue/red wall lights

Use the Vibha lighting stage before camera moves, text and graphics. Select the **Blue/red wall lights** example above the scene table to apply it across the project. For a lighting-only edit use the [studio lighting preview workflow](../studio-lighting/SKILL.md) with `"preset":"adaptive-studio", "look":"wall-accents"`.

Inspect the photographed room. Put the blue pool on the wall below or beside a frame and the softer red pool on the wall just above or behind the monitor. Save the two normalized [x,y] positions under `lighting.accent_centers.blue` and `lighting.accent_centers.red`. Outline visible screens with `screen_regions`. For different camera angles store geometry in the shot's `lighting_calibration`. The renderer supplies a neutral softbox key on the presenter and protects calibrated screen content. Defaults give left and right wall pools when a room has no calibration.

Use the actual frames and audio review for approval. Inspect wall falloff, skin, monitor content and moving silhouettes. See [configuration](../../docs/STUDIO_LIGHTING.md).
