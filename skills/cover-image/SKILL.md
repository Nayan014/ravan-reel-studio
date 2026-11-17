---
name: cover-image
description: Understand a video's topic and create or revise a relevant Techno Ravan cover or YouTube thumbnail in the shared, versioned visual style. Use for /cover-image, cover or thumbnail requests, and the cover step after a studio video export.
---

# Consistent video covers

Resolve the studio root two directories above this skill. Read [references/style.md](references/style.md) before creating a cover. It is the shared design source for all new videos; project-specific topics and copy do not belong there. A video reference style does not silently replace the channel's cover style.

## Understand the video

- Read the project's latest accepted script, title and export record. Inspect representative video frames and its spoken content; use the available transcript or transcribe locally when needed. Check display rotation before choosing portrait or landscape. Do not infer the topic from a filename such as demo.mov or from the creator's appearance.
- Before composing, save a content brief: the actual topic, main point, intended audience when supported, spoken/visual evidence with timestamps, confidence and the connection between the chosen headline and topic visual. The style controls the visual identity; the video's meaning controls its message and imagery.
- A very short or incomplete recording may establish only a hook. Cover that supported idea without pretending to know the full argument. If the topic is still unclear after inspection, ask one focused question before inventing a headline or topic graphic.
- Use a short, truthful headline, usually 3–6 words, expressing one idea. Keep names, logos and claims accurate. Do not invent results, metrics, endorsements or a more dramatic promise than the video supports.
- Reuse the saved cover brief when revising. A supplied cover reference overrides the shared defaults for this request; ask whether to adopt it globally only if that intent is unclear.

## Choose a supplied photo or a cover without the creator's face

Do not extract or reuse a video frame as the creator's portrait by default. Video frames may still be inspected to understand the topic.

- If the user supplies a separate photo specifically for this cover, use it without asking again. Inspect it, preserve their identity and expression, and save a project copy as the portrait reference. Do not silently substitute an earlier video frame or generated likeness.
- Otherwise ask whether they want to **provide a separate photo** or **create a cover without their face**, using the native choice form described in `../../docs/WORKFLOW_REVIEW.md`. If they already requested a cover without their face, continue without another question. Acceptance of the shared style does not authorize using their likeness.
- If they choose to provide a photo, request the attachment or local image path in the normal reply and wait for it. Native text-choice forms cannot receive image uploads. Topic analysis and headline preparation can continue while waiting; do not generate the portrait cover before the image arrives.
- If they decline to provide a photo or choose a cover without their face, create an original topic-led visual: a relevant object, illustration, scene, screenshot or strong typographic composition. Keep the shared channel identity and truthful message. Do not invent a lookalike, extract a face from the video, or make a generic empty portrait placeholder.
- Record `portrait_mode` (`provided_photo`, `no_creator_face`, or explicitly requested `video_frame`), the actual source asset when used, and the user's choice in `publishing/cover/brief.json`. Reuse a saved provided-photo or no-face choice on resume unless the user changes it. Do not let an older automatically selected video frame override this preference.
- Only if the user explicitly requests a portrait from the video, follow [references/frame-selection.md](references/frame-selection.md). That optional route shows visible numbered images and waits for their selection before using a frame.

## Compose

For a geographic map of India or a regional/world map including India, first follow `../india-map/SKILL.md`. Use its verified geometry/asset, complete territories and source acknowledgement; do not reuse an unchecked map from an earlier cover.

1. Follow the version 2.0 shared style in [references/style.md](references/style.md):
   - **Topic-Driven Visual**: Full-bleed 3D visual, app UI, scene or technical architecture across the entire canvas.
   - **2D-3D Pop-Out Avatar**: When using creator footage, position the circular badge in the lower-left corner. Let the head and hair realistically pop out over the top rim into the 3D space, while shoulders stay seated inside the bottom arc. Never horizontally stretch or compress the face.
   - **Zero Small Text**: Never use tiny subtitles, unreadable micro-badges, or small corner tags. Keep only the bold two-tier headline.
   - **Smooth Ambient Top Gradient**: Use a wide, gradual falloff gradient at the top; never create an abrupt dark bar or black strap.
   - **Headline Typography**: Render `TECHNO RAVAN` brand header, line 1 in bold white, line 2 in warm gold `#FFB800` using `ArchivoBlack-Regular.ttf` with drop shadows.
2. Build covers with the bundled production renderer:
   ```bash
   skills/effects/.venv/bin/python skills/cover-image/scripts/render_2d3d_cover.py \
     --visual <path-to-topic-visual> \
     --creator <path-to-creator-frame> \
     --line1 "<LINE_1>" \
     --line2 "<LINE_2>" \
     --output <output-path>
   ```
3. Use the project's aspect ratio by default: portrait 1080x1920 or landscape 1920x1080. Export an additional size only when requested or required by the project publishing brief.
4. For extended five-dimensional styling (type x palette x rendering x text x mood), agents can also use `../baoyu-cover-image/SKILL.md` and its bundled scripts. Preserve the code, assets, and generation prompts for reproducible revisions.

The existing effects environment includes Pillow; see `../effects/SKILL.md` for local setup if needed. Do not install the video renderer just to write a cover brief. Keep font licences with any redistributed font assets.

## Inspect and save

- Inspect the actual rendered image at full size and at a small feed-preview size. Check headline readability, face coverage, cutout edges, logo accuracy, contrast and clipping. For portrait covers, also inspect the central square and 3:4 crops as design stress tests; these do not guarantee any platform's current crop.
- Save work under the project: `publishing/cover/` for the source frame, editable composition or generation prompt, and `brief.json`. Store source video path and timestamp for extracted frames. Keep generated assets distinguishable from recorded imagery.
- Copy the exact shared style used to `publishing/cover/style.md`. In `brief.json`, record the content brief, `style_version`, `style_status`, exact headline, canvas dimensions, source assets, composition/prompt path and final image path. This snapshot lets older covers be reproduced after shared-style improvements.
- After the final video renderer has finished, save the finished cover as `export/cover.png` for planned reel/video projects. For quick edits, use the session's existing export folder, or `<session>/cover.png` when none exists. Preserve a previous authored cover and its brief in a numbered revision folder before replacing it.
- If the project has `export.json`, merge only its `cover` field, retaining the existing string/object convention and every unrelated field. A `cover.png` beside an edit export is discoverable without inventing a new session schema. Do not change video approval records or renderer fingerprints. Reapply the authored cover after a video rerender that extracts frame zero again.
- Show the actual cover inline and provide its file path. Apply requested revisions to the saved composition and brief. Describe the current style as proposed until the user accepts it; do not invent approval. Cover review never substitutes for actual video-frame/audio approval.

## Improve the shared style

When the user asks for a channel-wide change, update `references/style.md`, increment its version and preserve the design decisions they keep. An ordinary topic/headline change is project-specific. New covers use the latest shared style; existing images and their snapshots remain unchanged unless a refresh is requested. Add an accepted exemplar's project path to the style notes without copying private photos into this public skill package.

For paired social copy, follow `../../docs/SOCIAL_COPY.md`. Creating a cover does not publish a post.
