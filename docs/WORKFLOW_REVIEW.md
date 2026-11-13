# Clickable workflow reviews

Use this pattern for every workflow command and its aliases. Questions use native choice/input forms; in Codex prefer `request_user_input_async`. Free-form input forms still provide a Submit button. Do not simulate buttons in Markdown or treat preselected choices as submitted. Single edits retain their established flow. New reels use Vibha effects followed by Hyperframes finishing. Existing authored projects retain their renderer.

## Present a review

Start `npm run dashboard` from the studio. Preserve portable HTML as the source document, and open the returned interactive URL:

```bash
node scripts/review.mjs prepare --kind reels --id SLUG --stage script --document outputs/reels/SLUG/review.html
node scripts/review.mjs prepare --kind reels --id SLUG --stage plan --document outputs/reels/SLUG/review.html
node scripts/review.mjs prepare --kind reels --id SLUG --stage frames --document outputs/reels/SLUG/previews/REVISION/review.html
node scripts/review.mjs prepare --kind edits --id SESSION --stage frames
```

Standalone older HTML plans remain supported with `--kind plans --id DRAFT --document docs/your-plan.html --stage plan`. New script-first projects use saved reel drafts and `--stage script`.

The page shows the full script first, one chronological scene table, actual frames, audio choices and a single approval button. Feedback belongs to the script, a scene, or a specific actual frame and review revision. Users may submit several independent comments. Drafts stay in local browser storage per target/revision; older drafts remain recoverable. Five-second refresh preserves active inputs and audio playback while the revision is unchanged.

There are no custom canvas, colour, size or drag controls. For direct editing, **Launch Hyperframes Studio** opens authored HTML elements in the bundled editor. Composition changes invalidate review; regenerate actual frames. The Studio stays open for editing; stop it from its composition folder with the local wrapper's `preview --stop` when finished. Legacy authored text-layer data remains render-compatible; the removed review editing endpoint is unavailable.

The audio catalogue reuses four tracks and 23 SFX with stable IDs, durations, mood and source/licence credits. Recommended music appears first. Auditioning never approves; selecting changes the review revision and rebuilds the bounded voice-mix sample. Valid visual stills and Vibha caches are retained for music-only changes. No music is a valid selection. Final audio is one source-voice track plus a ducked music-only bed and chosen cues; no second source-video voice.

## Process submissions

During an active review, wait once for at most 45 seconds:

```bash
node scripts/review.mjs wait --kind reels --id SLUG --seconds 45
```

If no submission arrives, report the URL/pending state and yield. Do not automatically retry or create a detached listener. On resume use `status --kind reels --id SLUG`; read earlier pending feedback as well as current events. Feedback is processed by the active agent or on resume; the dashboard does not run AI autonomously.

- **Feedback:** use `scope`, `scene`, `frame`, `requestId` and fingerprint to identify its exact target. Apply changes, regenerate the affected HTML/frames/audio, and acknowledge every handled comment. Earlier-revision feedback can remain useful; never silently drop it.
- **Script approval:** preserve the approved script, call `approve-script` with the actual approval text, then collect/attach numbered takes. This approves no visuals or unseen frames.
- **Plan approval:** continue visual preview preparation. It does not authorize final rendering.
- **Frame/audio approval:** verify the current request is not stale and its `previewId` matches current actual frames. Call the reel/edit helper's `approve` with the submission's exact text, then the normal render command. Existing legacy Hyperframes projects keep their recorded export process.
- **Stale approval:** never carry it to changed content. Publish a fresh review and collect fresh approval.

After handling a submission:

```bash
node scripts/review.mjs ack --kind reels --id SLUG --event EVENT_ID --message "Applied the scene change and published fresh frames."
```

Approval is blocked while any submission remains pending or any feedback draft is nonempty. Pending feedback across earlier revisions also blocks final rendering. Resolve feedback, acknowledge it, and publish current review content. The final helper's content hashes remain authoritative; saved approvals/checks never claim to validate later changed files. State lives in `outputs/.workflow/reviews/`, outside production fingerprints.
