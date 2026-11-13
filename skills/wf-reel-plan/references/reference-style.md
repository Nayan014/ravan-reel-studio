# Optional reference style

Resolve paths from the studio root. Use the effects environment's Python to run `scripts/reference_styles.py`. This is an internal helper shared by `/wf-reel-plan` and `/wf-video-plan`.

## Offer a reference only when footage is ready

1. Read the project's `reference_selection` and `reference_style`. Reuse a saved selected style or explicit No reference decision on resume unless the creator asks to change it. Read the pinned profile under the project's assets, without reopening its original reference video.
2. After recordings are imported/attached and source speech/scenes are understood, run `list`. If no videos exist under `references/`, skip the question and continue normal planning. Do not inspect the reference library while waiting for idea-first recordings.
3. Show the discovered filenames as native choices with **No reference — use the usual style**. Use pages if the list is large. Ask, “Would you like to use one of these videos as a style reference?” A reference already named by the creator skips this choice. Never analyze every library video automatically.
4. For No reference, run `use --kind KIND --project SLUG --none`. Otherwise prepare only the selected file using `prepare --file "NAME.mp4"`.

## Analyze once and retain the evidence

A `cached_style` result already contains the summary and patterns. Reuse it, then select it for the project. Do not reopen the video or contact sheet, retranscribe reference speech or rewrite equivalent notes. Cache identity uses video content hash and sampling version, so renaming the same footage reuses the notes and changed footage receives a new cache entry.

A `samples_ready` result returns a local contact-sheet path and a samples JSON path. Inspect that sheet using the host's image-viewing capability. Read the sample timestamps, media dimensions, coverage and coarse cut candidates. The helper performs local ffmpeg/ffprobe sampling, with up to six paired moments across the video and a low-resolution cut scan covering at most the first 120 seconds. It does not call a model or transcribe reference speech.

Write a compact JSON profile with this shape:

```json
{
  "summary": "A concise description supported by the observed frames.",
  "patterns": {
    "pacing": "Observed cut rhythm, with the scan window and uncertainty stated.",
    "typography": "Caption placement, size, weight and animation evidence, or unknown.",
    "colour": "Observed palette, contrast and grading.",
    "framing": "Crop, subject position and supported evidence of camera changes.",
    "transitions": "Observed changes; label motion inferred from paired stills as tentative.",
    "graphics": "Observed overlays, hierarchy and likely production approach.",
    "audio": "Not analysed from these stills. Suggest local audio separately."
  },
  "evidence": [
    {"time": 3.2, "observation": "A factual description of a visible sample at this timestamp."}
  ]
}
```

Replace example content with actual observations. Evidence timestamps must come from the sampled footage. Use 1–12 concise observations, and describe unknown details explicitly. A sparse sample cannot establish every animation, precise edit timing or sound cue. If a specific uncertain transition matters, inspect only the relevant local interval with targeted ffmpeg frames or a short clip when the host can view it, then update the saved profile. Do not replay the whole reference by default.

Run `save --file "NAME.mp4" --profile /absolute/profile-draft.json`. Keep this agent-authored draft in the project working folder or ignored cache. The helper stores the validated profile and readable notes under `.cache/reference-styles/v1/SHA256/`. Initial interpretation uses the active agent's image reasoning and may consume its normal credits; later use reads compact saved notes. No new AI service is installed.

## Bring the style into the production plan

Run `use --kind KIND --project SLUG --file "NAME.mp4"`. This pins the profile and notes into project assets and records the selected filename, content hash and summary. It copies no reference footage, speech or music into the production. A reference is style guidance, not an automatically available effect engine.

Read that pinned style and map the relevant patterns to the creator's footage. Use catalogue-verified Vibha IDs for available effects, Hyperframes for authored graphics, captions, transitions and audio, and ordinary cuts/crop changes where appropriate. Mark an unsupported or uncertain effect and propose an alternative rather than claiming an exact recreation. Preserve the creator's actual dialogue, source voice, branding and approved output quality.

For each affected shot, save a plain-language `reference_note` explaining which pattern is used, the supported treatment and any limitation. Set actual Vibha/Hyperframes configuration through the normal production helper. The HTML and interactive review show the selected reference summary and per-scene treatment. The reference choice is included in approval fingerprints; changing it requires a refreshed plan/frame review. Style selection does not approve suggested effects or unseen frames.

Keep reference material and its notes local. The cache and entire root `references/` contents are Git-ignored, with only an empty `.gitkeep` folder marker in the public package. Source videos are not served by the dashboard. The pinned style notes appear among the project's supporting files and remain usable if the original reference is removed.
