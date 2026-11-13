# Set up Ravan Reel Studio

The repository root contains the application. Open that folder in an agent with local file access and a terminal; no global skill installation is required. Dashboard viewing and video production have different requirements.

## Platform and laptop guidance

macOS on Apple Silicon is validated. The reference machine is an Apple M4 Pro with 48 GB memory. Linux and Windows instructions below are provided for portability and remain unverified end to end.

| Task | Practical recommendation | Storage guidance |
| --- | --- | --- |
| Browse the dashboard | Modern Node-compatible laptop, 8 GB RAM | Existing media plus browser storage |
| Short 1080p reels | Apple Silicon or modern multicore Intel/AMD, 16 GB RAM, SSD | 20 GB+ free, excluding originals |
| 4K/60 reels | Pro-class Apple Silicon or strong multicore Intel/AMD, 32 GB+ RAM, SSD | 50 GB+ free, excluding originals |

These are starting recommendations, not measured minimums. A 48 GB machine working successfully does not establish a minimum RAM requirement. Longer shots, effect tracking, large images and browser rendering increase memory and time. Temporary copies and previews can occupy several times the size of a source clip. A dedicated NVIDIA GPU is not required for default CPU transcription; the current workflow does not automatically accelerate every stage when a GPU is present.

## Software prerequisites

| Tool | Needed for |
| --- | --- |
| Node.js 22.18+ | Dashboard, Hyperframes, legacy Remotion |
| Python 3.10+ with compatible wheels | Effects and local speech analysis; use Python 3.12 or 3.13 |
| System ffmpeg and ffprobe | Source inspection, trimming, audio and video encoding |
| Chrome/Chromium | Hyperframes actual-frame capture, Studio and rendering |
| Coding agent with terminal/file access | Planning, reviewing feedback and running production |

