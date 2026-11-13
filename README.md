<div align="center">

<h1><img src="docs/images/wordmark.png" width="900" alt="Ravan Reel Studio"></h1>

**Create → Review → Finish**  
Make reels locally with your coding agent.

[🚀 Get started](#start-with-your-ai-assistant) · [⌨️ Commands](#commands) · [💻 System requirements](#system-requirements) · <a href="https://www.youtube.com/@techno_ravan"><img src="docs/images/youtube.png" width="20" alt=""> Techno Ravan on YouTube</a>

Built by **[Nayan Vekariya (Techno Ravan)](#about-the-creator)**

</div>

## Start with your AI assistant

Paste this into a coding assistant with access to your computer’s files and terminal, such as Codex or Gemini CLI.

```text
Install Ravan Reel Studio from https://github.com/Nayan014/ravan-reel-studio and open the demo dashboard on my computer.
```

On the first launch, the studio downloads its tools and opens the bundled demo in your browser. Press **Play** to watch the six-second reel. If you already have a local checkout, run `npm start` from the project folder.

## Create your first reel

```mermaid
flowchart TD
    A["Have an idea? · /wf-reel-plan"] --> B["Approve your script and record your takes"]
    B --> C["Have recordings? · /wf-reel"]
    C --> D["Review the scene plan and choose effects"]
    D --> E["Check actual frames and audition music"]
    E --> F["Approve, render and download your reel"]
```

**Start with what you have.**

| Starting point | What to do |
| --- | --- |
| An idea | Send `/wf-reel-plan`. Review the script, give feedback on any scene, then record the approved takes. |
| Recorded clips | Put your clips in `inputs/my-first-reel/`, named `1.mp4`, `2.mp4` and so on. Send `/wf-reel` and choose that folder. |

**Review your footage.** The studio transcribes the takes locally and proposes a scene plan. Choose effects, then approve the plan to see preview frames from your recordings. Type feedback beneath any frame you want to change.

**Finish the reel.** Listen to music against your voice and approve the frames and audio. The studio renders the effects, adds captions and sound cues, and makes your export available in the local dashboard.

The workflow matches recording quality up to portrait **4K/60**, including fractional frame rates. When takes differ, you choose the output profile.

<details>
<summary><strong>See a frame review and three sample effects</strong></summary>

![Review page with feedback fields beneath individual preview frames](docs/images/review.jpg)

| Orbit | Spotlight | Glass widgets |
| :---: | :---: | :---: |
| <img src="skills/effects/assets/reference-previews/orbit.jpg" width="170" alt="Orbit reference"> | <img src="skills/effects/assets/reference-previews/spotlight.jpg" width="170" alt="Spotlight reference"> | <img src="skills/effects/assets/reference-previews/glass-widgets.jpg" width="170" alt="Glass widgets reference"> |

[Browse the illustrated effects guide](docs/Video_Effects_Visual_Guide.pdf)

</details>

## Commands

Type any command below directly into your coding assistant. If you open the menu with `/wf`, reply with the number in the last column. For example, replying **5** in that menu starts `/wf-reel`.

| Command | Purpose | Reply in the `/wf` menu |
| --- | --- | --- |
| `/wf-video` | Guided edit of a single video | 1 |
| `/wf-reel-plan` | Develop and approve a script before recording | 6 |
| `/wf-reel` | Combine numbered recorded takes | 5 |
| `/wf-gallery` | Browse the effect reference pictures | 2 |
| `/wf-effects` | Apply a named effect | 3 |
| `/wf-resume` | Resume a saved single-video edit | 4 |

`/wf reel`, `/wf reel-plan`, `/video-edit` and `/effects` remain available. Command discovery varies by agent; reading the shared instructions is the portable fallback.

## System requirements

| Use | Processor guidance | RAM | Suggested free SSD space |
| --- | --- | ---: | ---: |
| Dashboard and reviewing files | Modern laptop supporting Node.js | 8 GB | Space for your media |
| Short 1080p reels | Apple Silicon or a modern multicore Intel/AMD CPU | 16 GB | 20 GB+ |
| 4K/60 reels | Apple Silicon Pro-class or a strong modern multicore CPU | 32 GB+ | 50 GB+ |

These figures are practical starting points. Allow the suggested free space in addition to your original footage. Long takes and complex effects need more time and memory.

Tested on macOS with an **Apple M4 Pro and 48 GB of memory**. Windows and Linux setup instructions are available, with end-to-end validation pending. Default speech recognition runs on the CPU. [Setup and troubleshooting](docs/SETUP.md) · [Upstream CPU documentation](https://github.com/SYSTRAN/faster-whisper#small-model-on-cpu)

Speech recognition, trimming and rendering run locally. Your coding assistant may use an external service and incur charges. Git ignores your recordings and generated exports.

## Guides and contributions

[Reel workflow](docs/COMBINED_REEL_WORKFLOW.md) · [Review controls](docs/WORKFLOW_REVIEW.md) · [Contributing](CONTRIBUTING.md)

## Credits and licence

| Contribution | Credit |
| --- | --- |
| Original effects engine and bundled effect catalogue | [Vibha Ramprakash — claude-video-effects](https://github.com/Vibha-Ramprakash/claude-video-effects) |
| Guided workflows, review integration and Ravan Reel Studio | Techno Ravan |
| Adapted dashboard and legacy Remotion kit | [Techno Reel by Nayan V.](https://github.com/Nayan014/techno-reel) |
| HTML finishing and Studio editor | [Hyperframes by HeyGen](https://github.com/heygen-com/hyperframes) |
| Music, sound effects, fonts and tracking models | Individual authors listed in [third-party notices](THIRD_PARTY_NOTICES.md) |

Original project contributions use the [MIT licence](LICENSE). Third-party code, media, fonts and models retain their own licences and notices. The project licence does not replace those terms. Upstream versions and local adaptations are recorded in [SOURCE.json](SOURCE.json).

## About the creator

<table>
<tr>
<td align="center" width="150"><a href="https://vekariya.ai.studio/"><img src="https://github.com/Nayan014.png?size=320" width="124" alt="Nayan Vekariya"></a></td>
<td>

**Nayan Vekariya** · Techno Ravan

I build Ravan Reel Studio and share tutorials on the Techno Ravan channel.

<a href="https://www.youtube.com/@techno_ravan"><img src="docs/images/youtube.png" width="20" alt=""> <strong>Watch on YouTube</strong></a>

[Website](https://vekariya.ai.studio/) · [LinkedIn](https://www.linkedin.com/in/nayan-vekariya/) · [Instagram](https://www.instagram.com/techno_ravan/)

</td>
</tr>
</table>
