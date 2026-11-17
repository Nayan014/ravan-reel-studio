# Techno Ravan cover style

Version: **2.0**  
Status: **2D-3D pop-out avatar and topic-driven visual accepted**  
Direction: **High-impact 2D-3D hybrid**

The cover combines full-bleed topic-driven visuals with an authentic creator 2D-3D pop-out avatar, high-contrast headline typography, and zero small text clutter.

## Shared identity

| Element | Value |
| --- | --- |
| Canvas ratio | 9:16 portrait (1080x1920) or 16:9 landscape (1920x1080) |
| Topic visual | Full-bleed relevant 3D graphic, mobile UI, scene, or architecture |
| Creator avatar | 2D-3D pop-out avatar in lower-left circle with head breaking out over top rim |
| Circle ring | Warm gold `#FFB800` with subtle outer glow and drop shadow |
| Headline line 1 | Bold pure white `#FFFFFF` with drop shadow (font size 108px) |
| Headline line 2 | Bold warm gold `#FFB800` with drop shadow (font size 72px) |
| Headline font | Bundled `skills/effects/fonts/ArchivoBlack-Regular.ttf` |
| Brand header | `TECHNO` in white, `RAVAN` in red/coral `#FF5252` |
| Top gradient | Ultra-smooth wide ambient gradient (y=0 to 680), zero harsh black strap |
| Small text | None. Never use micro-badges, tiny subtitles, or unreadable code snippets |

## Core design rules

1. **Zero small text**:
   Never use small subtitles, category pills, or tiny badges. On mobile feeds and notification cards, small text is unreadable and clutters the visual hierarchy. Keep only the bold 2-tier headline.

2. **2D-3D pop-out avatar**:
   When creator footage or a portrait is provided:
   - Position a circular badge in the lower-left (cx=240, cy=1620, R=210).
   - Use automated local selfie segmentation (`selfie_segmenter.tflite`).
   - The head and hair realistically pop out over the top rim into the 3D canvas space.
   - A soft drop shadow is cast from the popping head onto the top rim.
   - The chest and shoulders stay cleanly seated inside the bottom arc of the circle.
   - Aspect ratio integrity: Always preserve the native aspect ratio with face-centered cropping. Never stretch or horizontally compress the face.

3. **Smooth ambient gradient (no black strap)**:
   Never create an abrupt dark bar or black strap across the top. Use a wide, gradual quadratic falloff gradient that seamlessly dissolves into the background atmosphere.

4. **Production script**:
   Generate covers using the bundled production tool:
   ```bash
   skills/effects/.venv/bin/python skills/cover-image/scripts/render_2d3d_cover.py \
     --visual <path-to-topic-visual> \
     --creator <path-to-creator-frame> \
     --line1 "<HEADLINE_1>" \
     --line2 "<HEADLINE_2>" \
     --output <output-path>
   ```
