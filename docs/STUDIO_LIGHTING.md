# Studio lighting

Use the [studio-lighting skill](../skills/studio-lighting/SKILL.md) for adaptive correction of the recorded presenter and room. Set `{"lighting":{"preset":"adaptive-studio"},"effects":[]}` in an effects plan. This preset samples the confirmed face and surrounding room, gently fills the darker cheek, and rolls the gain back near highlights. The tracking pass stabilizes measurements within the shot and resets them at detected cuts. Frames without a reliable face receive no adaptive correction. Optional calibrated screen polygons protect background display pixels.

For a stronger studio look use `{"lighting":{"preset":"adaptive-studio","look":"softbox"},"effects":[]}`. It shapes a broad key from above, lowers room exposure and adds a cool pool of reflected light. Calibrated displays retain their recorded image.

For a standalone before-and-after review use `scripts/video_workflow.py lighting-preview "inputs/take.mov"` with the effects Python. The returned session contains matched stills and a short motion sample with the recording's audio. Open the edits frame review and obtain approval before export. For the direct renderer, the equivalent named command is `fx.py studio-light … --opt preset=adaptive-studio`.

## Project lighting in the plan

Choose **Studio softbox**, **Blue/red wall lights** or **Off** in the single section above the scene table. The whole-project choice replaces per-shot look overrides and keeps camera-specific geometry. For the coloured look use `{"preset":"adaptive-studio","look":"wall-accents"}`. Set normalized `accent_centers` for blue and red at the wall beside the artwork and above the display. Use `screen_regions` to protect display content. Plans can store geometry separately as `lighting_calibration` at project or shot level. The [wall lights skill](../skills/studio-wall-lights/SKILL.md) covers placement and review.

## Existing blue/red room look

`studio-light` is an optional local treatment, separate from the 51 numbered effects. It uses the existing local person segmentation and face tracking, with muted blue/red room lights, a darker background and a small neutral face lift. It retains the recorded skin texture and facial shading; it does not generate a replacement face or reconstruct physical 3D lighting.

Keep lighting off unless the user selects it. Apply it to camera footage **before** camera moves, Vibha graphics, Hyperframes captions and final assembly. Existing stylized effects can subsequently change the look, including intentional monochrome scenes. Do not apply it as a final filter to a flattened reel with captions or logos.

## Single-video plans

Add lighting beside the existing effects in a guided video's plan. The selected numbered effects retain their normal sample-selection checks. For lighting alone, use the direct effects route with an empty effects list:

```json
{
  "lighting": {"preset": "natural-studio"},
  "effects": []
}
```

From the studio root, inspect an actual still before rendering:

```sh
skills/effects/.venv/bin/python skills/effects/scripts/fx.py --plan lighting.json inputs/clip.mp4 outputs/studio-check.png --still 1.4
```

After the user approves the actual frame, render through the established workflow; a direct effect request can use the same command with an MP4 destination and no `--still`. The named shortcut also works:

```sh
skills/effects/.venv/bin/python skills/effects/scripts/fx.py studio-light inputs/clip.mp4 outputs/clip-studio.mp4
```

The direct renderer retains source audio as AAC, like the other effects. For an existing project, retain its authoritative voice/music/SFX mix and single-audio-track assembly.

## Reels and YouTube projects

Set the top-level `lighting` in `plan.json` to apply the treatment to every take. A shot's own `lighting` overrides the project setting; use `"lighting": null` on a cutaway or a shot that should retain its original look. Omission inherits the project setting. No existing project changes unless lighting is selected.

```json
{
  "lighting": {"preset": "natural-studio"},
  "shots": [
    {"id": "01", "lighting": {"preset": "natural-studio"}},
    {"id": "02", "lighting": null}
  ]
}
```

This excerpt shows lighting fields only; keep the existing complete shot records, script, trims, words, captions, selected effects, output profile and audio. Both portrait reels and landscape YouTube projects use their established output dimensions and exact frame rate. The Vibha renderer owns this treatment; Nafay remains a separate editor.

Inspect each shot's actual frames, including face/hair/hand edges, highlights, lighting consistency and effect interactions. Obtain current frame/audio approval before export. Lighting configuration, calibrated regions and renderer changes participate in approval fingerprints and invalidate relevant render caches. A frame with no confident person mask is left unchanged; review false detections and explicitly disable lighting on cutaways.

For a manually authored legacy Hyperframes project, preserve its authored composition. Use `effects_for(folder, shot)` to compile lighting before the existing shot effects, replace only the new version's photographic media, and retain its captions, overlays, timing and accepted audio. Work in a separate local version when reviewing a change to an accepted project.

## Optional screen calibration

Monitor geometry depends on the shot. By default, no monitor positions are guessed. When a display is visible, inspect its actual frame and supply `screen_regions`: a list of polygons, each containing at least three normalized `[x, y]` points between zero and one. These regions reduce coloured spill on emissive displays while retaining their recorded image. Recheck them after a crop, camera move or source change.

```json
{
  "lighting": {
    "preset": "natural-studio",
    "screen_regions": [
      [[0.60, 0.20], [0.90, 0.20], [0.90, 0.40], [0.60, 0.40]]
    ]
  },
  "effects": []
}
```

The polygon above is an example, not a reusable room calibration. Save real coordinates with the individual project/shot and approve its resulting actual frames. Do not bake a person's room, reference video or private preview into the public preset.
