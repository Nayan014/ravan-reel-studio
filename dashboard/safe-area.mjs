// Platform-specific and universal safe area guidelines, simulated UI, and overlay renderer
// for Instagram Reels, YouTube Shorts, and TikTok.

export const BASE_CANVAS = { width: 1080, height: 1920 };

export const PLATFORMS = {
  universal: {
    id: 'universal',
    name: 'Universal Safe Area',
    shortName: 'Universal',
    badge: 'Cross-Platform',
    accentColor: '#10b981',
    description: 'Guaranteed safe on Instagram Reels, TikTok, and YouTube Shorts.',
    top: 290,
    bottom: 440,
    left: 70,
    right: 160,
    showProfileGrid: true,
  },
  instagram: {
    id: 'instagram',
    name: 'Instagram Reels',
    shortName: 'Instagram',
    badge: 'IG Reels',
    accentColor: '#e1306c',
    description: 'Optimized for Instagram: protects top audio bar, right engagement rail, and bottom handle/captions.',
    top: 220,
    bottom: 380,
    left: 60,
    right: 130,
    showProfileGrid: true,
  },
  tiktok: {
    id: 'tiktok',
    name: 'TikTok',
    shortName: 'TikTok',
    badge: 'TikTok',
    accentColor: '#00f2fe',
    description: 'Optimized for TikTok: protects Following/For You tabs, right vertical actions, and heavy bottom caption/sound area.',
    top: 240,
    bottom: 440,
    left: 60,
    right: 150,
    showProfileGrid: false,
  },
  youtube: {
    id: 'youtube',
    name: 'YouTube Shorts',
    shortName: 'YT Shorts',
    badge: 'Shorts',
    accentColor: '#ff0000',
    description: 'Optimized for YouTube Shorts: protects top search/create, right thumbs/share rail, and bottom subscribe/title pill.',
    top: 280,
    bottom: 400,
    left: 60,
    right: 160,
    showProfileGrid: false,
  },
  off: {
    id: 'off',
    name: 'Off (Clean View)',
    shortName: 'Off',
    badge: 'Raw Frame',
    accentColor: '#94a3b8',
    description: 'Displays the raw frame without overlays or simulated UI.',
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
    showProfileGrid: false,
  }
};

/**
 * Calculate safe area coordinates and percentages for a given canvas.
 */
export function getSafeArea(platformKey = 'universal', width = BASE_CANVAS.width, height = BASE_CANVAS.height) {
  const key = (platformKey || 'universal').toLowerCase();
  const spec = PLATFORMS[key] || PLATFORMS.universal;
  if (key === 'off') {
    return {
      platform: 'off',
      width,
      height,
      topPx: 0,
      bottomPx: 0,
      leftPx: 0,
      rightPx: 0,
      topPct: 0,
      bottomPct: 0,
      leftPct: 0,
      rightPct: 0,
      safeWidthPct: 100,
      safeHeightPct: 100,
    };
  }

  const scaleX = width / BASE_CANVAS.width;
  const scaleY = height / BASE_CANVAS.height;

  const topPx = Math.round(spec.top * scaleY);
  const bottomPx = Math.round(spec.bottom * scaleY);
  const leftPx = Math.round(spec.left * scaleX);
  const rightPx = Math.round(spec.right * scaleX);

  const safeWidthPx = Math.max(1, width - leftPx - rightPx);
  const safeHeightPx = Math.max(1, height - topPx - bottomPx);

  return {
    platform: spec.id,
    spec,
    width,
    height,
    topPx,
    bottomPx,
    leftPx,
    rightPx,
    safeWidthPx,
    safeHeightPx,
    safeXMaxPx: width - rightPx,
    safeYMaxPx: height - bottomPx,
    // Percentages for CSS positioning
    topPct: (topPx / height) * 100,
    bottomPct: (bottomPx / height) * 100,
    leftPct: (leftPx / width) * 100,
    rightPct: (rightPx / width) * 100,
    safeWidthPct: (safeWidthPx / width) * 100,
    safeHeightPct: (safeHeightPx / height) * 100,
    // Instagram 1:1 Profile Grid Crop (Center square on profile feed)
    profileGridTopPct: ((420 * scaleY) / height) * 100,
    profileGridHeightPct: ((1080 * scaleY) / height) * 100,
  };
}

