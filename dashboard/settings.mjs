// Studio Creator Profile & Theme Management
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

export function applyTheme(theme) {
  let effective = theme;
  if (!theme || theme === 'system') {
    effective = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  document.documentElement.setAttribute('data-theme', effective);
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.textContent = effective === 'dark' ? '☀️' : '🌙';
    toggleBtn.title = effective === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    toggleBtn.setAttribute('aria-label', toggleBtn.title);
  }
}

export function initTheme() {
  const saved = localStorage.getItem('techno-reel-theme') || 'system';
  applyTheme(saved);

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const current = localStorage.getItem('techno-reel-theme') || 'system';
    if (current === 'system') applyTheme('system');
  });

  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem('techno-reel-theme', next);
      applyTheme(next);
    });
  }
}

const SETTINGS_MODAL_HTML = `
  <div class="settings-modal-wrapper">
    <div class="settings-modal-header">
      <div>
        <h2 class="settings-modal-title">Studio Settings</h2>
        <p class="settings-modal-subtitle">Creator profile and defaults for new reels and YouTube plans</p>
      </div>
      <button type="button" id="close-settings-x" class="settings-close-x" aria-label="Close dialog">&times;</button>
    </div>
    <form id="settings-form" class="settings-form">
      <div class="settings-tabs-nav" role="tablist">
        <button type="button" class="settings-tab active" data-tab="profile" role="tab" aria-selected="true">Channel Profile</button>
        <button type="button" class="settings-tab" data-tab="video" role="tab" aria-selected="false">Video & Visuals</button>
        <button type="button" class="settings-tab" data-tab="script" role="tab" aria-selected="false">Script & Tone</button>
        <button type="button" class="settings-tab" data-tab="audio" role="tab" aria-selected="false">Audio & Sound</button>
        <button type="button" class="settings-tab" data-tab="appearance" role="tab" aria-selected="false">Appearance</button>
      </div>

      <div class="settings-tab-content active" id="tab-profile" role="tabpanel">
        <div class="settings-grid">
          <div class="form-group">
            <label for="set-channelName">Channel name</label>
            <input type="text" id="set-channelName" name="channelName" placeholder="e.g. Techno Ravan">
            <small>Used in plan headers, covers, and review watermarks.</small>
          </div>
          <div class="form-group">
            <label for="set-creatorName">Creator name</label>
            <input type="text" id="set-creatorName" name="creatorName" placeholder="e.g. Nayan">
            <small>Your name or handle for host attribution.</small>
          </div>
          <div class="form-group">
            <label for="set-youtubeHandle">YouTube handle</label>
            <input type="text" id="set-youtubeHandle" name="youtubeHandle" placeholder="e.g. @TechnoRavan">
          </div>
          <div class="form-group">
            <label for="set-instagramHandle">Instagram handle</label>
            <input type="text" id="set-instagramHandle" name="instagramHandle" placeholder="e.g. @technoravan">
          </div>
          <div class="form-group full-width">
            <label for="set-linkedinUrl">LinkedIn profile URL</label>
            <input type="url" id="set-linkedinUrl" name="linkedinUrl" placeholder="https://www.linkedin.com/in/...">
          </div>
          <div class="form-group full-width">
            <label for="set-niche">Niche / Content focus</label>
            <input type="text" id="set-niche" name="niche" placeholder="Developer Tutorials, AI Engineering, Full-Stack Architecture">
            <small>Informs AI script hooks and recommended technical vocabulary.</small>
          </div>
          <div class="form-group full-width">
            <label for="set-targetAudience">Target audience</label>
            <input type="text" id="set-targetAudience" name="targetAudience" placeholder="Developers, Software Engineers, AI Builders">
          </div>
          <div class="form-group full-width">
            <label for="set-bio">Short bio / channel description</label>
            <textarea id="set-bio" name="bio" rows="2" placeholder="Bite-sized developer workflows, AI systems, and modern software engineering."></textarea>
          </div>
        </div>
      </div>

      <div class="settings-tab-content" id="tab-video" role="tabpanel" hidden>
        <div class="settings-grid">
          <div class="form-group">
            <label for="set-primaryRatio">Primary aspect ratio</label>
            <select id="set-primaryRatio" name="primaryRatio">
              <option value="9:16 (Portrait Reel)">9:16 (Portrait Reel)</option>
              <option value="16:9 (Landscape YouTube)">16:9 (Landscape YouTube)</option>
            </select>
          </div>
          <div class="form-group">
            <label for="set-targetResolution">Target resolution</label>
            <select id="set-targetResolution" name="targetResolution">
              <option value="4K UHD (2160x3840)">4K UHD (2160x3840)</option>
              <option value="1080p FHD (1080x1920)">1080p FHD (1080x1920)</option>
            </select>
          </div>
          <div class="form-group">
            <label for="set-targetFps">Target frame rate</label>
            <select id="set-targetFps" name="targetFps">
              <option value="60">60 FPS</option>
              <option value="30">30 FPS</option>
            </select>
          </div>
          <div class="form-group">
            <label for="set-preferredEffectCategory">Preferred effects group</label>
            <select id="set-preferredEffectCategory" name="preferredEffectCategory">
              <option value="Techno Ravan Effects">Techno Ravan Effects</option>
              <option value="Vibha Effects">Vibha Effects</option>
            </select>
          </div>
          <div class="form-group full-width">
            <label for="set-aesthetic">Visual aesthetic</label>
            <input type="text" id="set-aesthetic" name="aesthetic" placeholder="Developer Dark (Deep Slate, Clean Accents, Terminal Highlighting)">
          </div>
        </div>
      </div>

      <div class="settings-tab-content" id="tab-script" role="tabpanel" hidden>
        <div class="settings-grid">
          <div class="form-group full-width">
            <label for="set-tone">Script tone</label>
            <input type="text" id="set-tone" name="tone" placeholder="Direct, punchy, pragmatic, high developer empathy, zero fluff">
          </div>
          <div class="form-group full-width">
            <label for="set-pacing">Pacing & hook formula</label>
            <input type="text" id="set-pacing" name="pacing" placeholder="Fast hook in 0-3s, rapid transitions every 3-5s, code/terminal proof first">
          </div>
          <div class="form-group full-width">
            <label for="set-callToAction">Default Call to Action (CTA)</label>
            <input type="text" id="set-callToAction" name="callToAction" placeholder="Follow @TechnoRavan for more developer systems">
          </div>
          <div class="form-group full-width checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" id="set-noEmDashes" name="noEmDashes" checked>
              <span>Strict zero em dash rule (prohibit em dashes in newly authored copy)</span>
            </label>
          </div>
        </div>
      </div>

      <div class="settings-tab-content" id="tab-audio" role="tabpanel" hidden>
        <div class="settings-grid">
          <div class="form-group full-width">
            <label for="set-defaultMusicMood">Default background music vibe</label>
            <input type="text" id="set-defaultMusicMood" name="defaultMusicMood" placeholder="Tech Minimal / Coding Focus">
          </div>
          <div class="form-group">
            <label for="set-voiceDucking">Voice ducking level</label>
            <input type="text" id="set-voiceDucking" name="voiceDucking" placeholder="-18 dB during dialogue">
          </div>
          <div class="form-group">
            <label for="set-sfxStyle">Sound effects style</label>
            <input type="text" id="set-sfxStyle" name="sfxStyle" placeholder="Subtle mechanical clicks, terminal beeps, soft risers">
          </div>
        </div>
      </div>

      <div class="settings-tab-content" id="tab-appearance" role="tabpanel" hidden>
        <div class="settings-grid">
          <div class="form-group full-width">
            <label for="set-theme">Dashboard theme preference</label>
            <select id="set-theme" name="theme">
              <option value="system">Follow System Setting</option>
              <option value="dark">Always Dark Mode</option>
              <option value="light">Always Light Mode</option>
            </select>
            <small>Can also be quickly toggled at any time using the ☀️/🌙 icon in the header.</small>
          </div>
        </div>
      </div>

      <div class="settings-modal-footer">
        <span id="settings-status" class="settings-status" role="status"></span>
        <div class="settings-footer-actions">
          <button type="button" class="button secondary" id="close-settings-btn">Cancel</button>
          <button type="submit" class="button" id="save-settings-btn">Save Settings</button>
        </div>
      </div>
    </form>
  </div>
`;

