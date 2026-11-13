# Local effect options used in the introduction reel

These additions live in `skills/effects/scripts/fx.py`; the upstream defaults remain available. Captions, transitions, music and final assembly belong to Hyperframes.

| Effect | Extra options | Purpose |
| --- | --- | --- |
| #35 headline-wall | `images`, `layout: "tools"`, `show_total: false` | Display supplied logo cards in a safe 2×2 layout without a sample views counter. |
| #28 timeline | `color`, `tc_start`, `status_cues: [{at, label, color}]` | Switch title and timeline colour at local shot times. Titles fit the frame; `tc_start` sets the project clock. |
| #51 fan-build | `fit_frame: true` | Keep the rotating cards inside the frame. |
| #24 red-collage | `word_width: 0.90`, `hold_end: true` | Fit a large word and hold the final treatment through the last frame. |
| #33 phone-fan | `headline_style: "experience"` | Bordered dark headline with “ABOUT 10 YEARS / IN MOBILE APPS”; leave captions off separately. |
| #35 headline-wall | `layout: "icons"`, `images`, `gap` | Pop up to seven supplied original PNG app icons without added cards or labels. Transparency is retained. |
| #23 glass-widgets | `layout: "projects"` | Three glass artifacts for projects, build progress and learning, without sample view counts or creator branding. |
| #41 led-sign | `head_gap` | Raise the sign above the face; default remains 0.75. |
| #7 spotlight | `font`, `font_size`, `word_width`, `title_y`, `glow: 0` | Place a sharp upright title above the head. |
| B1 glitter-spotlight | `font`, `gradient_end`, `word_glow`, `sparkles` | Restyle the name in bold monospace with restrained highlights. |
| #24 red-collage | `glow: 0`, `color`, `stroke`, `stroke_color`, `shadow`, `font` | Remove bloom and retain a clear title edge. |

For stateful still previews, `--warmup` replays earlier frames before the sampled moment. The reel's editable plan and build scripts are in `outputs/reels/meet-nayan-building-with-ai/`. Mobile UIs are illustrative concepts; tool icons come from the installed original apps, with provenance in the project's `assets/logos/sources.json`.
