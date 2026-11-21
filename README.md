<div align="center">

<h1><img src="docs/images/wordmark-ivory.svg" width="900" alt="Ravan Reel Studio"></h1>

**Create → Review → Finish**  
The open-source AI video workstation: craft high-retention reels, YouTube videos, and Remotion motion graphics locally with your coding agent.

[![Node.js 22+](https://img.shields.io/badge/Node.js-22+-339933?style=flat&logo=node.js&logoColor=white)](https://nodejs.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Remotion](https://img.shields.io/badge/Remotion-Video_in_React-0B84F3?style=flat)](https://www.remotion.dev/)
[![Tests Passing](https://img.shields.io/badge/Unit_Tests-49%2F49_Passing-brightgreen?style=flat)](#)
[![AI Brain](https://img.shields.io/badge/AI_Brain-24_Skills_Synced-8A2BE2?style=flat)](#-centralized-ai-brain-integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[🚀 Start with AI](#start-with-your-ai-assistant) · [🧠 AI Brain Skills](#-centralized-ai-brain-integration) · [⌨️ Commands](#commands) · [💻 System Requirements](#system-requirements) · <a href="https://www.youtube.com/@techno_ravan"><img src="docs/images/youtube.png" width="16" alt=""> Techno Ravan on YouTube</a>

Built by **[Nayan Vekariya (Techno Ravan)](#about-the-creator)**

</div>

---

## Start with your AI assistant

Paste this into any coding assistant with access to your computer’s workspace and terminal (e.g., **Google Antigravity**, **Claude Code**, **OpenAI Codex**, or **Cursor**):

```text
Install Ravan Reel Studio from https://github.com/Nayan014/ravan-reel-studio and open the demo dashboard on my computer.
```

On first launch, the studio downloads its local dependencies and opens the review dashboard in your browser. If you already have a local checkout, start the studio via:
```bash
npm start
# Opens review dashboard at http://127.0.0.1:4173 with Universal AI DevBar active
```

---

## How the Studio Works

Start from a raw concept or bring your own recordings. Choose **Reel Plan** for 9:16 portrait shorts or **Video Plan** for landscape YouTube videos. The pipeline guides you through planning, frame-by-frame approval, and multi-track export:

<picture>
  <source media="(max-width: 640px)" srcset="docs/images/workflow-mobile-ivory-planning.svg">
  <img src="docs/images/workflow-ivory-planning.svg" width="1260" alt="Idea → Script → Record, or existing recordings → Scene plan → Frame and audio review → Your approval → Render and download">
</picture>

---

## 🧠 Centralized AI Brain Integration

Ravan Reel Studio is directly integrated with the **[Centralized AI Brain](../ai-brain)**. All AI agents working in this studio share **24 active production skills** and persistent session memory:

| Skill | Category | Purpose |
| :--- | :--- | :--- |
| **`safe-area-standard`** | Global | Multi-platform 9:16 safe area boundaries & overlay HUD simulator |
| **`creator-brand-voice`** | Global | Authentic Techno Ravan developer voice (clean, direct, zero em dashes) |
| **`ui-ux-pro-max`** | Global | Studio UI heuristics, design systems, and Remotion CSS/Canvas styling |
| **`captions`** | Studio | Platform-optimized social posting copy (Instagram, YouTube, TikTok, LinkedIn) |
| **`effects`** | Studio | Local effects pipeline (selfie segmentation, depth glow, glass widgets, spotlight) |
| **`wf-reel-plan`** | Studio | Full end-to-end portrait reel planning, pacing, and storyboard generator |
| **`studio-lighting`** | Studio | Synthetic 3-point face lighting simulation & color grading |
| **`sound-design`** | Studio | Sound effects timing, risers, whooshes, and audio mix balance |
| **`cover-image`** | Studio | High-CTR portrait covers and landscape thumbnails |
| **`wf-nafay`** | Studio | Nafay 3D motion graphics editor with 7 landscape aesthetics |

For full documentation and skill management instructions, read **[AI_SKILLS.md](AI_SKILLS.md)**.

### Universal DevBar Injected
The studio's review dashboard (`:4173`) automatically includes the **Universal AI DevBar** at the bottom-right corner:
- Toggle studio and global skills ON/OFF live without restarting.
- One-click jump to the Standalone Console (`:4999`) and Faceless Shorts Dashboard (`:8765`).
- View and update session goals from `STATE.md`.

---

## Create your first reel or YouTube video

1. **Start the studio**: Run `npm start` (or `node scripts/dashboard.mjs`).
2. **Bring your recordings**: Place numbered clips (`1.mp4`, `2.mp4`...) into `inputs/my-first-reel/`. Send `/wf-reel-plan` for a reel or `/wf-video-plan` for YouTube. Choose **I have footage** and select the folder.
3. **Review the direction**: Comment on the interactive plan and approve it to see actual preview frames. Give scene-by-scene feedback and select music.
4. **Finish your reel**: Approve final frames. The studio renders effects, captions, and audio mixes locally, adding your finished export to the dashboard.

> **Starting with an idea?** Send `/wf-reel-plan` or `/wf-video-plan` and choose **I have an idea** or **Suggest ideas**. Approve the script, record your takes, and continue in the same session. Choose **Resume a project** to pick up saved work.

<details>
<summary><strong>See a frame review and three sample effects</strong></summary>

![Review page with feedback fields beneath individual preview frames](docs/images/review.jpg)

| Orbit | Spotlight | Glass widgets |
| :---: | :---: | :---: |
| <img src="skills/effects/assets/reference-previews/orbit.jpg" width="170" alt="Orbit reference"> | <img src="skills/effects/assets/reference-previews/spotlight.jpg" width="170" alt="Spotlight reference"> | <img src="skills/effects/assets/reference-previews/glass-widgets.jpg" width="170" alt="Glass widgets reference"> |

[Browse the illustrated effects guide](docs/Video_Effects_Visual_Guide.pdf)

</details>

---

## Commands Cheat Sheet

Send these shortcuts directly to your coding assistant:

| Command | Purpose |
| :--- | :--- |
| `/wf-reel-plan` | Create a portrait reel from an idea, recordings, or a saved project |
| `/wf-video-plan` | Create a landscape YouTube video from an idea, footage, or a saved project |
| `/wf-video` | Choose Vibha effects or Nafay graphics for a single video |
| `/wf-nafay` | Edit one landscape video with Nafay 3D’s motion-graphics styles |
| `/wf-gallery` | Browse the interactive effect reference pictures |
| `/wf-effects` | Apply a named effect directly to an input take |
| `/wf-resume` | Resume a saved video edit session |
| `/cover-image` | Create or revise a video cover using the Techno Ravan style standard |
| `/india-map` | Prepare an official animated map using Survey of India boundary depiction |
| `/captions` | Author multi-platform social captions (Instagram, YouTube, TikTok, LinkedIn) |

---

## 💻 System Requirements

| Use | Processor Guidance | RAM | Suggested SSD Space |
| :--- | :--- | ---: | ---: |
| **Dashboard & file review** | Modern laptop supporting Node.js 22+ | 8 GB | Standard media space |
| **Short 1080p reels** | Apple Silicon (M1+) or modern multicore CPU | 16 GB | 20 GB+ |
| **4K/60 master reels** | Apple Silicon Pro/Max or strong workstation CPU | 32 GB+ | 50 GB+ |

---

## 🧪 Testing & Reliability

The studio includes a comprehensive unit and dashboard test suite:
```bash
npm run test:dashboard
```
- Validates safe-area bounds math, danger zones, frame review flows, dashboard APIs, and session isolation.
- **49/49 unit and integration tests passing.**

---

## 📜 Credits and License

| Contribution | Credit |
| :--- | :--- |
| **Original effects engine & catalogue** | [Vibha Ramprakash — claude-video-effects](https://github.com/Vibha-Ramprakash/claude-video-effects) |
| **Guided workflows, review studio & DevBar** | [Techno Ravan (Nayan Vekariya)](https://github.com/Nayan014) |
| **Dashboard & Remotion kit** | [Techno Reel by Nayan V.](https://github.com/Nayan014/techno-reel) |
| **7 Motion graphics styles** | [Nafay 3D](https://nafay3d.com/) · [YouTube](https://www.youtube.com/@nafay3d) |
| **HTML finishing and Studio editor** | [Hyperframes by HeyGen](https://github.com/heygen-com/hyperframes) |

Distributed under the **[MIT License](LICENSE)**.

---

## About the Creator

<div align="center">

<a href="https://vekariya.ai.studio/"><img src="https://github.com/Nayan014.png?size=400" width="140" height="140" style="border-radius:50%;" alt="Nayan Vekariya"></a>

### Nayan Vekariya
**Techno Ravan**

I build developer tools, AI workflows, and share engineering tutorials on YouTube.<br>
Connect through my website and social platforms:

<a href="https://www.youtube.com/@techno_ravan"><img src="docs/images/social-youtube-ivory.svg" width="160" height="44" alt="YouTube"></a>
<a href="https://www.linkedin.com/in/nayan-vekariya/"><img src="docs/images/social-linkedin-ivory.svg" width="160" height="44" alt="LinkedIn"></a>
<a href="https://www.instagram.com/techno_ravan/"><img src="docs/images/social-instagram-ivory.svg" width="160" height="44" alt="Instagram"></a>
<a href="https://vekariya.ai.studio/"><img src="docs/images/social-website-ivory.svg" width="160" height="44" alt="Website"></a>

</div>
