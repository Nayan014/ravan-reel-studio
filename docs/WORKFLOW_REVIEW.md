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

## 3-step interactive review lifecycle

The interactive review interface (`/review/<kind>/<slug>`) structures review into three clean sequential stages:

1. **Step 1: Initial plan** (`--stage plan` or `--stage script`):
   - Shows full script first, one chronological scene table, and dummy reference cards for proposed visual effects.
   - Sticky header action bar always visible at the top: shows current step, status, "Submit feedback" and "Approve initial plan" buttons.
   - Per-scene **Approve** button (e.g. `Approve Scene 01`) and per-scene **Submit feedback** button. When feedback is submitted for a scene, it immediately displays down below that scene.
   - No audio clutter, sound effect auditions, or raw draft history dumps.

2. **Step 2: Final plan & preview frames** (`--stage frames`):
   - Triggered when the initial plan is approved. The agent renders actual preview frames with chosen effects applied.
   - Scene-by-scene focused cards: each scene presents its dialogue, applied visual effect, **1 key actual preview frame** showing the effect in action (no flood of redundant frames), and the history of feedback addressed for that scene from earlier revisions.
   - Per-scene **Approve** button and per-scene **Submit feedback** button.
   - Sticky header action bar always visible at the top with "Submit feedback" and "Approve final plan".

3. **Step 3: Final release**:
   - Triggered when final plan frames are approved. Renders the full video export, generates the cover, and prepares posting copy.

## Process submissions and reactive wait

During an active review, wait for user submissions:

```bash
node scripts/review.mjs wait --kind reels --id SLUG
```

In agent environments supporting background commands (like Antigravity), launch the wait command in the background so the agent reactively wakes up as soon as the creator clicks "Submit feedback" or "Approve plan" in the browser, without requiring the creator to type a chat message. On resume or submission, use `status --kind KIND --project SLUG` to read events.

- **Feedback:** use `scope`, `scene`, `frame`, `requestId` to identify its exact target. Apply changes, regenerate the affected HTML/frames, and acknowledge every handled comment.
- **Initial plan approval:** automatically advances to Step 2 (generates preview frames with effects applied and presents the final plan review).
- **Final plan approval:** verifies `previewId` matches current actual frames, calls `approve`, and renders the final video export.
- **Stale approval:** never carry it to changed content. Publish a fresh review and collect fresh approval.

After handling a submission:

```bash
node scripts/review.mjs ack --kind reels --id SLUG --event EVENT_ID --message "Applied the scene change and published fresh frames."
```

Approval is blocked while any submission remains pending or any feedback draft is nonempty. Pending feedback across earlier revisions also blocks final rendering. Resolve feedback, acknowledge it, and publish current review content. The final helper's content hashes remain authoritative; saved approvals/checks never claim to validate later changed files. State lives in `outputs/.workflow/reviews/`, outside production fingerprints.
