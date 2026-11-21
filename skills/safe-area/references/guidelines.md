# Platform-Specific Safe Area Guidelines & UI Layout Research

This reference documents the UI overlay measurements, interaction zones, and layout best practices for vertical video across **Instagram Reels, TikTok, and YouTube Shorts**.

---

## 1. Research & Platform UI Breakdown

All three major vertical video platforms use a **9:16 aspect ratio** (typically 1080×1920 pixels or 2160×3840 4K). However, each platform places native navigation, social interaction, and audio attribution chrome in distinct screen regions.

### A. Instagram Reels
- **Top Overlay (~220 px)**:
  - Header with "Reels" logo, back navigation, audio tag, and camera/settings icons.
  - Sponsored tags or branded content disclosures appear directly below the header.
- **Right Engagement Rail (~130 px wide, from y ≈ 1100 to y ≈ 1800)**:
  - Vertically stacked buttons:
    1. Like icon (Heart) + like counter
    2. Comment bubble + comment counter
    3. Paper airplane (Share / DM) + share counter
    4. Three dots menu (Remix, Save, QR code)
    5. Rotating audio album cover square (bottom right)
- **Bottom Metadata (~380 px)**:
  - Account profile picture and handle (`@creator`), followed by a "Follow" button.
  - Multi-line caption preview with "more" expand trigger.
  - Audio track scrolling ticker with music note icon.
- **Profile Feed 1:1 Grid**:
  - When viewed on a creator's profile page, Instagram crops the 9:16 reel to a centered 1:1 square:
  - `top: 420px`, `bottom: 420px`, `height: 1080px`.
  - Content placed in the top 420px or bottom 420px is cut off in grid preview thumbnails.

### B. TikTok
- **Top Overlay (~240 px)**:
  - "Following | For You" dual-tab navigation centered at top.
  - LIVE icon on the top-left; search icon on the top-right.
- **Right Engagement Stack (~150 px wide, from y ≈ 950 to y ≈ 1800)**:
  - Vertically stacked buttons:
    1. Creator profile circle with red "+" follow badge.
    2. Heart icon + like counter.
    3. Comment bubble + comment counter.
    4. Bookmark/Favorites star icon + save counter.
    5. Share arrow + share counter.
    6. Rotating vinyl record disc with musical note animation.
- **Bottom Metadata (~440 px)**:
  - TikTok has the heaviest bottom footprint among all platforms:
  - Creator username (`@creator`).
  - Multi-line caption with clickable hashtags (`#coding`, `#ai`).
  - Search suggestion pill (TikTok auto-adds a search query pill above the caption).
  - Sound marquee with disc animation.
  - Native bottom tab bar (Home, Friends, Create, Inbox, Profile).

### C. YouTube Shorts
- **Top Overlay (~280 px)**:
  - Back arrow (left), Search magnifying glass, Camera/create icon, and 3-dots menu (right).
- **Right Engagement Column (~160 px wide, from y ≈ 1000 to y ≈ 1800)**:
  - Vertically stacked buttons:
    1. Thumbs Up (Like) + count.
    2. Thumbs Down (Dislike).
    3. Comments bubble + count.
    4. Share arrow.
    5. Remix button with scissors icon.
    6. Audio square thumbnail with sound wave animation.
- **Bottom Metadata (~400 px)**:
  - Channel avatar + `@ChannelName` + prominent red "Subscribe" pill button.
  - Video title and description text.
  - Sound remix pill button.
  - Video scrubber / progress bar along the very bottom edge.

---

## 2. The Universal Cross-Platform Safe Zone

When distributing one master video across all three platforms, use the **Universal Safe Zone**:

- **Top Margin**: **290 px** (clear of Shorts header and TikTok tabs)
- **Bottom Margin**: **440 px** (clear of TikTok multi-line captions and bottom controls)
- **Left Margin**: **70 px** (clean margin from phone bezel)
- **Right Margin**: **160 px** (clear of Shorts and TikTok vertical action buttons)
- **Usable Canvas**: **850 × 1190 px** centered between x: 70 and x: 920, y: 290 and y: 1480.

---

## 3. Implementation Rules

1. **Captions**:
   - Always place captions with `bottom: 460px` and `left: 80px`, `width: 825px`.
   - Never use `top: 76%` with `width: 84%` which overflows into the right action rail and bottom captions.
2. **Headlines**:
   - Always start headlines below `top: 300px` with `left: 80px`, `width: 825px`.
3. **Graphics & Product Demos**:
   - Code blocks, architecture diagrams, and software demos must fit inside `850×1190`.
4. **Interactive Verification**:
   - Always use the interactive review dashboard toolbar to preview with simulated UI before approving release exports.
