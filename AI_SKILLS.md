# 🧠 AI Skills & Architecture Guide: Video Effects Studio

This repository is connected to the **Centralized AI Brain** (`../ai-brain`). All AI coding agents working in this repository (Google Antigravity, Claude Code, ChatGPT, OpenAI Codex, and Cursor) share a synchronized set of skills, brand rules, and cross-session memory.

---

## 1. Where Skills Live

**Do not create skills directly in this folder.** Skills are authored once in the shared `ai-brain` repo and mounted here by `scripts/ai_brain.py`:

1. Finds the brain: `$AI_BRAIN_HOME`, `../ai-brain` (side-by-side dev layout) or `.ai-brain/` (auto-cloned on first run).
2. Pulls the latest brain (fast-forward only, at most once an hour, skipped offline or when the brain has local edits).
3. Mounts skills: `.claude/skills` (Claude Code), `.agents/skills` (Codex, Cursor, others), `.gemini/skills` and `.gemini/commands` (Antigravity/Gemini), plus `STATE.md`.

It runs from `npm start`, `npm run dashboard` (via `scripts/ai-brain.mjs`) and a Claude Code `SessionStart` hook. The mounted folders are git-ignored, never committed. Force it any time: `python3 scripts/ai_brain.py --pull`.

## 2. Active Skills in this Repository

### Global Skills (Shared Across All Workspace Repos)
- **`safe-area-standard`**: Multi-platform 9:16 vertical video safe area boundaries (Shorts, Reels, TikTok) and preview overlay HUD.
- **`creator-brand-voice`**: Techno Ravan brand voice, direct developer tone, and strict zero-em-dash rule.
- **`ui-ux-pro-max`**: Design system heuristics, color systems, typography, and Remotion CSS/Canvas styling.
- **`ai-brain-manager`**: Autonomous skill manager to create, toggle, and synchronize skills across repos.
- **`captions`**: Platform-optimized social posting copy (Instagram, YouTube, TikTok, LinkedIn) without em dashes.
- **`cover-image`**: High-CTR portrait covers and landscape thumbnails in the Techno Ravan style standard.
- **`sound-design`**: Sound effect timing, risers, swooshes, and audio mix balancing.
- **`baoyu-cover-image`**: Multi-aspect ratio editorial & infographic covers across 11 palettes.
- **`connected-educational-triad`**: 7-step automated pipeline connecting Short ➔ Masterclass ➔ Quiz ➔ Masterclass.

### Project-Scoped Skills (Studio & Workflows)
- **`effects`**: Computer vision and effects pipeline (depth estimation, selfie segmentation, glow shaders, text layers).
- **`wf-reel-plan`**: End-to-end workflow for designing, pacing, and structuring portrait reels.
- **`studio-lighting`**: Synthetic 3-point studio lighting simulation and color grading.
- **`studio-wall-lights`**: Studio background lighting, neon wall washes, and accents.
- **`natural-narration`**: Audio cadence and speech timing refinement.
- **`video-edit`**: Core video editing assembly and cut automation.
- **`wf` / `wf-auto-ai` / `wf-effects` / `wf-gallery` / `wf-nafay` / `wf-resume` / `wf-video` / `wf-video-plan`**: Domain-specific workflow orchestrators.
- **`india-map`**: Animated map overlay graphics.
- **`effect-tailor`**: Visual shader parameter fine-tuning.

---

## 3. How to Add a New Skill to this Project

### Method A: Ask Any AI Agent (Recommended)
Simply ask your AI assistant in chat:
> *"Add a skill for video-effects-studio to handle automated color lut extraction"*

The agent will use `ai-brain-manager` to:
1. Validate that `video-effects-studio` is an active project.
2. Create the skill package inside `../ai-brain/skills/projects/video-effects-studio/<skill-name>/`.
3. (Optional) Add a manifest entry in the brain only if it needs a custom summary or should start disabled.
4. Run `python3 scripts/ai_brain.py`.
5. Instantly provide the skill to Antigravity, Claude, and ChatGPT.

### Method B: Manual Addition
1. Create the skill directory in `../ai-brain/skills/projects/video-effects-studio/<skill-name>/`.
2. Add `SKILL.md` with YAML frontmatter (`name`, `description`).
3. Nothing to register: any folder with a `SKILL.md` is discovered (use `skills-manifest.json` only to disable it or set a summary).
4. Run `python3 scripts/ai_brain.py`.

---

## 4. Visual DevBar in Dashboard & Review Studio

When running the local dashboard or review studio (`npm start` or `npm run dashboard` on port `4173`), the **Universal AI DevBar** is automatically loaded at the bottom-right of the screen (`review.html` and `index.html`).

- Click the pill `🧠 AI Brain` to open the control drawer.
- Toggle active skills ON/OFF instantly.
- Jump to the Standalone Console (`:4999`) or Faceless Shorts (`:8765`).
- View and update session notes from `STATE.md`.
