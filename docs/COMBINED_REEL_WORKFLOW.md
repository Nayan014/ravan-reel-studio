# Reel workflow

`/wf-reel` (or `/wf reel`, menu 5) starts with numbered recordings. `/wf-reel-plan` (or `/wf reel-plan`, menu 6) starts with an idea, an approved script and shooting plan; recordings attach later. Menu choices1–5 retain their meanings.

New reels use **Vibha → Hyperframes**. Vibha renders selected effects and approved labels without spoken subtitles. Hyperframes assembles those clips, adds the single spoken-caption layer and mixes the authoritative source voice with chosen music/SFX. Existing Remotion and manually authored Hyperframes projects retain their prior workflow and exports.

## Review flow

1. Choose an idea or existing takes using native choice/input forms.
2. Review the full script first and one scene table second. Submit feedback under the script and independently in each scene row.
3. Inspect source dimensions, rotation and exact rate locally. Matching recordings select portrait output automatically. Mixed/variable/unsupported profiles prompt an explicit choice.
4. Analyze speech locally once per uncached batch, confirm actual words, trim pauses and choose numbered Vibha effects. Original expected wording never substitutes for uncertain speech.
5. Approve the production plan/visual choices, then review actual combined stills with proposed captions. Each actual frame has a targeted feedback box.
6. Audition recommended music (preselected), alternatives, No music, suggested SFX and a voice/music sample. Selecting music creates a fresh review revision; playing alone is not approval.
7. Resolve feedback and approve current frames/audio/profile/crop. Full effects render only after this approval. Final encoding checks dimensions, exact FPS, frame count, duration, audio duration and decode integrity. The agent also reviews actual visual/audio synchronization.

Use Hyperframes Studio for direct visual edits. The review page has no custom text/colour/size canvas. Five-second refresh retains drafts and playback while the revision is unchanged. Earlier drafts remain recoverable; saved feedback is handled by the active agent or collected on resume. See [review interaction](WORKFLOW_REVIEW.md).

## Output quality

| Recordings | Portrait output |
| --- | --- |
|4K/60|2160×3840 at 60 FPS|
|4K/30|2160×3840 at 30 FPS|
|1080p/60|1080×1920 at 60 FPS|
|59.94FPS|Exact60000/1001 when supported|

Rotation metadata determines displayed dimensions. Portrait cropping can discard landscape pixels and require scaling; actual frames show the crop. Supported new-run profiles are even portrait9:16, up to2160×3840 and 60 FPS. Smaller source resolutions remain smaller. Unsupported sizes/rates require an explicit supported profile. This matches dimensions/rate, not a promise of lossless encoding, HDR or original bitrate. Preview thumbnails never become production video sources.

## Files and helpers

Projects live at `outputs/reels/SLUG/`: `plan.json`, `review.html`, copied originals in `raw/`, real supporting assets in `assets/`, versioned `previews/`, cached analysis/normalization/effects/audio in `working/`, editable `hyperframes/` and deliverables in `export/`. Unrecorded drafts are valid dashboard projects. `export/caption.txt` holds agent-authored posting copy; an actual exported frame supplies the default cover. Private recordings remain local.

Use the effects environment's Python to run `scripts/reel_workflow.py`:

```bash
skills/effects/.venv/bin/python scripts/reel_workflow.py doctor
skills/effects/.venv/bin/python scripts/reel_workflow.py init --project SLUG --folder /absolute/studio/inputs/TAKES --title TITLE
skills/effects/.venv/bin/python scripts/reel_workflow.py quality --project SLUG
skills/effects/.venv/bin/python scripts/reel_workflow.py profile --project SLUG --width 2160 --height 3840 --fps 60000/1001
```

`draft --file MANIFEST` saves `title`, `idea` and `shots: [{expected_say,shooting_note}]`. After actual script approval, `approve-script --message TEXT`, then `attach --folder INPUTS_FOLDER`. Attach refuses mismatched scene numbers or overwriting originals. `analyze`, `plan`, `preview`, `approve --preview-id ID --message TEXT`, `render` and `status` follow the shared skill. `audio --track ID` or `--track none` updates music and mix. `scripts/speech_segment.py` produces a candidate for a flagged uncertain interval without changing the plan.

One local ASR model serves each uncached batch. Speech/timings, quality metadata, trims, individual effect stills/clips and mixes are cached on disk; agent output stays compact. Music/caption changes reuse unchanged full Vibha clips. Profile changes rebuild affected video while keeping valid speech analysis. Approval fingerprints include sources, profile, engine/font/model inputs, authored Hyperframes code, reviewed frames and audio. Pending feedback blocks rendering. Changed content requires fresh approval.

## Setup and credits

Node 22.18+, ffmpeg/ffprobe, the bundled effects Python environment and `npm ci` in `tools/hyperframes/` are needed for production. Dashboard viewing still needs only Node. Use the local wrapper `node tools/hyperframes/hyperframes.mjs COMMAND ABSOLUTE_COMPOSITION_DIRECTORY`. Existing Remotion projects use the Techno Reel package and its `npm ci` setup.

The audio catalogue in `assets/audio/catalogue.json` references the existing4 music tracks and23 SFX, without copying new media. It includes stable IDs, moods, duration, source/author and CC0 notices; upstream credit files remain under `tools/techno-reel/public/`. Dashboard adaptation credits/licence remain in `dashboard/LICENSE`; renderer origins/import hashes remain in `SOURCE.json` and `tools/techno-reel/STUDIO_SOURCE.json`.

## Verification

```bash
npm run test:dashboard
skills/effects/.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
REEL_INTEGRATION=1 skills/effects/.venv/bin/python -m unittest discover -s tests -p test_reel_pipeline_integration.py
```

The opt-in integration suite uses short synthetic footage and a local browser for real4K/60/4K/30/1080p/60/fractional/rotated exports, audio/caption wiring, stale approvals and music/cache reuse. It never renders user reels. Manual review remains necessary for spoken wording, aesthetic choices and perceived lip synchronization.