The default reel backend is `faster-whisper==1.2.1`, using `small.en` for English and `small` for other selected languages, on CPU with INT8. The [upstream CPU reference](https://github.com/SYSTRAN/faster-whisper#small-model-on-cpu) is a component benchmark, not a whole-project performance guarantee. If `mlx-whisper` is already installed, the existing Apple Silicon backend is selected instead; it is optional and not installed by this setup.

## Recommended: setup, demo and browser in one command

From the repository root:

```bash
npm start
```

Node.js with npm must be installed to invoke the command. Node 22.18+ runs directly; an older Node/npm installation uses an isolated Node 22 runtime selected through npm. Nothing upgrades global Node. The launcher then:

1. Finds a compatible Python and ffmpeg/ffprobe; installs missing system tools through an available supported package manager.
2. Runs the existing reel setup to prepare the effects virtual environment and `faster-whisper`.
3. Installs the pinned Hyperframes runtime when its dependency lock changes and locates/downloads Chrome/Chromium.
4. Downloads and checks the default English CPU speech model, preferring its local cache on repeat runs.
5. Adds the synthetic demo without overwriting an existing project, starts the local dashboard and opens the demo overview.

macOS uses Homebrew if system tools are missing. Windows uses winget; Debian/Ubuntu uses apt with root/sudo when needed. Install Homebrew or your missing base tools yourself if no supported package manager is available, then rerun `npm start`. Package managers may require administrator permission or agreement review; the launcher does not automatically accept agreements. No Docker, voice-generation service, GPU package stack or legacy Remotion installation is added by this default path.

Keep the terminal open for a new dashboard. Ctrl+C stops it. A repeat invocation reuses a dashboard only when it identifies the same workspace. Other occupied ports are skipped automatically; trust the printed URL. To suppress browser opening, use `npm start -- --no-open`. If automatic opening fails, setup still prints the URL. Headless/cloud environments need their own port forwarding; opening a dashboard in a cloud sandbox is not a validated end-to-end workflow.

Other selected languages/custom speech models, optional MLX setups and legacy Remotion projects can need their own additional downloads. First startup needs internet; warm startup reuses caches. To avoid installing production tools just to browse files, use the dashboard-only commands below.

## Dashboard only

From the repository root:

```bash
node --version
npm run dashboard
```

Open `http://127.0.0.1:4173`. The library starts empty. No npm dependency installation, Python or ffmpeg is required for browsing. Press Ctrl+C to stop it. On macOS/Linux choose another port with `DASHBOARD_PORT=4174 npm run dashboard`. On PowerShell use `$env:DASHBOARD_PORT=4174; npm run dashboard`.

The server accepts its printed `127.0.0.1` address, not LAN access. See [the dashboard guide](DASHBOARD.md).

## Manual production setup on macOS

Install the prerequisites using your normal package manager or official installers. For example, with Homebrew already installed:

```bash
brew install node@22 python@3.13 ffmpeg
# If Homebrew's versioned executables are not already on PATH:
export PATH="$(brew --prefix node@22)/bin:$(brew --prefix python@3.13)/libexec/bin:$PATH"
```

Ensure the installed executables are on PATH and `node --version` reports at least 22.18. Then, from the repository root:

```bash
bash skills/effects/scripts/setup.sh --reel
npm --prefix tools/hyperframes ci
node tools/hyperframes/hyperframes.mjs browser ensure
skills/effects/.venv/bin/python scripts/reel_workflow.py doctor
```

The setup creates `skills/effects/.venv` and installs base effects plus speech dependencies. Re-running `--reel` checks imports and upgrades an existing effects-only environment without replacing it. For effects alone, omit `--reel`.

The Hyperframes wrapper uses installed Google Chrome on macOS when available, otherwise its managed browser. To use another installed executable, set `HYPERFRAMES_BROWSER_PATH` to its full path. It keeps runtime caches under the tool folder and disables Hyperframes telemetry/update checks.

## Linux guidance — not yet validated end to end

Install Node 22.18+, Python 3.12/3.13 with venv support, ffmpeg/ffprobe and the system libraries required by Chrome/Chromium using your distribution's package manager. Run the same four production setup commands above. Browser sandbox and shared-library requirements vary by distribution; preserve browser security settings and follow the browser's installation guidance rather than disabling its sandbox.

## Windows guidance — not yet validated end to end

Install Node 22.18+, Python 3.12/3.13, Git, ffmpeg/ffprobe and Chrome/Chromium with official installers or your normal package manager. Confirm they are on PATH. In PowerShell, from the repository root:

```powershell
py -3 -m venv skills/effects/.venv
skills/effects/.venv/Scripts/python.exe -m pip install --upgrade pip
skills/effects/.venv/Scripts/python.exe -m pip install -r skills/effects/requirements-reel.txt
npm --prefix tools/hyperframes ci
node tools/hyperframes/hyperframes.mjs browser ensure
skills/effects/.venv/Scripts/python.exe scripts/reel_workflow.py doctor
```

Use `.venv/Scripts/python.exe` in place of `.venv/bin/python` in subsequent commands. If your checkout does not preserve relative skill symlinks, tell your agent to read `AGENTS.md` and the canonical `skills/` files directly. Do not copy a virtual environment from another operating system.

## First reel and downloads

1. Put unique numbered recordings in `inputs/your-reel/`.
2. Open the repository in your coding agent and ask it to read `AGENTS.md`.
3. Invoke `/wf-reel-plan`, or say “Use the wf-reel skill.” Choose an idea, existing footage or a saved project within the same command. Use `/wf-video-plan` for a landscape YouTube video.
4. Confirm actual speech and visual choices, review actual frames/audio, then approve the current revision.
5. Find the resulting files in `outputs/reels/` and review them in the dashboard.

Initial package installation needs internet. `browser ensure` downloads Chromium if an adequate browser is missing. First speech analysis downloads the selected model; later runs use cached weights and transcripts. The workflow keeps its model cache under `skills/effects/.cache/huggingface` unless you explicitly configure `HF_HOME`. Python package downloads use the local setup cache; npm uses its configured package cache. Existing public models/fonts/audio are shipped with their notices.

After packages, browser and model weights are present, default local media processing can work offline. The agent itself, idea research and explicitly chosen external services can still need internet or an account. Cached weights alone do not make a hosted chat offline. No voice-cloning or social publishing service is part of the default reel setup.

## Legacy projects

Existing Remotion projects keep their engine. Install its dependencies only when you need that path:

```bash
npm --prefix tools/techno-reel ci
```

Do not run the upstream voice-engine setup for a recorded-voice reel. New reel runs use Hyperframes. See [combined workflow details](COMBINED_REEL_WORKFLOW.md).

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `node` missing or too old | Install Node 22.18+ and reopen the terminal; inspect `node --version`. |
| `NEED_FFMPEG` | Install system ffmpeg and confirm both `ffmpeg -version` and `ffprobe -version` work. |
| Python installation fails | Use a supported Python with available wheels and a fresh venv; do not copy the reference machine's environment. Keep the error log. |
| `No module named faster_whisper` | Run `bash skills/effects/scripts/setup.sh --reel` or the Windows reel requirements command. |
| Speech model unavailable offline | Connect once to download the chosen model, then retry locally. |
| Chrome missing | Run the wrapper's `browser ensure`, or set `HYPERFRAMES_BROWSER_PATH` to an installed compatible browser. |
| Empty dashboard | Expected before a saved project exists; source videos alone do not create projects. |
| Port 4173 is occupied | Choose another `DASHBOARD_PORT`; use the matching review URL. |
| Approval rejected | Plan/source/profile/frame/audio content changed. Resolve feedback and create a fresh review. |
| Slow or memory-heavy 4K rendering | Keep takes short, close other heavy apps and retain ample SSD space. Choose lower output quality explicitly if appropriate, then review it again. |

Keep originals. Do not delete active project caches blindly: they support reuse and approval checks. Commands and exact effect options are in [the workflow menu](../skills/wf/SKILL.md) and [effects skill](../skills/effects/SKILL.md).

## YouTube planning and production

`/wf-video-plan` uses the same installed production tools as `/wf-reel-plan`. New YouTube projects use `outputs/videos/` and landscape output; no additional renderer installation is required. The implementation of the two planning entry points and landscape pipeline awaits the deferred workflow testing session.