/**
 * Render platform-specific SVG icons for UI simulation.
 */
function svgIcons() {
  return {
    heart: `<svg viewBox="0 0 24 24" width="28" height="28" fill="white" stroke="white" stroke-width="1.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`,
    comment: `<svg viewBox="0 0 24 24" width="28" height="28" fill="white" stroke="white" stroke-width="1.5"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>`,
    share: `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`,
    bookmark: `<svg viewBox="0 0 24 24" width="28" height="28" fill="white" stroke="white" stroke-width="1.5"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>`,
    more: `<svg viewBox="0 0 24 24" width="24" height="24" fill="white"><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/><circle cx="5" cy="12" r="2"/></svg>`,
    music: `<svg viewBox="0 0 24 24" width="16" height="16" fill="white"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>`,
    search: `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
    camera: `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>`,
    thumbsUp: `<svg viewBox="0 0 24 24" width="28" height="28" fill="white"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>`,
    thumbsDown: `<svg viewBox="0 0 24 24" width="28" height="28" fill="white"><path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/></svg>`,
    remix: `<svg viewBox="0 0 24 24" width="26" height="26" fill="white"><path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/></svg>`,
  };
}

/**
 * Generate simulated UI markup for a specific platform.
 */
export function renderSimulatedUI(platform = 'universal', channelName = 'Techno Ravan') {
  const key = (platform || 'universal').toLowerCase();
  if (key === 'off') return '';

  const icons = svgIcons();
  const safeName = channelName || 'Techno Ravan';
  const handle = safeName.toLowerCase().replace(/[^a-z0-9_]/g, '');

  if (key === 'instagram') {
    return `
      <div class="safe-sim-ui sim-instagram" aria-hidden="true">
        <!-- Top header -->
        <div class="sim-header-ig">
          <span class="sim-logo">Reels</span>
          <div class="sim-header-icons">${icons.camera}</div>
        </div>
        <!-- Right Action Rail -->
        <div class="sim-action-rail-ig">
          <div class="sim-action-btn">${icons.heart}<span>142K</span></div>
          <div class="sim-action-btn">${icons.comment}<span>1,842</span></div>
          <div class="sim-action-btn">${icons.share}<span>24.5K</span></div>
          <div class="sim-action-btn">${icons.more}</div>
          <div class="sim-vinyl-ig"><div class="sim-vinyl-inner"></div></div>
        </div>
        <!-- Bottom metadata -->
        <div class="sim-bottom-ig">
          <div class="sim-creator-row">
            <div class="sim-avatar"></div>
            <strong class="sim-handle">@${handle}</strong>
            <button class="sim-follow-btn" type="button">Follow</button>
          </div>
          <p class="sim-caption">Developer workflow tutorial · Tap to expand full caption</p>
          <div class="sim-sound-row">${icons.music}<span>${safeName} · Original audio</span></div>
        </div>
      </div>
    `;
  }

  if (key === 'tiktok') {
    return `
      <div class="safe-sim-ui sim-tiktok" aria-hidden="true">
        <!-- Top header -->
        <div class="sim-header-tt">
          <span class="sim-live-badge">LIVE</span>
          <div class="sim-tabs"><span class="sim-tab">Following</span><span class="sim-tab active">For You</span></div>
          <span class="sim-search-icon">${icons.search}</span>
        </div>
        <!-- Right Action Rail -->
        <div class="sim-action-rail-tt">
          <div class="sim-tt-avatar-wrap">
            <div class="sim-avatar"></div>
            <span class="sim-avatar-plus">+</span>
          </div>
          <div class="sim-action-btn">${icons.heart}<span>248.6K</span></div>
          <div class="sim-action-btn">${icons.comment}<span>3,190</span></div>
          <div class="sim-action-btn">${icons.bookmark}<span>41.2K</span></div>
          <div class="sim-action-btn">${icons.share}<span>18.9K</span></div>
          <div class="sim-vinyl-disc"><div class="sim-vinyl-needle"></div></div>
        </div>
        <!-- Bottom metadata -->
        <div class="sim-bottom-tt">
          <strong class="sim-handle">@${handle}</strong>
          <p class="sim-caption">Full-stack system architecture in 60s #developer #ai</p>
          <div class="sim-sound-pill">${icons.music}<span>♫ ${safeName} - Original Studio Sound</span></div>
        </div>
      </div>
    `;
  }

  if (key === 'youtube') {
    return `
      <div class="safe-sim-ui sim-youtube" aria-hidden="true">
        <!-- Top header -->
        <div class="sim-header-yt">
          <span class="sim-back-arrow">←</span>
          <div class="sim-yt-top-right">${icons.search}${icons.camera}${icons.more}</div>
        </div>
        <!-- Right Action Rail -->
        <div class="sim-action-rail-yt">
          <div class="sim-action-btn">${icons.thumbsUp}<span>94K</span></div>
          <div class="sim-action-btn">${icons.thumbsDown}<span>Dislike</span></div>
          <div class="sim-action-btn">${icons.comment}<span>1,120</span></div>
          <div class="sim-action-btn">${icons.share}<span>Share</span></div>
          <div class="sim-action-btn">${icons.remix}<span>Remix</span></div>
          <div class="sim-yt-audio-square"><div class="sim-yt-sound-wave"></div></div>
        </div>
        <!-- Bottom metadata -->
        <div class="sim-bottom-yt">
          <div class="sim-creator-row">
            <div class="sim-avatar"></div>
            <strong class="sim-handle">@${safeName}</strong>
            <button class="sim-yt-subscribe-btn" type="button">Subscribe</button>
          </div>
          <p class="sim-caption">Developer tutorial and clean engineering patterns</p>
          <div class="sim-yt-sound-pill">${icons.music}<span>${safeName} · Sound</span></div>
        </div>
      </div>
    `;
  }

  // Universal composite view: indicates the shared collision zones for all 3 apps
  return `
    <div class="safe-sim-ui sim-universal" aria-hidden="true">
      <div class="sim-header-uni">
        <span class="sim-uni-tag">TOP UI ZONE (290px)</span>
        <span class="sim-uni-sub">Search · Audio · Navigation · Tabs</span>
      </div>
      <div class="sim-action-rail-uni">
        <div class="sim-uni-rail-tag">ACTION RAIL<br>(160px)<br><small>Likes · Comments · Shares · Remix</small></div>
      </div>
      <div class="sim-bottom-uni">
        <span class="sim-uni-tag">BOTTOM UI ZONE (440px)</span>
        <span class="sim-uni-sub">Creator Handle · Full Spoken Captions · Audio Ticker · Controls</span>
      </div>
    </div>
  `;
}

/**
 * Generate the safe area boundary lines, danger zone shading and markers.
 */
export function renderSafeAreaGuides(platform = 'universal', showGuides = true, showProfileGrid = false) {
  const key = (platform || 'universal').toLowerCase();
  if (key === 'off' || !showGuides) return '';

  const sa = getSafeArea(key);
  const spec = sa.spec;

  const profileGridHtml = (showProfileGrid && sa.profileGridTopPct) ? `
    <div class="safe-profile-grid-crop" style="top:${sa.profileGridTopPct}%;height:${sa.profileGridHeightPct}%" title="Instagram 1:1 Profile Grid Crop (Center Square)">
      <span class="safe-grid-label">1:1 Profile Grid Center Crop</span>
    </div>
  ` : '';

  return `
    <div class="safe-guides-layer" style="--safe-color:${spec.accentColor}" aria-hidden="true">
      <!-- Top restricted zone -->
      <div class="safe-danger-zone top-zone" style="height:${sa.topPct}%">
        <span class="zone-label">⚠️ Top UI Danger Zone (${sa.topPx}px)</span>
      </div>
      <!-- Bottom restricted zone -->
      <div class="safe-danger-zone bottom-zone" style="height:${sa.bottomPct}%">
        <span class="zone-label">⚠️ Bottom UI Danger Zone (${sa.bottomPx}px)</span>
      </div>
      <!-- Right action rail restricted zone -->
      <div class="safe-danger-zone right-zone" style="top:${sa.topPct}%;bottom:${sa.bottomPct}%;width:${sa.rightPct}%">
        <span class="zone-label vertical">⚠️ Action Rail (${sa.rightPx}px)</span>
      </div>
      <!-- Safe Content Box -->
      <div class="safe-content-box" style="top:${sa.topPct}%;bottom:${sa.bottomPct}%;left:${sa.leftPct}%;right:${sa.rightPct}%">
        <span class="safe-box-tag">${spec.shortName} Safe Area (${sa.safeWidthPx}×${sa.safeHeightPx}px)</span>
        <div class="corner-bracket tl"></div>
        <div class="corner-bracket tr"></div>
        <div class="corner-bracket bl"></div>
        <div class="corner-bracket br"></div>
      </div>
      ${profileGridHtml}
    </div>
  `;
}

/**
 * Renders the complete safe area control bar HTML for review pages and dashboard.
 */
export function renderSafeAreaToolbar(currentPlatform = 'universal', options = {}) {
  const { showGuides = true, showSimUi = true, showProfileGrid = false, isVideo = false } = options;
  const platformButtons = Object.values(PLATFORMS).map(p => {
    const active = p.id === currentPlatform ? 'active' : '';
    return `<button type="button" class="safe-platform-btn ${active}" data-platform="${p.id}" title="${p.description}">${p.badge || p.shortName}</button>`;
  }).join('');

  return `
    <div class="safe-area-toolbar" role="toolbar" aria-label="Safe Area Controls">
      <div class="safe-toolbar-group platforms-group">
        <span class="safe-toolbar-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg> Safe Area:</span>
        <div class="safe-btn-cluster">${platformButtons}</div>
      </div>
      <div class="safe-toolbar-group toggles-group">
        <label class="safe-toggle-item" title="Toggle visible boundary lines and danger zones">
          <input type="checkbox" id="safe-toggle-guides" ${showGuides ? 'checked' : ''}>
          <span>Guides</span>
        </label>
        <label class="safe-toggle-item" title="Simulate realistic native platform UI elements">
          <input type="checkbox" id="safe-toggle-ui" ${showSimUi ? 'checked' : ''}>
          <span>Simulate UI</span>
        </label>
        <label class="safe-toggle-item" title="Show Instagram 1:1 Profile Feed crop box">
          <input type="checkbox" id="safe-toggle-grid" ${showProfileGrid ? 'checked' : ''}>
          <span>1:1 Grid</span>
        </label>
      </div>
      <div class="safe-toolbar-info">
        <span id="safe-status-pill" class="safe-status-pill ${currentPlatform !== 'off' ? 'active' : ''}">
          ${PLATFORMS[currentPlatform]?.shortName || 'Universal'} Safe Zone
        </span>
      </div>
    </div>
  `;
}

/**
 * Validate a bounding box (normalized or pixel) against the safe area.
 */
export function validateBox(box, platform = 'universal', width = BASE_CANVAS.width, height = BASE_CANVAS.height) {
  const sa = getSafeArea(platform, width, height);
  if (sa.platform === 'off') {
    return { valid: true, violations: [] };
  }

  let { x, y, width: bw, height: bh } = box;
  // If normalized (all <= 1.0)
  if (x <= 1.0 && y <= 1.0 && bw <= 1.0 && bh <= 1.0) {
    x *= width;
    y *= height;
    bw *= width;
    bh *= height;
  }

  const violations = [];
  if (y < sa.topPx) violations.push(`Top overflow: ${(sa.topPx - y).toFixed(0)}px into top header`);
  if (y + bh > sa.safeYMaxPx) violations.push(`Bottom overflow: ${(y + bh - sa.safeYMaxPx).toFixed(0)}px into bottom UI/captions`);
  if (x < sa.leftPx) violations.push(`Left overflow: ${(sa.leftPx - x).toFixed(0)}px past left edge`);
  if (x + bw > sa.safeXMaxPx) violations.push(`Right overflow: ${(x + bw - sa.safeXMaxPx).toFixed(0)}px into action rail`);

  return {
    valid: violations.length === 0,
    platform: sa.platform,
    violations,
    clamped: {
      x: Math.max(sa.leftPx, Math.min(x, sa.safeXMaxPx - bw)),
      y: Math.max(sa.topPx, Math.min(y, sa.safeYMaxPx - bh)),
      width: Math.min(bw, sa.safeWidthPx),
      height: Math.min(bh, sa.safeHeightPx),
    }
  };
}
