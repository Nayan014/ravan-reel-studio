# Unified planning entry

Read `docs/WORKFLOW_REVIEW.md` and `docs/REEL_PLAN_FORMAT.md` from the studio root. Use native choice/input forms and the local effects Python for `scripts/reel_workflow.py`. KIND and project_type come from the calling skill. New projects use Vibha effects followed by Hyperframes finishing.

## Choose a starting point

Offer four clickable choices: **I have an idea**, **Suggest ideas**, **I have footage**, **Resume a project**. A supplied topic, folder or saved project skips the corresponding question. Respect an explicitly supplied starting point. Ask only for missing information.

- **Idea:** ask for topic and intended length. Keep the creator's language/channel preferences. For YouTube, build an opening hook, ordered sections and a conclusion, with manageable recording takes and clear shooting cues. Reels use a concise hook and short takes.
- **Suggestions:** offer exactly three ideas, each with a hook and angle, based on channel context. Research current factual claims using primary sources. Let the creator select an idea and intended length.
- **Footage:** ask for a folder name or path. A bare name resolves inside `inputs/`; `inputs/name` is studio-relative. Run `init --kind KIND --project SLUG --folder FOLDER --title TITLE`, then follow the production reference. A single continuous recording may have any filename; multiple takes use unique numbered filenames. Base the production plan on actual transcribed speech. This route skips idea selection and writing a pre-recording script. After speech analysis and scene mapping, use the optional reference-style step in the production reference.
- **Resume:** show saved projects only from `outputs/KIND/`. Run `status --kind KIND --project SLUG`, read pending feedback, and continue its recorded phase. Drafts await script review or attached takes; recorded projects continue through production. Do not restart or overwrite a saved project.

## Idea to recorded production

1. Create HTML with the full spoken script first, followed by the integrated scene table. Include scene timing estimates, recording cues, source, proposed captions, numbered effect suggestions and Hyperframes finishing. For YouTube include section headings in the script and section labels in shooting notes. Effects remain suggestions until selected.
2. Save a JSON manifest containing `title`, `idea`, `language`, `channel`, `target_duration` in seconds, optional `sections`, and `shots: [{expected_say, shooting_note}]`. Run `draft --kind KIND --project SLUG --file ABSOLUTE_MANIFEST`. Project type is set by KIND. Keep accepted wording and save drafts before footage exists.
3. Run `node scripts/review.mjs prepare --kind KIND --id SLUG --stage script --document outputs/KIND/SLUG/review.html`. Open the returned URL. Handle full-script and per-scene feedback in that review. Record explicit approval using `approve-script --kind KIND --project SLUG --message "Exact user approval"`.
4. Ask the creator to record the takes and provide their folder. Run `attach --kind KIND --project SLUG --folder FOLDER`. Numbered takes map to approved scene numbers. Never overwrite originals or replace the approved script.
5. If a continuous recording covers several approved scenes, obtain the scene boundaries from real audio/transcription and create a mapping JSON `{"scenes":[{"id":"01","source":"recording.mp4","clip":[0,12.4]},{"id":"02","source":"recording.mp4","clip":[12.4,30]}]}`. Use `attach ... --mapping ABSOLUTE_MAPPING` to attach one source to several scenes. Do not guess time ranges from expected dialogue.
6. Once footage is attached, use the optional reference-style step before choosing treatments. Continue `skills/wf-reel-plan/references/production.md` at quality inspection within the same planning command. Script approval does not approve unseen frames, effects or final audio.

## Continuous recordings and scene revisions

After importing footage, `analyze --kind KIND --project SLUG` caches the source transcription. For long footage, read only the relevant word timings and identify actual section/scene boundaries. Create a JSON file with `scenes: [{id, source, clip: [start,end], shooting_note}]`, using filenames already copied into `raw/`. Run `scenes --kind KIND --project SLUG --file ABSOLUTE_MAPPING`, then analyze again. The cached source transcript is reused and restricted to each scene's time range. A scene can share its source with other scenes. Splitting resets affected visual decisions and sound cues so revised timings receive a fresh review.

All helper commands require `--kind KIND` when working on YouTube. Choose `profile --kind KIND --project SLUG --width W --height H --fps RATE` when matching sources cannot select a profile. For mismatched orientations, discuss crop versus fit, set `framing` to `crop` or `fit` on each shot, and review the actual result. Portrait reels default to crop; YouTube defaults to a centred crop unless the creator selects fit. Fit preserves the whole picture with padding. Confirm the proposed framing before actual-frame approval.

Keep feedback linked to script, scene or actual frame and to its review revision. Use Hyperframes Studio for direct visual edits. Keep cached speech, effect clips and valid previews where their inputs are unchanged. Process saved feedback on resume. Wait at most once for 45 seconds when presenting a review, then yield and collect submissions on resume.

## Skip answered questions and reuse reference decisions

A supplied folder enters the footage path directly. Existing footage skips idea generation, script drafting and recording instructions. Supplied topic, language, duration, chosen reference or saved project details skip those corresponding questions. Ask only for genuinely missing information in the current stage. If footage has not been attached, wait until it exists before offering reference styles.

Use `skills/wf-reel-plan/references/reference-style.md` after footage analysis and scene mapping, before production-plan approval. This applies to both reel and YouTube projects. Reuse `reference_selection: selected` or `none` on resume. A request to change the reference reopens that choice. If no reference videos exist, continue without asking a reference question. Keep an existing selected snapshot when the library file is later renamed, removed or changed, unless the user requests a different style.

## Nafay styles during YouTube planning

Read `assets/styles/nafay.json` alongside the Vibha catalogue and any pinned reference notes when suggesting landscape motion graphics. Label the creator and canonical nafay: style ID. These styles render through the standalone Nafay editor in this version. Do not write a Nafay-only suggestion into a Hyperframes project as if it were already integrated.

For ready footage, offer “Open a separate Nafay edit” when the creator wants one of those styles. Ask which recording if there are several. Read `skills/wf-nafay/SKILL.md`, pass the selected source path and create a distinct project slug. Preserve the existing planning project, script and approvals; do not migrate its renderer. Explain that this standalone path uses Nafay cutting, captions and audio. Saved Nafay projects selected on resume route to wf-nafay rather than the reel/Hyperframes helper.
