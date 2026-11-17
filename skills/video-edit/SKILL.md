---
name: video-edit
description: Run the guided local video editing workflow when the user says start video edit, invokes video-edit, wants to choose a recent input video, or asks for effect recommendations with sample images and approval of actual preview frames before rendering.
---

# Guided video edit

For every question and approval, follow `../../docs/WORKFLOW_REVIEW.md`: use native choice buttons and open interactive HTML reviews with script, scene and frame feedback. Read saved submissions on resume; preserve the existing actual-frame approval gates.

Use this workflow in the conversation with the user. The helper handles files and stages; you analyze the video, recommend suitable effects and show the images. It does not call a model service itself.

When the user requests natural studio lighting, read `../../docs/STUDIO_LIGHTING.md`. It is opt-in, before graphics, and can accompany selected effects through the plan's `lighting` field. Show actual frames across the whole clip, not only the graphic windows. For lighting alone, use the direct effects route and its actual-frame review rather than choosing an unrelated numbered effect. Never reuse approval after changing the lighting or its calibrated screen regions.

The preferred project shortcut is `/wf video-edit`, routed by `../wf/SKILL.md`. `/video-edit` and `Start video edit` still invoke this same workflow.

Resolve the studio root as two directories above this canonical `skills/video-edit/` folder. Read `../effects/SKILL.md` for effect options and setup. Use the studio's local effects Python environment; if it is missing, perform its setup. Commands below run from the studio root:

```text
skills/effects/.venv/bin/python scripts/video_workflow.py COMMAND
```

On Windows, use `skills/effects/.venv/Scripts/python.exe`. Use absolute paths if the current directory differs. Each helper command returns JSON. Keep its `session` identifier for subsequent commands; `status --session ID` restores progress after a new chat.

## Choose the editor for a new run

For a new run, offer **Vibha effects** or **Nafay motion graphics** through native choices, unless the user already specified an editor. Existing sessions resume their saved editor. A Nafay project has renderer nafay under outputs/videos/; read `../wf-nafay/SKILL.md` and continue it without creating a Vibha session. A supplied path/selection carries into the chosen editor so the same question is not asked twice.

Choosing Nafay uses its standalone one-recording, landscape workflow. Choosing Vibha continues below. Keep the six menu numbers unchanged. Direct /effects requests retain their effect workflow. Mixed rendering is not offered in this version.

## 1 Choose the video

Run `start`. Show only its returned videos, numbered 1 to 3, newest first. Ask which one the user wants and wait. Never choose automatically, even if only one exists. If the list is empty, ask the user to put a video in `inputs/` and stop this stage. An attachment should be placed there with the user's supplied filename before listing.

After the user chooses a displayed number, run `select NUMBER`. Selection uses the displayed snapshot so adding a newer video cannot change what a number means. If the chosen file changed, refresh the list and ask again.

## 2 Analyze and suggest effects

Run `analyze --session ID --transcribe`. It extracts metadata, six source frames and, if audio exists, a transcript using the existing word timing helper. First time transcription may download packages and a model. If the host already provides reliable speech transcription, omit `--transcribe` and use that capability instead. If speech cannot be understood, disclose that limit and ask for the key message when it affects the recommendation. Do not invent the transcript.

Inspect the source overview and individual frames. Read available speech timings. Consider the opening hook, key statements, pace, face position, available space, lighting, orientation and whether the video actually has a talking head. If it has no suitable person in frame, explain the limitation before proposing face based effects.

Choose up to three suitable catalogue cards. Explain each in one short sentence tied to this clip, with a proposed time window and any words or assets needed. Use real spoken words and values. If a card needs reel covers and none are available, say whether it can reuse source frames or needs supplied assets.

Clearly label whether the recommendations are alternatives or a combined sequence. The user may pick one effect or ask to combine several; do not leave that distinction implicit.

Save a JSON file in the session folder and run `recommend --session ID --file PATH`. Format:

```json
{
  "summary": "What the clip says and how it is framed",
  "recommendations": [
    {"id": "6", "reason": "Why this visual fits the actual clip", "suggested_timing": "2 to 4 seconds"},
    {"id": "42", "reason": "Why a gentle push fits this moment", "suggested_timing": "4 to 7 seconds"},
    {"id": "46", "reason": "Why a short label suits this takeaway", "suggested_timing": "8 to 10 seconds"}
  ]
}
```

The example timings are placeholders for the agent to replace, not assumed clip facts. Card numbers follow `../effects/references/catalogue.json`, including B1, B2 and B3 for bonus looks.

Show the recommended **dummy sample images** returned by the helper, clearly labeled with catalogue numbers and reasons. Also show all six `all_sample_sheets` so the user can choose by picture without remembering names. These are the same samples as the README and PDF; do not yet render effects on the user's video. Use the host's image display capability or inline Markdown image embeds with absolute local paths. Links alone are not a substitute for the requested image comparison when image display is supported.

Ask which image number or combination the user prefers and wait. They may choose any card, not just a recommendation. If they point to an ambiguous picture, clarify its row or number. If they explicitly ask for all recommendations, select all their catalogue IDs.

## 3 Show actual frames and the plan

For an India/state map or regional/world map including India, follow `../india-map/SKILL.md` before preparing the map asset. Include the verified graphic in the existing actual-frame review.

After the user's choice, run `choose CARD_NUMBER --session ID`, or `choose 49,5,6 --session ID` for multiple selected cards. Draft a plan containing each selected effect exactly once with its canonical `fx` and optional `look` from the catalogue's `config`. Put camera effects before overlapping graphics in the effects list. Reuse only those identifiers from the sample config; its example copy, timing, names and metrics are not the user's data.

Use the actual clip's words and timing. If exact text or necessary assets are still missing, ask before previewing. Save the plan in the session folder, then run:

```text
preview --session ID --plan PATH
```

Inspect all generated frames, including samples from every selected effect window; fix unreadable copy, face overlaps or cropping by revising the plan and rerunning `preview`. Show the user the actual frame images, every included effect with its start/end seconds and text/metrics, and the output resolution. Explicitly ask them to approve these frames and the entire plan, or describe changes. Stop and wait for their answer. Their earlier sample selection is not approval of actual frames.

If the user asks for changes, revise and preview again. Every new preview invalidates the prior approval. Do not render a full clip during this review stage.

## 4 Render only after approval

Only after the user explicitly approves the displayed actual frames and plan, run:

```text
approve --session ID --preview-id CURRENT_PREVIEW_ID --message "Exact approval message from the user"
render --session ID
```

Never manufacture an approval message or treat silence as approval. `approve` records the user's decision; it is not a command to call speculatively. Use the helper's `render` command rather than bypassing this stage with a direct `fx.py` MP4 command.

The helper blocks a render without approval and rejects changed plans, sources, assets or preview frames. If it rejects stale approval, generate new preview frames and ask again. The output stays in this session's directory under `outputs/edits/`. After rendering, follow `../cover-image/SKILL.md` for the shared-style cover unless the user requested another cover or opted out. Give the finished MP4 path and remind the user to watch the result before posting.
