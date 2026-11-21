---
name: safe-area
description: Enforce platform-specific (Instagram Reels, YouTube Shorts, TikTok) and universal safe areas across all portrait reel previews and renders, preventing text, captions and graphics from colliding with platform UI overlays.
---

# Safe Area System & UI Overlay Guidelines

This skill defines the technical boundaries, layout constraints, and preview validation rules for all 9:16 portrait vertical reels and short-form videos across **Instagram Reels, YouTube Shorts, and TikTok**.

Resolve the studio root two directories above this skill. This skill applies automatically to **every reel we generate**, from planning and text layout to preview frames and final rendering.

---

## 1. Why Safe Areas Matter

Short-form video platforms superimpose native user interface elements directly over video playback. When content is not contained within verified safe zones, viewers experience:

- **Action rail collision**: Like, comment, share, remix, and sound disc buttons on the right edge obscure right-aligned text or ends of lines.
- **Top header collision**: Search bars, back arrows, Following/For You tabs, and audio pills cut through hooks and titles.
- **Bottom UI collision**: Creator handles, subscribe buttons, multi-line native captions, sound tickers, and home navigation bars bury spoken subtitles.
- **Profile grid clipping**: On Instagram profile grids, only the center 1:1 square (1080×1080) is visible; off-center headlines are cropped out in feed views.

---

## 2. Platform Safe Zones (1080×1920 Reference Canvas)

All vertical reels are authored for a 1080×1920 base canvas (or proportional 4K UHD 2160×3840).

| Platform | Top Restricted | Bottom Restricted | Left Margin | Right Restricted (Action Rail) | Usable Content Box | Primary UI Elements to Avoid |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Universal (Default)** | **290 px** (~15%) | **440 px** (~23%) | **70 px** (~6.5%) | **160 px** (~15%) | **850 × 1190 px** | Guaranteed intersection clear on all 3 apps. |
| **Instagram Reels** | **220 px** (~11.5%) | **380 px** (~20%) | **60 px** (~5.5%) | **130 px** (~12%) | **890 × 1320 px** | Top audio bar, right actions, handle & caption text. |
| **TikTok** | **240 px** (~12.5%) | **440 px** (~23%) | **60 px** (~5.5%) | **150 px** (~14%) | **870 × 1240 px** | Following/For You tabs, right avatar/rail, heavy captions. |
| **YouTube Shorts** | **280 px** (~14.5%) | **400 px** (~21%) | **60 px** (~5.5%) | **160 px** (~15%) | **860 × 1240 px** | Top search/camera, right thumbs/share rail, subscribe pill. |
| **Instagram 1:1 Profile Crop** | **420 px** (top) | **420 px** (bottom) | — | — | **1080 × 1080 px** | Centered square visible on Instagram profile tab. |

---

## 3. Core Positioning Rules for Every Reel

### A. Spoken Captions
1. **Bottom-Anchored Growth**:
   - Captions must be anchored from the **bottom** (`bottom: 460px` on 1080×1920) rather than a fixed top offset.
   - This ensures that 1-line, 2-line, and 3-line captions grow **upwards** into the open safe zone, never down into platform metadata.
2. **Right Action Rail Clearance**:
   - Captions must stop at `width: 825px` with `left: 80px`, leaving at least **175 px** clear on the right edge.
   - Text must never touch or run beneath the Like, Comment, and Share vertical column.
3. **Typography**:
   - Use bold sans-serif (StudioInter 800), line-height 1.15, balanced text-wrapping, with dark stroke and shadow for contrast over any background.

### B. Headlines & Hooks
1. **Top Header Clearance**:
   - Top hook headlines must start at or below `top: 300px` (or 16% of height).
   - Never place titles at `top: 10%` (which enters the top search/navigation bar).
2. **Horizontal Width**:
   - Center headlines within `width: 825px` and `left: 80px`.
   - In Instagram profile view, ensure the primary hook is centered within the 1080×1080 center zone (`y: 420` to `1500`).

### C. Visual Elements, Cards & Text Overlays
1. **Text Layers**:
   - Use `scripts/safe_area.py` to validate all custom text layers and graphic cards.
   - Normalized `x` must be between `0.07` and `0.78`.
   - Normalized `y` must be between `0.16` and `0.75`.
2. **Demo Screenshots & Diagrams**:
   - When showcasing code editors, terminals, or architecture diagrams, scale the media to fit within the `850×1190` safe area so essential lines are not covered by buttons.

---

## 4. Interactive Review & Preview Verification

Before rendering any video, verify framing using the studio review tools:

1. **Review Dashboard Toolbar** (`/review/reels/<slug>`):
   - In Step 2 (Final Plan & Preview Frames), use the **Safe Area Toolbar**:
     - **Universal**: Default cross-platform view.
     - **Instagram Reels**: Simulates Instagram controls and 1:1 profile crop.
     - **TikTok**: Simulates TikTok action rail, tabs, and bottom sound pill.
     - **YouTube Shorts**: Simulates Shorts header, subscribe button, and thumbs stack.
     - **Off**: Clean unobstructed video frame view.
   - Toggles:
     - **Guides**: Renders green safe boundary box with red/amber danger zones.
     - **Simulate UI**: Overlays realistic platform controls with SVG icons and counts.
     - **1:1 Grid**: Displays Instagram profile feed crop boundary.
2. **Validation Status**:
   - Each scene preview frame displays a `✓ Safe Area` badge confirming placement.
   - If an element crosses into the danger zone, an alert badge highlights the overflow.

---

## 5. Technical Integration & Commands

- **Calculate safe bounds in Python**:
  ```python
  from safe_area import get_safe_area, caption_bounds, headline_bounds, validate_box

  # Get universal safe zone for 1080x1920
  safe = get_safe_area('universal', 1080, 1920)

  # Get caption bounds
  cb = caption_bounds('universal', 1080, 1920)
  # cb['bottom'] -> 460, cb['left'] -> 80, cb['width'] -> 825

  # Validate bounding box
  result = validate_box({'x': 100, 'y': 1500, 'w': 500, 'h': 100}, 'universal')
  if not result['valid']:
      print("Danger zone violation:", result['violations'])
  ```

- **Inspect safe area via CLI**:
  ```bash
  python scripts/safe_area.py --platform universal --caption
  python scripts/safe_area.py --platform instagram
  python scripts/safe_area.py --platform tiktok
  python scripts/safe_area.py --platform youtube_shorts
  ```
