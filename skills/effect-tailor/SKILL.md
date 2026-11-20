---
name: effect-tailor
description: Analyzes scene speech, visual context, and creator branding to author meaningful, tailored effect parameters (text, metrics, labels, kinetic words, and options) for all 54+ studio effects, eliminating generic template placeholders.
---

# Semantic Effect Tailoring

Whenever a visual effect is recommended, chosen, or edited for a video shot, do NOT use empty options `{}` or default generic template strings (such as "Claude", "38", "Vibha", or random placeholder metrics).

Analyze the scene dialogue, timing, topic, and creator branding to author meaningful, punchy parameters that reinforce what the creator is actually saying.

## Core Rules

1. **Extract Real Speech & Metrics**:
   - Extract actual numbers mentioned (years, counts, percentages, dollar amounts, benchmarks).
   - Extract core technical nouns and actions (e.g. "Mobile Apps", "Architecture", "AI Systems", "Build").
   - Never use placeholder sample data when the creator has real speech in that frame.

2. **Respect Creator Branding**:
   - Creator name: `Nayan` (or from `settings.json` / `plan.json`).
   - Channel name: `Techno Ravan`.
   - Social handle: `@TechnoRavan`.
   - Visual tone: Developer Dark, pragmatic, high developer empathy, zero fluff.

3. **Zero Em Dashes**:
   - Never author em dashes in effect labels, pills, or overlays. Use middle dots `·`, hyphens `-`, slashes `/`, or vertical bars `|` as separators.

## Option Schemas by Effect Type

### 1. Stats and Glass Widgets (`#23 glass-widgets`)
- `title`: Domain or category (e.g. `Experience`, `Architecture`, `Systems`).
- `text`: Primary numeric metric (e.g. `10+`, `50+`, `100%`).
- `sub`: Pipe-separated sub-bullets (e.g. `Years|Mobile Apps`, `iOS|Android`).
- `name`: Real creator name (`Nayan`).
- `handle`: Real handle (`@TechnoRavan`).
- `label`: Progress/architecture headline (e.g. `Mobile Architecture`, `System Design`).
- `card_title`: Artifact card headline (e.g. `Production Apps`).
- `card_stat`: Artifact stat badge (e.g. `10 YRS`).
- `event`: Contextual event pill (e.g. `50+ Production Apps · iOS & Android`).
- `day` / `date`: Key milestone label and number (e.g. `EXP`, `10`).

### 2. Kinetic Headlines & Collages (`#24 red-collage`, `#25 split-headline`, `#6 backdrop-word`)
- `red-collage`:
  - `text`: Core theme noun (e.g. `MOBILE`, `SYSTEMS`, `CODE`).
  - `lines`: Pipe-separated 3 punchy claims (e.g. `10 YEARS.|PRODUCTION APPS.|REAL ARCHITECTURE.`).
- `split-headline`:
  - `text`: Two-line headline matching dialogue (e.g. `10 Years Building|Mobile Apps`).
  - `hl`: The specific keyword to highlight in accent colour (e.g. `Mobile`).
- `backdrop-word`:
  - `text`: Single bold technical noun placed behind the head (e.g. `MOBILE`, `SCALE`, `BUILD`).

### 3. Spotlights and Focus Labels (`#46 tape-label` / `spotlight`)
- `text`: Short high-impact hook or callout (e.g. `10 YEARS EXP`, `SYSTEM ARCHITECTURE`).

### 4. Lists, Checklists, and Billboards (`#2 lineup`, `#11 todo`, `#36 checklist`, `#27 check-pills`)
- Pipe-separated items matching the scene progression (e.g. `iOS|Android|Architecture`, `Design::done|Code::done|Ship::next`).

## Automated Helper Integration

The studio bundles `scripts/effect_tailor.py` which automatically derives tailored parameters from:
```bash
python scripts/effect_tailor.py
```
Both the dashboard (`scripts/dashboard.mjs`) and planning workflows (`scripts/reel_workflow.py`) use this helper whenever an effect is selected or suggested.
