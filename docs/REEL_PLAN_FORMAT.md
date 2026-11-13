# Reel plan review format

These are the studio's reusable planning defaults; adapt the channel and style to the creator. Apply them to new reel plans and revisions unless a later request changes them. Update this file when the user changes a reusable preference; keep reel-specific decisions in that reel's plan.

## Deliverable

- Create a portable local HTML file for review. Do not create or regenerate a PDF unless the user asks for it.
- Use a clear header with the channel name **Techno Ravan** and the reel's concept or title.
- Put the complete spoken script first, in comfortable reading text for rehearsal. Preserve the latest accepted wording. English is the current default; do not change language without a request.
- Divide the full script into short, numbered recording takes with visible separators, usually one short sentence or natural phrase per take. Prefer recording and practicing small sections rather than delivering a paragraph in one clip. Preserve the wording; split at natural sentence or breath boundaries.
- Map every take to its production-table scene(s). Put a brief practice cue beside the full script: practice one take, record it, then pause; allow a short quiet hold before/after speaking for editing. Retake only that section if needed. Recording pauses are trimmed and are not included in final video timings.
- Plan how each take joins the next: cover cuts with planned graphics or use an intentional change of crop for consecutive on-camera takes. Keep camera position, lighting and posture consistent. Never promise invisible edits before seeing the footage. If a spoken sentence continues across takes, note the continuation and hide that join under graphics where possible.
- Follow with one chronological production table. Do not put captions or recording cues into a separate repeated section.
- Keep the plan simple and readable on desktop and mobile. Prefer one self-contained HTML file with no external assets needed for reading.

## Interactive review preference

Use native choice buttons for questions and approvals. Open HTML plans through the interactive studio review page, with feedback beneath the full script, in every scene row and beneath every actual frame. Use Hyperframes Studio for direct text/style editing; no custom review canvas. Apply feedback to the actual production plan; changes require fresh reviewed content before approval. See `WORKFLOW_REVIEW.md` for the local submission flow. Keep the standalone HTML readable without the server.

## Production table

Each scene or meaningful visual beat needs these columns:

1. **Scene and timing**: scene number and start/end seconds. Use estimated times until a recording provides actual word timings. If a row changes from the person to a graphic, state the transition time explicitly.
2. **What I say**: exact spoken words for that scene, matching the full script.
3. **Picture and source**: explain what is visible and where it comes from: the user's recording, a real screenshot, a Remotion animation made with code, or an explicitly proposed generated asset. Keep the real recorded voice under graphics. Do not call code animation AI-generated footage.
4. **CC on screen**: exact spoken words broken into short caption pages. Show page breaks clearly. Separate extra graphic labels/headlines from captions by putting them in the relevant graphic/effect column.
5. **Vibha effect**: write **None**, or the verified visual-guide number and canonical effect name, plus a short suggestion for timing, text and placement. Verify IDs in `skills/effects/references/catalogue.json`.
6. **Hyperframes finish** for new reels; **Remotion graphic** for existing Remotion projects: write **None**, or the Techno Reel scene name and a plain description of its text, animation and screen placement. Clearly mark any new custom scene as proposed, not already available. Remotion scenes have no Vibha catalogue number.

## Visual preferences and decisions

- Prefer clear developer typography: upright bold or monospace headings, controlled glow and readable edges. Avoid decorative italic name/AI lettering, blurred red titles and caption pills. Use bold outlined captions when requested; omit a scene's captions when its headline already carries the same idea. Tool-logo sequences should use original icons without added white cards or repeated names. Keep these as style preferences, not automatic effect approval.
- New reels use Vibha effects followed by Hyperframes. Keep captions separate from Vibha treatments and use Hyperframes for captions and final assembly, including the chosen transitions, camera moves and sound. Do not silently substitute Remotion captions. Record any explicitly delegated self-review/final-output authorization for that reel separately; it does not change the default preview approval policy.
- Aim for approximately 70% real person on screen and 30% graphics when appropriate. Show the proposed split; timings remain estimates until the take is edited.
- Recommend a coordinated sequence with varied placement and motion. Avoid repeating behind-the-head text for every idea. A simple cut or an effect-free moment is valid.
- Always include catalogue numbers beside Vibha effect names. Clearly distinguish alternatives from effects intended to run together.
- All suggested effects and graphics remain pending the creator's final selection. Script acceptance does not approve effects, graphics or a final render.
- State real tool readiness accurately. The combined workflow bundles Techno Reel locally under `tools/techno-reel`, invoked through `skills/wf-reel-plan/references/production.md`. The original sibling project remains separate. Re-check the helper doctor and renderer test status before claiming readiness.
- Follow the existing workflow for actual preview frames and explicit approval before rendering the full video.

## Project-specific choices

Keep a creator's approved script, channel, assets and effect decisions in that project's plan. Personal examples and rejected choices from another project are not defaults for new reels. The channel label in this guide is an example; use the creator's own channel when supplied.

## Source quality and audio

Inspect recordings locally, including rotation and exact frame rate. Matching sources choose portrait output automatically; 4K/60 remains 2160×3840 at 60 FPS, and fractional rates stay exact. Mixed/variable/unsupported profiles require an explicit choice. Show output dimensions, FPS and crop/scaling before approval. Review thumbnails never become production footage.

The final approval page includes recommended music preselected, playable alternatives, No music, the voice/music mix sample, and suggested playable sound cues. Use the existing 4 music/23 SFX catalogue with licence notices. Selection changes the review revision; playing does not approve. Final approval covers current frames, crop, output profile and audio together.

## Planning entry points and YouTube videos

Use `/wf-reel-plan` for portrait reels and `/wf-video-plan` for landscape YouTube videos. Both accept ideas, three suggested ideas, existing footage and saved projects. Ask for topic and intended length when starting from an idea; ask for a folder when footage already exists. Bare folder names resolve under inputs/. Continue in the selected command through final production.

YouTube scripts include a hook, sections and a conclusion, with shooting cues and the full script before the integrated scene table. Keep approved script text when mapping continuous footage into several source ranges. The video profile is 16:9, up to 3840×2160 at 60 FPS; preserve fractional rates, confirm mixed profiles and show crop or fit. Adapt selected effects/captions for landscape actual-frame review. New videos use the same feedback, music and approval rules as reels.

## Optional reference style

Once recordings are ready, the two planning commands may offer videos from root `references/`, with a No reference choice. An empty library skips the question. Reuse the saved project choice on resume. Show the selected reference filename/summary and describe each proposed reference-inspired treatment in the scene table using `reference_note`. Observations are cached with evidence and uncertainty, then pinned to the project; use those notes instead of repeatedly watching the reference. The normal effect-selection and actual-frame/audio approval stages apply. See `REFERENCE_STYLES.md`.
