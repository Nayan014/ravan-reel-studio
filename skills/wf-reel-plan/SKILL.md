---
name: wf-reel-plan
description: Develop a reel idea into an approved script and shooting plan before recording. Use for /wf-reel-plan, /wf reel-plan or workflow menu choice 6, then attach numbered takes and continue the recorded reel workflow.
---

# Plan before recording

Read `../../docs/WORKFLOW_REVIEW.md` and `../../docs/REEL_PLAN_FORMAT.md`. Use native choice/input forms for questions. Resolve the studio two directories above this skill; use its effects Python for `scripts/reel_workflow.py`.

1. Ask **My idea** / **Find three ideas**. An idea already supplied skips this question. Use channel context for tutorial suggestions. Research current AI/tech facts with available search tools and cite primary sources; do not browse for timeless script mechanics. Present exactly three ideas with a short hook and angle, and let the user select one.
2. Draft the full script and short numbered shooting takes. Keep dialogue, captions, footage/shooting notes, numbered Vibha suggestions and Hyperframes finishing in one integrated chronological table. Effects are suggestions until explicitly selected.
3. Save a JSON draft manifest with `title`, `idea`, optional `language`/`channel`, and `shots: [{expected_say, shooting_note}]`. Run `draft --project SLUG --file ABSOLUTE_MANIFEST`. This creates a saved project without recordings; it appears in the dashboard.
4. Run `node scripts/review.mjs prepare --kind reels --id SLUG --stage script --document outputs/reels/SLUG/review.html`. Open the returned URL. The full script and each scene have their own feedback field. Collect/handle feedback using the shared review instructions. Keep accepted wording; do not invent an approval.
5. After explicit current script approval, run `approve-script --project SLUG --message "Exact user approval"`. Ask the user to record numbered takes. Keep this saved draft available until recordings arrive.
6. Run `attach --project SLUG --folder ABSOLUTE_INPUTS_FOLDER`. Scene/take numbers must match. This copies originals and preserves the approved script. Continue `../wf-reel/SKILL.md` at quality inspection and speech analysis. Script approval does not approve effects or unseen actual frames.

An existing slug resumes the saved stage and pending feedback, rather than creating another draft. Wait at most once for 45 seconds when actively presenting a review; yield after no submission and collect it on resume.
