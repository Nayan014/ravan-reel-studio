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

## How the studio works

Start with an idea or bring recordings. Both paths lead through a scene plan, frame and audio review, your approval, and a finished reel.

<picture>
  <source media="(max-width: 640px)" srcset="docs/images/workflow-mobile.svg">
  <img src="docs/images/workflow.svg" width="1260" alt="Idea → Script → Record, or existing recordings → Scene plan → Frame and audio review → Your approval → Render and download">
</picture>

## Create your first reel

| Step | What you do | What happens next |
| --- | --- | --- |
| **1. Start the studio** | Paste the installation prompt above into your coding agent. | The studio opens the demo dashboard. |
| **2. Bring your recordings** | Save numbered clips in `inputs/my-first-reel/`, then send `/wf-reel` in your agent and choose that folder. | The agent transcribes your takes and prepares the scene plan. |
| **3. Review the direction** | Comment on the plan and approve it to see actual preview frames. Give frame feedback and choose music. | The agent revises the affected scenes and refreshes the review. |
| **4. Finish your reel** | Approve the current frames and audio. | The studio renders effects, captions and sound, then adds your export to the dashboard. |

> **Starting with an idea?** Send `/wf-reel-plan` first. Develop the script and shooting plan with your agent, approve it, then record your numbered takes and continue with `/wf-reel`.

Name the clips `1.mp4`, `2.mp4`, `3.mp4` and so on. If your assistant does not recognise slash commands, ask it to read `AGENTS.md` and use the corresponding skill.

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

Send these shortcuts directly to your coding assistant.

| Command | Purpose |
| --- | --- |
| `/wf-video` | Guided edit of a single video |
| `/wf-reel-plan` | Develop and approve a script before recording |
| `/wf-reel` | Combine numbered recorded takes |
| `/wf-gallery` | Browse the effect reference pictures |
| `/wf-effects` | Apply a named effect |
| `/wf-resume` | Resume a saved single-video edit |

<details>
<summary>Prefer the numbered workflow menu?</summary>

Send `/wf`, then reply with a menu number. For example, `/wf` followed by **5** starts the same workflow as `/wf-reel`.

| Reply | Workflow |
| --- | --- |
| 1 | Single-video edit |
| 2 | Effect gallery |
| 3 | Named effect |
| 4 | Resume an edit |
| 5 | Recorded reel |
| 6 | Script and shooting plan |

</details>

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

<div align="center">

<a href="https://vekariya.ai.studio/"><img src="https://github.com/Nayan014.png?size=400" width="160" height="160" alt="Nayan Vekariya, creator of Ravan Reel Studio"></a>

### Nayan Vekariya

**Techno Ravan**

I build Ravan Reel Studio and share tutorials on the Techno Ravan channel.<br>
Explore the project with me on YouTube, or connect through my website and socials.

<a href="https://www.youtube.com/@techno_ravan"><img src="docs/images/social-youtube.svg" width="168" height="48" alt="Watch Techno Ravan on YouTube"></a>
<a href="https://www.linkedin.com/in/nayan-vekariya/"><img src="docs/images/social-linkedin.svg" width="168" height="48" alt="Connect with Nayan on LinkedIn"></a>
<a href="https://www.instagram.com/techno_ravan/"><img src="docs/images/social-instagram.svg" width="168" height="48" alt="Follow Techno Ravan on Instagram"></a>
<a href="https://vekariya.ai.studio/"><img src="docs/images/social-website.svg" width="168" height="48" alt="Visit Nayan’s website"></a>

</div>
