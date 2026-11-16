---
name: wf-nafay
description: Edit one talking-head video with Nafay 3D's seven motion-graphics styles. Use for /wf-nafay or /wf nafay, or when Nafay is selected in /wf-video. Review cuts, graphics plan, actual frames and audio before a source-quality landscape export.
---

# Nafay standalone video editor

Read `../../docs/WORKFLOW_REVIEW.md`, `../../docs/NAFAY_VIDEO_EDITOR.md`, the bundled `tools/nafay-video-editor/SKILL.md` and its story guide. Resolve the studio root two directories above this canonical skill. The bundled skill describes the original editor; this studio wrapper controls paths, dependencies, review, output quality and final export. Its optional upstream check-ins are replaced by the studio approvals below. Run all editing commands with the effects environment's Python and `scripts/nafay_workflow.py`.

## Select and prepare

- An existing Nafay slug resumes `status --project SLUG` and saved submissions. Read `plan.json` and the work files to continue the saved phase. Never run init over an existing project. Existing Vibha sessions retain their original workflow.
- A supplied video path skips the picker. Otherwise run `scripts/video_workflow.py start` and show its recent candidates with native choices. Use the selected path directly for Nafay init; do not call the Vibha select command. If a supplied folder has several recordings, ask which one to edit. Nafay supports one continuous source per project in this version.
- Ask only for missing choices, using native forms in manageable groups: remove silence (default yes, natural 0.3-second pauses), remove mistakes (yes, with cut review), style (Warm Canvas), language (English, Hindi or auto), captions (off, with Devanagari/Roman preference if Hindi), graphics intensity (light, medium or none). Preserve details already supplied. Show all seven creator-labelled catalogue choices from `assets/styles/nafay.json`; list styles with their use rather than reading every base.js file.
- If base Node/ffmpeg tools are missing, run the studio npm start setup first. On first Nafay selection, run `python3 scripts/nafay_setup.py` with a compatible Python or the existing effects Python. On Windows use the installed compatible Python. This installs the optional Playwright browser into local caches using the shared environment. Never run the upstream setup.py, a system pip upgrade, or its break-system-packages fallback. Model weights download on first use; English small.en reuses the existing CPU cache. Hindi/auto defaults to large-v3-turbo, a larger download and slower CPU run; explain that before starting it. No dedicated GPU is required.
- Run `init --project SLUG --source ABSOLUTE_VIDEO --title TITLE`. Put options in a JSON file under the project working folder and run `configure --project SLUG --file OPTIONS`. Options are documented in the editor guide. Native matching quality is selected automatically. For mixed/variable/unsupported source rates use an explicit user choice and `profile --project SLUG --width W --height H --fps RATE`. Fractional rates stay exact. Portrait or non-16:9 footage requires explicit centre-crop agreement, recorded as `crop_approved: true`. Show the crop in actual frames.

## Transcribe and approve cuts

1. Run `transcribe --project SLUG`. Read the original transcript and its confidence markers. Confirm uncertain speech from the source; never substitute expected script text. Preserve informal speech and word indices when proposing mistake cuts.
2. Follow the bundled skill's mistake-finding rules. Author `working/nafay/edits.json` with inclusive word-index removals and reasons. Clear removals when mistake cutting is off. Keep word timing and transcript corrections accurate.
3. Run `cut-plan --project SLUG`. Open `node scripts/review.mjs prepare --kind videos --id SLUG --stage plan --document outputs/videos/SLUG/review.html`. The full transcript and proposed removed words/times are visible. Handle feedback, acknowledge completed changes through the review helper, and republish the current cut review when revised.
4. After explicit approval, run `approve-cuts --project SLUG --message "Exact approval"`, then `cut --project SLUG`. This produces cut.mp4, cut.wav and edited-time transcripts in working/nafay/. Time all graphics to the EDITED transcript. Original recordings remain intact.

## Plan the graphics

1. Read `tools/nafay-video-editor/references/story-guide.md`, the selected style's style.md and the relevant helpers/demo code in its base.js. For Warm Canvas also read its example story. Treat demo dialogue and numbers as examples. Use the creator's actual topic, words and supplied assets.
2. Propose only useful visual beats: light is about one per 30–60 seconds; medium about one per 15–30 seconds. Leave the speaker on screen between beats. Use deterministic animation and reuse the selected style's helpers.
3. Author `working/nafay/story.js` with `EDIT.D` equal to the exact kept frame count divided by the approved FPS and `EDIT.SPANS` matching the beat ranges. Use the original 1280×720 logical design space; the renderer scales to the approved output. Preserve FOOTAGE, gfxInOut and engine render hooks. Do not bake another spoken-caption layer into story.js. Keep synthesized effects sparse and tied to visual events, with no synthetic replacement voice.
4. Save a beats manifest `{"beats":[{"start":12.1,"end":18.6,"description":"Nafay · selected-style explanation using actual content"}]}`. Use non-overlapping edited-time beats. For no graphics use an empty beats list and a story with an empty SPANS list and no score. Run `plan --project SLUG --file BEATS_MANIFEST`.
5. Prepare and open the current plan review again. It contains the full edited script and integrated chronological scene table. Resolve script/scene feedback and get explicit graphics-plan approval. Run `approve-plan --project SLUG --message "Exact approval"`.

## Actual frames, audio and final export

1. Run `preview --project SLUG`. The helper checks story duration/spans and captures representative actual frames from every beat plus plain footage. Captions follow the chosen style and language. The preview includes a source-voice/effects mix excerpt.
2. Inspect all actual frames for clipping, face coverage, readability, crop and correct text. Listen to the audio sample where the host supports playback. Open a `frames` review using the existing review helper with kind videos and this project. Individual frames and scenes support feedback. Revisions to code, captions or cuts require refreshed relevant reviews and previews.
3. Resolve pending feedback before approval. Only after explicit approval of the current frames/audio run `approve --project SLUG --preview-id CURRENT_ID --message "Exact approval"`, then `render --project SLUG`. Do not render directly with the vendor script or fabricate approval. The wrapper checks source, edit decisions, story, selected style/fonts, quality and actual preview fingerprints.
4. Report the MP4 under outputs/videos/SLUG/export/. For requested posting copy, follow `docs/SOCIAL_COPY.md`: Instagram, YouTube title/description, TikTok and LinkedIn by default, with natural writing and no em dashes. Update the existing posting-copy file or create `publishing/Social_Copy.md`. The dashboard discovers the export, cover, plans and frames. Ask the user to watch before posting.

Nafay owns captions and audio in this standalone route. Hyperframes finishing and mixed Vibha/Nafay rendering are deferred. A style suggestion or playing a preview does not approve a full render. Setup, media processing and end-to-end verification were deferred at installation time. Report the actual validation status of each later run accurately.
