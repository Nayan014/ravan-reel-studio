# Guided video edit

Put your videos in `inputs/`, open this studio in your coding agent and send:

> /wf-video

Use `/wf` for the command menu, `/wf gallery` for sample images, or `/wf resume <session>` to continue a saved edit. The previous `/video-edit`, `/effects <name>` and `Start video edit` commands remain available. If your host does not expose slash skills, use its skill mention (for example `$wf video-edit`) or say `Use the wf skill with video-edit`.

You do not need to remember subcommands: send `/wf`, then reply **1** for video editing, **2** for the gallery, **3** for a direct effect or **4** to resume. Standalone shortcuts `/wf-video`, `/wf-gallery`, `/wf-effects` and `/wf-resume` also appear as separate discoverable skills or project commands. In supported command menus, type `/wf-` to filter them. Completion after a space depends on the host and is not configured by this project.

```mermaid
flowchart TD
    A[/wf-video or menu choice 1] --> B[See the three newest input videos]
    B --> C[You choose a video]
    C --> D[Agent analyzes the picture and speech]
    D --> E[See recommended sample images and the full gallery]
    E --> F[You choose one effect or a combination]
    F --> G[Agent creates actual preview frames and an edit plan]
    G --> H{You approve?}
    H -->|Changes needed| G
    H -->|Yes| I[Agent renders your finished MP4]
```

You do not need to know effect names. The first pictures are the existing dummy samples; the next preview uses your selected video. Nothing renders as a full video until you approve that preview and plan.

You can select one effect or say **combine all three**. Recommendations should be labeled as alternatives or a combined sequence. A combined plan shows preview frames for every included effect before you approve the full edit.

All files for an edit stay together in `outputs/edits/<session>/`. Tell the agent that session identifier to resume an unfinished edit.

The helper lists at most three immediate files in `inputs/`, newest arrivals first. On first discovery, it estimates arrival from filesystem creation/change times, then remembers that order so later edits do not move a file up the list. An older last-modified date does not make a newly copied video fall to the bottom. This is a snapshot; the video numbering stays fixed while you choose.

The helper extracts frames, audio and optional word timings. Your agent interprets them and supplies recommendations. First time transcription may need a download; if speech cannot be analyzed, the agent should say so and ask for the key message. Original media remains intact.

The command works inside an agent conversation, not as a standalone AI service. For terminal helpers, run `skills/effects/.venv/bin/python scripts/video_workflow.py --help` from the studio folder. An agent handles the conversation between those stages.
