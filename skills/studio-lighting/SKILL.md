---
name: studio-lighting
description: Improve lighting on a presenter’s face and recorded room in an existing talking-head video. Use for face lighting, a backlit presenter, uneven cheek shadows or adaptive studio lighting. Includes actual before-and-after motion review.
---

# Studio lighting

Use the local Vibha renderer. For a request such as “improve the lighting on my face”, choose `adaptive-studio`. Reserve `natural-studio` for the existing darker blue/red room look. The adaptive preset measures exposure and cheek shading from confident presenter detections, retains the photographed room and colours, and applies before graphics.

When the creator asks for a visibly stronger studio look, set `"look":"softbox"` inside `lighting`. It adds a broad directional face key and a darker room with cool bounce. Preserve the take’s screen calibration and review a fresh revision.

For a lighting-only edit, run this from the workspace root with the effects environment:

```sh
skills/effects/.venv/bin/python scripts/video_workflow.py lighting-preview "inputs/take.mov"
node scripts/review.mjs prepare --kind edits --id SESSION --stage frames
```

Use the returned session ID. Inspect the matched stills and play the motion sample. Open the interactive URL from the running dashboard for the creator. The left panel is the original, the right panel is the treated image, and the sample carries source audio when present. For a visible monitor, inspect its corners in the actual shot and pass a project-local lighting plan with `--plan`. To revise within the same session use the regular `preview --session … --plan … --width …` command and preserve the reviewed output width.

For existing portrait, YouTube or guided Vibha edits, set the project or shot lighting field and use that project's normal preview, audio review and approval. A cutaway can set `lighting` to null. Keep Nafay projects in their own editor. Review hair and moving hands, bright glasses, monitor edges, exposure changes and cutaways. Obtain approval for the exact frames and audio before the full render. See [lighting configuration](../../docs/STUDIO_LIGHTING.md) and [interactive reviews](../../docs/WORKFLOW_REVIEW.md).
