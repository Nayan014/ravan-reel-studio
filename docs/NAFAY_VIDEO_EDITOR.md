# Nafay 3D standalone video editor

Use `/wf-nafay` directly, or choose **Nafay motion graphics** in a new `/wf-video` run. It edits one continuous talking-head recording into a landscape YouTube video. Existing Vibha sessions continue with their saved editor.

## The editing flow

Choose recording → Confirm cutting, style and language → Review proposed cuts → Approve cuts → Review graphics plan → Approve plan → Review actual frames and voice/effects sample → Approve export.

The full spoken script appears first, followed by a chronological scene table. Script, scene and individual-frame feedback use the normal studio review pages. The imported original is preserved in `outputs/videos/SLUG/raw/`; Nafay work files stay under `working/nafay/`; the final video and cover are in `export/`. Posting copy is authored separately in export/caption.txt. Projects appear in the dashboard Videos category with renderer nafay.

## Seven creator-labelled styles

| Catalogue ID | Style | Typical use |
| --- | --- | --- |
| `nafay:warm-canvas` | Warm Canvas | Editorial cards and picture-in-picture for talking heads |
| `nafay:creator-motion-graphics` | Creator Motion Graphics | Kinetic type and energetic emphasis |
| `nafay:clean-tech` | Clean Tech | Crisp UI cards and technology explanations |
| `nafay:software-walkthrough` | Software Walkthrough | Software screens, cursors and clicks |
| `nafay:data-story` | Data Story | Charts, counters and numerical comparisons |
| `nafay:chalk-talk` | Chalk Talk | Hand-drawn concept explanations |
| `nafay:pop-info` | Pop Info | Illustrated infographic scenes |

The machine-readable planning catalogue is `assets/styles/nafay.json`. Each entry includes its creator, orientation, guide, engine path and available helpers. These are complete graphics styles, distinct from Vibha's numbered effects. Read only the chosen style's guide and relevant helpers to keep planning context small. The original demos illustrate style mechanics; use the creator's real dialogue and topic in authored graphics. No rendered style samples were generated during installation.

YouTube planning can suggest these styles alongside Vibha and cached reference-style notes. Choose “Open a separate Nafay edit” for ready footage to start a distinct standalone project. Preserve the saved planning project and its approvals. Combining Vibha and Nafay in one finished project is deferred.

## First-use setup

Run `npm start` to prepare the base studio tools. Nafay’s additional renderer is installed when selected.

The agent runs `python3 scripts/nafay_setup.py` with a compatible Python, or the existing effects Python. On Windows use the installed compatible Python. It creates/reuses skills/effects/.venv, installs the shared pinned faster-whisper backend plus Playwright, and downloads Chromium into tools/nafay-video-editor/.cache/browsers. Packages, browser and speech models are cached locally. No system-wide pip upgrade is used.

The default English path uses small.en on CPU, sharing the studio model cache. Hindi and automatic/mixed detection use large-v3-turbo by default, a larger first download and slower CPU run. The agent explains this before starting and may use an explicitly chosen model. Dedicated NVIDIA hardware is optional. Speech corrections must follow actual audio; uncertainty is not replaced by an expected script.

## Source quality

The studio wrapper selects landscape dimensions and exact FPS from the recording. A 4K/60 recording produces 3840×2160 at 60 FPS, and fractional rates such as 60000/1001 are retained through cutting, graphics and encoding. Variable-rate or unsupported sources need an explicit supported profile. Portrait/non-16:9 recordings require approval of the centre crop. Preview thumbnails do not become production sources.

The upstream 1080p default and FPS snapping are bypassed when the studio output profile is active. Selected captions are visible in actual preview frames. A voice/effects sample is prepared before approval. Nafay handles its own caption layer and final voice/effects mix in this standalone route, with one source-voice track and -14 LUFS finishing. Hyperframes remains the finishing editor for the other planning workflow.

## Agent helper commands

Use the effects environment's Python with `scripts/nafay_workflow.py` and these subcommands:

| Operation | Arguments |
| --- | --- |
| Catalogue | `styles` |
| Import | `init --project SLUG --source VIDEO --title TITLE` |
| Settings | `configure --project SLUG --file OPTIONS_JSON` |
| Explicit quality | `profile --project SLUG --width 3840 --height 2160 --fps 60000/1001` |
| Speech | `transcribe --project SLUG` |
| Cut proposal | `cut-plan --project SLUG` |
| Cut approval | `approve-cuts --project SLUG --message "Exact approval"` |
| Apply approved cuts | `cut --project SLUG` |
| Graphics proposal | `plan --project SLUG --file BEATS_JSON` |
| Graphics approval | `approve-plan --project SLUG --message "Exact approval"` |
| Actual preview | `preview --project SLUG` |
| Frame/audio approval | `approve --project SLUG --preview-id ID --message "Exact approval"` |
| Export | `render --project SLUG` |
| Resume | `status --project SLUG` |

Options JSON may contain `style`, `language` (en/hi/auto), `captions`, `silence`, `mistakes`, `pause`, `min_gap`, `graphics` (light/medium/none), `sfx_gain`, optional `model`, and `crop_approved` when needed. Style accepts a catalogue ID or its upstream ID. Defaults are Warm Canvas, English, captions off, natural 0.3-second pauses, mistake-cut review and light graphics.

The agent authors edits.json using inclusive original word-index ranges. Cut approval happens before cut.mp4 is generated. Graphics use edited-time words and the original 1280×720 logical canvas. Author working/nafay/story.js and a beats manifest such as `{"beats":[{"start":12.1,"end":18.6,"description":"A style-labelled explanation"}]}`. EDIT.D must equal the kept frame count divided by FPS; EDIT.SPANS must match the reviewed beat ranges. New cut timings require a revised story and review. Pure graphics/caption changes reuse the source transcript and unchanged cut media.

Source, edit decisions, story, selected style/fonts, quality, preview images and audio are fingerprinted. Source or input changes require refreshed approvals. Pending feedback blocks approval/export. The final wrapper verifies encoded dimensions, FPS, frame count, duration, source audio and decode integrity when it is run.

## Credits and installation status

Created by [Nafay 3D](https://nafay3d.com/) · [YouTube](https://www.youtube.com/@nafay3d). Original files, archive hash and adaptations are recorded in tools/nafay-video-editor/STUDIO_SOURCE.json. The supplied package has no explicit licence file. Its code/assets are outside the project MIT grant. Font metadata notices are retained in the bundled FONT_NOTICES.md.

Installation copied/adapted source files only. Setup, model loading, transcription, previews, rendering and tests were deferred. Later validation should cover all seven styles, English/Hindi and Devanagari/Roman captions, cut timing, audio sync, 1080p/4K60/fractional output, feedback and stale approvals, cache reuse, clean setup and dashboard discovery.
