# Local cover composition

Use the effects environment's Python and bundled Pillow, without running the video renderer or calling an image-generation service:

```bash
skills/effects/.venv/bin/python skills/cover-image/scripts/render_cover.py --spec outputs/edits/PROJECT/publishing/cover/composition.json --output outputs/edits/PROJECT/publishing/cover/code-preview.png
```

Resolve the studio root as usual. Windows uses `skills/effects/.venv/Scripts/python.exe`. The helper resolves its own fonts and style from the portable workspace. Inspect the preview before copying it to the project's final cover path. Preserve the previous image, brief and composition when replacing an authored cover.

The project JSON spec accepts:

- `size`: `[width, height]`, normally `[1080, 1920]` or `[1920, 1080]`.
- `style_tokens`: optional path relative to the spec to a saved copy of `assets/style.json`. Pin this copy for a delivered cover so future shared token changes do not alter its colours or spacing.
- `headline`: one to four exact lines. The helper fits each line within the text width; the final line uses the shared headline-accent token (currently charcoal).
- `brand_position`: `[x, y]` fractions of the canvas, and `brand_size` in pixels. Colour and compact spacing come from the shared `assets/style.json`; background, glow, grid and engraving are also controlled there.
- `headline_box`: `[x, y, width]` fractions of the canvas; `headline_size` is the starting font size as a fraction of the shorter canvas edge.
- `hero.box`: `[x, y, width, height]` fractions of the canvas.
- `hero.polygons`: optional arrays of `[x, y]` pairs, normalized within the hero box. The helper draws the graphic using shared fill and outline tokens. Use geometry relevant to the actual topic; the renderer does not choose or validate its meaning.
- `hero.depth`: extrusion depth in pixels; use 0 for the current flat editorial style.
- `hero.image`: optional image path relative to the spec file. It is fitted within the hero box without stretching. For a portrait, use the separately supplied/selected asset; transparent cutouts work best. The helper does not remove backgrounds or generate faces.

Make a distinct landscape composition by changing the boxes, rather than cropping a portrait cover. Retain exact output dimensions. Rendered words, colours and gap must be checked on the actual PNG.

The built-in graphic is one available treatment, not a requirement for every topic. For a different illustration, keep a small project-local drawing script alongside the composition. Do not reuse an India map or another video's content for unrelated topics. Store source URLs/licences beside any sourced vector or image; distinguish those from code-drawn elements and earlier AI assets. Run the code and inspect its output before delivery.
