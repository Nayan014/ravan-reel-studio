# Local reference styles

Place reference videos directly in `references/`. Keep your own takes in `inputs/`. Reels are saved under `outputs/reels/`; YouTube projects use `outputs/videos/`.

Both planning commands support references. A topic starts script planning; a supplied footage folder skips idea/script preparation. Once actual recordings are ready and the agent understands their scenes, it offers the reference filenames plus No reference. An empty library skips this question. A project retains its selected style or No reference choice on resume.

## How the agent reads a reference

The internal `scripts/reference_styles.py` helper lists files and prepares a selected video using local ffprobe, ffmpeg and Pillow. It extracts up to six pairs of frames, builds a contact sheet and estimates scene changes at low resolution over at most the first 120 seconds. Sample moments span the video. Audio is not analysed automatically.

The active coding agent inspects those samples once and writes evidence-based style notes. These cover pacing, typography, colours, framing, transitions, graphics and audio uncertainty. Observed details are distinguished from tentative motion inferences. A targeted additional interval may be inspected when needed. Initial image reasoning can consume normal agent credits. Media preparation uses local tools without an additional model service.

## Cache and project snapshots

`.cache/reference-styles/v1/CONTENT_HASH/` stores sample frames, cut candidates, a contact sheet, the structured profile and human-readable notes. Identical file contents reuse that profile even under a new filename. Changed contents or a new sampling version create a separate cache entry.

The selected profile is pinned into the project's `assets/reference-styles/` with its filename and hashes recorded in `plan.json`. A `reference_note` on each affected scene explains how the style maps to actual effects and finishing. The project keeps its pinned notes when the library video is changed or removed. Request a different reference explicitly to update the project and refresh its review.

Style notes inform the normal catalogue/Hyperframes production choices. They do not install effects, guarantee an exact clone or import the reference's footage, voice or music. Use the existing effect-selection and actual-frame/audio approvals.

## Internal helper commands

Run with the local effects Python. These are agent tools, not additional public slash commands.

```text
scripts/reference_styles.py list
scripts/reference_styles.py prepare --file "Reference.mp4"
scripts/reference_styles.py save --file "Reference.mp4" --profile /absolute/style-draft.json
scripts/reference_styles.py use --kind reels --project my-reel --file "Reference.mp4"
scripts/reference_styles.py use --kind videos --project my-video --none
```

The full profile format and production instructions are in `skills/wf-reel-plan/references/reference-style.md`. The creator can leave normal script, scene or frame feedback when a proposed treatment needs revision.

## Publication and deferred testing

Git ignores all root `references/` contents except `.gitkeep`, as well as caches and generated projects. Public packaging creates only the empty reference folder. The dashboard serves pinned project notes through its existing project file boundary, and does not expose the original reference library.

Implementation checks, media sampling, cache reuse, style selection, approval invalidation and end-to-end renders are deferred at the creator's request. No reference videos were analysed during this implementation.