export function initSettingsModal() {
  const dialog = document.getElementById('settings-dialog');
  const openBtn = document.getElementById('open-settings-btn');
  if (!dialog || !openBtn) return;

  dialog.innerHTML = SETTINGS_MODAL_HTML;

  // Tab switching
  const tabs = dialog.querySelectorAll('.settings-tab');
  const panels = dialog.querySelectorAll('.settings-tab-content');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      panels.forEach(p => {
        p.classList.remove('active');
        p.hidden = true;
      });
      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');
      const targetPanel = dialog.querySelector(`#tab-${tab.dataset.tab}`);
      if (targetPanel) {
        targetPanel.classList.add('active');
        targetPanel.hidden = false;
      }
    });
  });

  const closeDialog = () => {
    if (dialog.open) dialog.close();
  };

  dialog.querySelector('#close-settings-x')?.addEventListener('click', closeDialog);
  dialog.querySelector('#close-settings-btn')?.addEventListener('click', closeDialog);

  // Close when clicking backdrop
  dialog.addEventListener('click', event => {
    if (event.target === dialog) closeDialog();
  });

  // Open & load settings
  openBtn.addEventListener('click', async () => {
    const status = dialog.querySelector('#settings-status');
    status.textContent = 'Loading settings…';
    status.className = 'settings-status';
    try {
      dialog.showModal();
      const res = await fetch('/api/settings');
      if (!res.ok) throw new Error('Could not load settings');
      const data = await res.json();
      status.textContent = '';

      // Populate form
      for (const [key, value] of Object.entries(data)) {
        const input = dialog.querySelector(`[name="${key}"]`);
        if (!input) continue;
        if (input.type === 'checkbox') {
          input.checked = Boolean(value);
        } else {
          input.value = value ?? '';
        }
      }
    } catch (err) {
      status.textContent = err.message;
      status.className = 'settings-status error';
    }
  });

  // Submit & save settings
  const form = dialog.querySelector('#settings-form');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const saveBtn = dialog.querySelector('#save-settings-btn');
    const status = dialog.querySelector('#settings-status');
    saveBtn.disabled = true;
    status.textContent = 'Saving settings…';
    status.className = 'settings-status';

    const formData = new FormData(form);
    const payload = {};
    for (const [key, value] of formData.entries()) {
      payload[key] = value;
    }
    // Checkbox fallback if unchecked
    payload.noEmDashes = Boolean(dialog.querySelector('#set-noEmDashes')?.checked);
    payload.targetFps = Number(payload.targetFps) || 60;

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Dashboard-Action': 'settings'
        },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || 'Failed to save settings');
      }
      const saved = await res.json();
      status.textContent = 'Settings saved successfully!';
      status.className = 'settings-status success';

      // Update theme if modified
      if (saved.theme) {
        localStorage.setItem('techno-reel-theme', saved.theme);
        applyTheme(saved.theme);
      }

      setTimeout(() => {
        if (dialog.open) dialog.close();
      }, 700);
    } catch (err) {
      status.textContent = err.message;
      status.className = 'settings-status error';
    } finally {
      saveBtn.disabled = false;
    }
  });
}
