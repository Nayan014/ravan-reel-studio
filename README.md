# Ravan Reel Studio

**Create, review and finish reels locally with your coding agent.**

Built by **Techno Ravan**, using **[Vibha Ramprakash’s open-source video effects engine](https://github.com/Vibha-Ramprakash/claude-video-effects)**. Vibha created the original effects engine; this project adds guided workflows, interactive review, a project dashboard and finishing integrations.

Turn a folder of recorded takes into a reel, or develop an idea into a script before recording. Review the script, comment on individual scenes and frames, choose music, then approve the finished direction before rendering.

## What you can do

- Apply **51 talking-head effects and 3 bonus looks** from the bundled catalogue.
- Plan short recording takes, transcribe speech locally and trim recordings.
- Review HTML plans and actual frames with feedback attached to the right revision.
- Finish new reels with **Vibha → Hyperframes**: effects, one spoken-caption layer, music and sound cues.
- Match source resolution and frame rate up to portrait **4K/60**, including fractional rates. Mixed sources require an explicit choice.
- Browse reels, covers, posting copy and downloads in a local dashboard.

Existing Remotion projects remain compatible. Creation and editing happen with your coding agent; the dashboard collects review feedback and does not run AI on its own.

## A look inside

![Ravan Reel Studio library with demonstration projects](docs/images/dashboard.jpg)

*Actual dashboard with synthetic demonstration projects: colour-card footage, tones and a credited upstream example voice. No personal recordings are shown. The bundled six-second demo described below is installed by `npm start`; this screenshot also shows separate test projects.*

<details>
<summary>See feedback beneath actual preview frames</summary>

![Ravan Reel Studio frame feedback](docs/images/review.jpg)

*This review example uses colour cards and tones. Its sample captions demonstrate the interface; they are not transcriptions of the tones.*

</details>

| Original effects: orbit | Original effects: spotlight | Original effects: glass widgets |
| --- | --- | --- |
| <img src="skills/effects/assets/reference-previews/orbit.jpg" width="170" alt="Orbit effect reference"> | <img src="skills/effects/assets/reference-previews/spotlight.jpg" width="170" alt="Spotlight effect reference"> | <img src="skills/effects/assets/reference-previews/glass-widgets.jpg" width="170" alt="Glass widgets effect reference"> |

*Bundled effect references, not effects applied to your footage. [Browse the illustrated guide](docs/Video_Effects_Visual_Guide.pdf).*

## Can my laptop run it?

These are **practical starting recommendations, not benchmarked minimum requirements**. A desktop with comparable specifications also works.

| Use | Processor guidance | RAM | Suggested free SSD space |
| --- | --- | ---: | ---: |
| Dashboard and reviewing files | Modern laptop supporting Node.js | 8 GB | Space for your media |
| Short 1080p reels | Apple Silicon or a modern multicore Intel/AMD CPU | 16 GB | 20 GB+ |
| 4K/60 reels | Apple Silicon Pro-class or a strong modern multicore CPU | 32 GB+ | 50 GB+ |

Rendering space is **additional to original recordings**. Copied sources, intermediate videos, actual-frame previews, model downloads and caches consume more disk space. Longer takes and complex effects increase memory use and render time; real-time rendering is not promised.

The reference machine is **Apple M4 Pro with 48 GB memory**. This is the tested configuration, not a requirement. macOS is validated; Windows and Linux have setup guidance but have not been validated end to end. The default transcription backend runs on CPU; a dedicated NVIDIA GPU is not required for that path. See the [upstream CPU implementation](https://github.com/SYSTRAN/faster-whisper#small-model-on-cpu) and [setup details](docs/SETUP.md).

## Quick start — one command

Install **Node.js with npm** first (Node 22.18+ recommended). Then clone the repository and run:

```bash
git clone https://github.com/Nayan014/ravan-reel-studio.git
cd ravan-reel-studio
npm start
```

`npm start` prepares the local reel tools, caches the default English speech model, installs the safe demo and **opens its dashboard page in your browser**. Press Play to watch the pre-rendered example. No separate `npm install` or frontend build is needed. If your Node version is older than 22.18, the launcher selects an isolated Node 22 runtime without changing global Node.

Missing Python and ffmpeg are installed through **Homebrew on macOS**, **winget on Windows**, or **apt on Debian/Ubuntu** when available. Normal administrator or package-agreement prompts may appear. If no supported package manager is available, setup prints the missing prerequisites and how to continue. macOS is validated; Windows/Linux automation is provided but remains unverified end to end. [Detailed setup →](docs/SETUP.md)

The first run needs internet and can download substantial packages/model weights. Later starts reuse the environment, renderer and model cache. Existing projects and demo changes are preserved. New dashboards run in this terminal; Ctrl+C stops them. A running dashboard for the same workspace is reused, and an occupied port belonging to another app/workspace is left alone.

The browser opens the synthetic demo's overview on the printed `127.0.0.1` address, usually port 4173. On a headless machine use `npm start -- --no-open` and access the printed URL through your own port forwarding. The server remains bound to this device.

### Dashboard or demo only

To browse without installing the production tools, use `npm run dashboard`. A fresh clone's library is empty until a project or demo is added. `npm run demo` installs only the bundled example; no Python, ffmpeg or AI service is required for that command.

The six-second **synthetic demo** contains generated colour cards and quiet test tones, with **no personal footage, faces or recorded speech**. It demonstrates playback, covers, posting copy and downloads. [Demo details and reproducible generator →](examples/demo/README.md)

Your recordings and generated projects remain ignored by Git, including the installed demo under `outputs/`. The one public video exception is the bundled `examples/demo/export/demo.mp4`; credited library audio retains its own explicit exceptions.

## Create your first reel

### 1. Prepare the production tools

If `npm start` completed, continue to step 2. For manual setup, you need **Python 3.10+**, **ffmpeg and ffprobe**, **Node.js 22.18+**, and **Chrome/Chromium**. Use a compatible Python 3.12 or 3.13 installation. Initial dependency and model downloads require internet access.

From the repository root on macOS/Linux:

```bash
bash skills/effects/scripts/setup.sh --reel
npm --prefix tools/hyperframes ci
node tools/hyperframes/hyperframes.mjs browser ensure
skills/effects/.venv/bin/python scripts/reel_workflow.py doctor
```

`--reel` installs the effects dependencies and the tested CPU speech-transcription backend. These commands do not install the optional legacy Remotion renderer. See [Windows instructions, offline use and troubleshooting](docs/SETUP.md).

### 2. Add your recordings

Create a folder such as:

```text
inputs/my-first-reel/
  1.mp4
  2.mp4
  3.mp4
```

Use unique numbered filenames. Keep your original recordings; the workflow imports copies. Videos and generated output are ignored by Git.

### 3. Open the folder in your coding agent

Use an agent with local file and terminal access. Ask it to **read `AGENTS.md`**, then send:

```text
/wf-reel
```

Choose the recording folder, confirm the speech, choose treatments, review the plan and actual frames, and audition music. Full rendering waits for approval of the current frames and audio. If slash commands are unavailable, say **“Read AGENTS.md and use the wf-reel skill.”**

Starting without footage? Use **`/wf-reel-plan`** to choose an idea, review the script and shooting plan, then attach numbered recordings later.

Finished reels, previews and posting copy live in `outputs/reels/`. Single-video edits live in `outputs/edits/`. Feedback is processed by the active agent or collected when you resume. [Full reel workflow →](docs/COMBINED_REEL_WORKFLOW.md)

## Commands

Send `/wf` to open the menu. Numbers apply only while that menu is awaiting your choice.

| Pick | Command | Purpose |
| --- | --- | --- |
| 1 | `/wf-video` | Guided edit of a single video |
| 2 | `/wf-gallery` | Browse the effect reference pictures |
| 3 | `/wf-effects` | Apply a named effect |
| 4 | `/wf-resume` | Resume a saved single-video edit |
| 5 | `/wf-reel` | Combine numbered recorded takes |
| 6 | `/wf-reel-plan` | Develop and approve a script before recording |

`/wf reel`, `/wf reel-plan`, `/video-edit` and `/effects` remain available. Command discovery varies by agent; reading the shared instructions is the portable fallback.

## Local processing, privacy and costs

Speech analysis, trimming and video rendering run locally in the default reel workflow. Your chosen coding agent may use an external AI service and may incur subscription or API costs. Idea research can use the internet. Do not assume media or chat attachments stay on your device merely because rendering is local.

The first run downloads packages, a browser if needed, and a speech model. Once cached, the default media-processing steps can run without a model API. Caches are reused for unchanged speech, clips and effects. No social account, voice-generation service or automatic publishing is required.

## Help and development

- **Empty library:** expected with dashboard-only setup. Run `npm start` for the bundled demo, or create a project with your agent.
- **Port busy:** set `DASHBOARD_PORT=4174` before `npm run dashboard`.
- **Missing speech dependency:** rerun `bash skills/effects/scripts/setup.sh --reel`.
- **Changed plan or frames:** generate a fresh review and approve that revision.
- **Slow rendering:** close heavy apps, keep takes short and use an SSD. Changing music reuses valid effect clips; changing output quality requires new video artifacts.

See [setup and troubleshooting](docs/SETUP.md), [review controls](docs/WORKFLOW_REVIEW.md), and [contributing and verification](CONTRIBUTING.md).

## Credits and licence

| Contribution | Credit |
| --- | --- |
| Original effects engine and bundled effect catalogue | [Vibha Ramprakash — claude-video-effects](https://github.com/Vibha-Ramprakash/claude-video-effects) |
| Guided workflows, review integration and Ravan Reel Studio | Techno Ravan |
| Adapted dashboard and legacy Remotion kit | [Techno Reel by Nayan V.](https://github.com/Nayan014/techno-reel) |
| HTML finishing and Studio editor | [Hyperframes by HeyGen](https://github.com/heygen-com/hyperframes) |
| Music, sound effects, fonts and tracking models | Individual authors listed in [third-party notices](THIRD_PARTY_NOTICES.md) |

Original project contributions use the [MIT licence](LICENSE). Third-party code, media, fonts and models retain their own licences and notices. The project licence does not replace those terms. Upstream versions and local adaptations are recorded in [SOURCE.json](SOURCE.json).
