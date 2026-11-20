// Adapted from Techno Reel by Nayan V. See LICENSE in this directory.
import { captionSections, captionRows, formatCaption, writeCaptionClipboard } from './captions.mjs';
import { initTheme, initSettingsModal } from './settings.mjs';

initTheme();
initSettingsModal();

const app = document.querySelector('#app');
const connection = document.querySelector('#connection');
const tabs = ['overview', 'plan', 'previews', 'exports', 'files'];
let projects = [], search = '', filter = 'reels', routeKey = '', signature = '', loaded = false;
const uploadLabels = { tiktok: 'TikTok', instagram: 'Instagram', youtube: 'YouTube' };
let uploadRevision = 0;
const savingUploads = new Map();
const selectedVideos = new Map();
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const date = value => value ? new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '';
const bytes = n => n < 1024 * 1024 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / (1024 * 1024)).toFixed(1)} MB`;
const href = (p, tab = 'overview') => `#${p.kind}/${encodeURIComponent(p.id)}/${tab}`;
const download = f => `${f.url}?download=1`;
const badge = text => `<span class="badge">${escape(text)}</span>`;
const aiBadge = p => p.fullyAiGenerated ? '<span class="badge ai-badge" title="Fully AI-generated video" aria-label="Fully AI-generated video">AI</span>' : '';
const libraryKind = p => p.kind === 'ai-reels' ? 'reels' : p.kind;
const empty = text => `<p class="empty-state">${escape(text)}</p>`;
const fileLink = f => `<a href="${escape(f.url)}" target="_blank" rel="noreferrer">${escape(f.name)}</a>`;

function revealButton(file, label = 'Show in folder', { id = '', className = '' } = {}) {
  return `<button class="button secondary ${escape(className)}"${id ? ` id="${escape(id)}"` : ''} data-reveal-file="${escape(file.path)}" title="Show ${escape(file.name)} in its folder">${escape(label)} ↗</button>`;
}

function fileList(files, reveal = false) {
  return files.length ? `<ul class="files">${files.map(f => `<li><div>${fileLink(f)}<small>${bytes(f.size)} · ${date(f.modified)}</small></div>${reveal ? revealButton(f) : `<a class="button secondary" href="${escape(download(f))}" download aria-label="Download ${escape(f.name)}">↓ Download</a>`}</li>`).join('')}</ul>` : empty('No files here yet.');
}

function renderCards() {
  const matchesFilter = p => {
    if (filter === 'needs-upload') return Object.keys(uploadLabels).some(platform => !p.uploads?.[platform]);
    return filter === 'ai' ? p.fullyAiGenerated : libraryKind(p) === filter;
  };
  const filtered = projects.filter(p => matchesFilter(p) && `${p.title} ${p.id}`.toLowerCase().includes(search.toLowerCase()));
  document.querySelector('#project-count').textContent = `${filtered.length} OF ${projects.length} PROJECT${projects.length === 1 ? '' : 'S'}`;
  document.querySelector('#cards').innerHTML = filtered.map(p => {
    const poster = p.cover || p.previews[0];
    const statusBadge = (p.status && p.status !== 'export available') ? badge(p.status) : '';
    const warnBadge = p.warnings.length ? '<span class="badge warn">Missing files</span>' : '';
    const tags = statusBadge + warnBadge;
    const tagsHtml = tags ? `<div class="tag-list">${tags}</div>` : '';
    return `<a class="card" href="${href(p)}" data-kind="${libraryKind(p)}"><div class="poster">${poster ? `<img loading="lazy" src="${escape(poster.url)}" alt="${escape(p.title)}${p.cover ? ' cover' : ' preview'}">` : `<span class="placeholder">${escape(p.title.slice(0, 2).toLowerCase())}.</span>`}${aiBadge(p)}<span class="poster-kind">${libraryKind(p) === 'reels' ? 'REEL' : p.kind === 'videos' ? 'YOUTUBE VIDEO' : 'SINGLE-VIDEO EDIT'}</span></div><div class="card-body">${tagsHtml}<h2>${escape(p.title)}</h2><div class="card-meta"><span class="meta-exports"><svg class="meta-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m22 8-6 4 6 4V8Z"/><rect width="14" height="12" x="2" y="6" rx="2" ry="2"/></svg> ${p.exports.length ? `${p.exports.length} export${p.exports.length === 1 ? '' : 's'}` : 'In progress'}</span><span class="meta-date">${date(p.updated)}</span></div></div></a>`;
  }).join('') || `<div class="empty">${projects.length ? 'No projects match your search or filter.' : 'No projects yet. <a href="#guide">Read the studio guide</a> to start your first project.'}</div>`;
}

function renderHome() {
  if (routeKey !== 'home') {
    app.innerHTML = `<div class="hero-section"><div class="eyebrow"><span class="eyebrow-dot"></span>Your local studio</div><h1>Your studio. One place.</h1></div><div class="toolbar"><div class="library-controls"><div class="search-box"><svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg><input id="search" type="search" placeholder="Search projects…" aria-label="Search projects" value="${escape(search)}"></div><div class="filters" role="group" aria-label="Project filters">${[['reels', 'Reels'], ['videos', 'Videos'], ['edits', 'Edits'], ['ai', 'AI'], ['needs-upload', 'Needs upload']].map(([value, label]) => `<button class="filter" data-filter="${value}"${value === 'ai' ? ' aria-label="Fully AI-generated videos" title="Fully AI-generated videos"' : ''} aria-pressed="${filter === value}">${label}</button>`).join('')}</div></div><span class="count" id="project-count"></span></div><div id="cards" class="grid"></div>`;
    document.querySelector('#search').addEventListener('input', e => { search = e.target.value; renderCards(); });
    document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
      filter = button.dataset.filter;
      document.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.filter === filter)));
      renderCards();
    }));
  }
  routeKey = 'home';
  renderCards();
}

function uploadChecklist(p) {
  const rows = Object.entries(uploadLabels).map(([platform, label]) => {
    const pending = savingUploads.get(`${p.path}/${platform}`);
    const checked = (pending ?? p.uploads?.[platform]) ? ' checked' : '';
    const disabled = pending !== undefined ? ' disabled' : '';
    return `<label class="upload-row"><input type="checkbox" data-upload="${platform}"${checked}${disabled}> ${label}</label>`;
  });
  return `<section class="panel upload-panel" aria-labelledby="upload-title">
    <h2 id="upload-title">Upload checklist</h2>
    <p class="muted">Check each platform after you upload.</p>
    ${rows.join('')}
    <p class="upload-message" role="status"></p>
  </section>`;
}

async function saveUpload(p, input) {
  const platform = input.dataset.upload;
  const checked = input.checked;
  const marker = `${p.path}/${platform}`;
  const panel = input.closest('.upload-panel');
  let errorMessage = '';
  savingUploads.set(marker, checked);
  uploadRevision++;
  input.disabled = true;
  panel.querySelector('.upload-message').textContent = '';
  try {
    const response = await fetch(`/api/projects/${p.kind}/${encodeURIComponent(p.id)}/uploads/${platform}`, {
      method: checked ? 'PUT' : 'DELETE', headers: { 'X-Dashboard-Action': 'track-upload' },
    });
    if (!response.ok) throw Error();
    const current = projects.find(project => project.path === p.path);
    if (current) current.uploads = { ...current.uploads, [platform]: checked };
  } catch {
    errorMessage = `Couldn’t save ${uploadLabels[platform]}. Try again.`;
  } finally {
    savingUploads.delete(marker);
    uploadRevision++;
    render();
    if (routeKey === `${p.kind}/${p.id}/overview`) {
      const checkbox = document.querySelector(`[data-upload="${platform}"]`);
      checkbox.disabled = false;
      checkbox.checked = errorMessage ? !checked : checked;
      if (errorMessage) document.querySelector('.upload-message').textContent = errorMessage;
    }
  }
}

function mediaPanel(p) {
  const key = `${p.kind}/${p.id}`, selected = selectedVideos.get(key);
  const current = p.exports.find(f => f.path === selected) || p.primary;
  return `<section class="panel media-panel"><div class="panel-title"><div><div class="section-label">YOUR REEL</div><h2>Video</h2></div>${current ? revealButton(current, 'Show video in folder', { id: 'video-reveal' }) : ''}</div>${current ? `<div class="video-wrap"><video id="reel-video" controls playsinline preload="metadata"${p.cover ? ` poster="${escape(p.cover.url)}"` : ''} src="${escape(current.url)}"></video></div>${p.exports.length > 1 ? `<label class="export-label" for="video-select">Available exports</label><select id="video-select">${p.exports.map(f => `<option value="${escape(f.path)}"${f.path === current.path ? ' selected' : ''}>${escape(f.name)}</option>`).join('')}</select>` : `<p class="media-filename">${escape(current.name)}</p>`}` : empty('No exported video yet. Review your plan and previews below.')}</section>`;
}

function captionsPanel(p) {
  const sources = p.captions.map((f, fileIndex) => {
    const sections = captionRows(captionSections(f.text)).map(row => `<div class="caption-row">${row.map(({ section, index: sectionIndex }) => {
      const formatted = formatCaption(section);
      return `<details class="caption-item" data-caption-section="${escape(JSON.stringify([f.path, section.label]))}"><summary>${escape(section.label)}</summary><p class="caption-text">${formatted.html}</p>${formatted.hint ? `<p class="caption-format-note">${escape(formatted.hint)}</p>` : ''}<button class="secondary copy-part" data-caption="${fileIndex}:${sectionIndex}" aria-label="Copy ${escape(section.label)}">${formatted.clipboardHtml ? 'Copy formatted' : 'Copy'}</button></details>`;
    }).join('')}</div>`).join('');
    return `<div class="caption-source"><p class="muted">${fileLink(f)}</p>${sections}</div>`;
  }).join('');
  return `<section class="panel caption-panel"><div class="panel-title"><div><div class="section-label">READY TO SHARE</div><h2>Social captions</h2></div></div>${sources || empty('No social captions yet. Add caption.txt, captions.md, or Social_Copy.md to this project when your copy is ready.')}</section>`;
}

function planPanel(p) {
  const cp = p.creativePlan || {};
  const hasStage1 = cp.planConfirmed || Boolean(cp.speech) || Boolean(cp.plannedEffects && cp.plannedEffects.length);
  const hasStage2 = cp.approved || Boolean(cp.sliceFrames && cp.sliceFrames.length) || Boolean(p.previews && p.previews.length);

  return `<section class="panel plan-panel">
    <div class="panel-title">
      <div>
        <div class="section-label">THE CREATIVE BLUEPRINT</div>
        <h2>Creative Plan & Confirmations</h2>
      </div>
      ${p.kind === 'ai-reels' ? '' : '<button class="button primary" data-review="plan">Review plan in full ↗</button>'}
    </div>
    <p class="muted">
      ${p.renderer === 'nafay'
        ? 'Nafay motion graphics review includes script breakdown, scene feedback, and approval gates.'
        : 'Track your video through its two distinct verification gates: the initial creative direction confirmation and the final slice frame approval before rendering.'}
    </p>

    <div class="confirmations-stack">
      <!-- 1. Initial Plan Confirmation -->
      <div class="confirmation-card ${hasStage1 ? 'confirmed' : 'pending'}">
        <div class="confirmation-header">
          <div class="confirmation-title-wrap">
            <span class="step-num">1</span>
            <div>
              <h3>Initial Plan Confirmation</h3>
              <p class="confirmation-subtitle">Creative direction, speech analysis & visual selection</p>
            </div>
          </div>
          <span class="badge ${cp.planConfirmed ? 'success' : 'pending'}">${cp.planConfirmed ? '✓ Plan Confirmed' : 'Planning in progress'}</span>
        </div>

        ${cp.speech ? `
          <div class="plan-speech-card">
            <div class="micro-label">SPOKEN HOOK / SCRIPT</div>
            <blockquote class="plan-speech-quote">“${escape(cp.speech)}”</blockquote>
          </div>
        ` : ''}

        ${cp.planRationale ? `
          <div class="plan-rationale-box">
            <div class="micro-label">CREATIVE RATIONALE</div>
            <p class="plan-rationale-text">${escape(cp.planRationale)}</p>
          </div>
        ` : ''}

        ${cp.plannedEffects && cp.plannedEffects.length ? `
          <div class="planned-effects-section">
            <div class="micro-label">PLANNED VISUAL SCENES & EFFECTS</div>
            <div class="planned-effects-grid">
              ${cp.plannedEffects.map(fx => `
                <div class="planned-effect-card">
                  <div class="planned-effect-top">
                    <span class="planned-effect-name">${escape(fx.name)}</span>
                    ${fx.timing ? `<span class="planned-effect-time">${escape(fx.timing)}</span>` : ''}
                  </div>
                  ${fx.text ? `<div class="planned-effect-overlay">Overlay text: <strong>“${escape(fx.text)}”</strong></div>` : ''}
                  ${fx.say ? `<div class="planned-effect-say">“${escape(fx.say)}”</div>` : ''}
                  ${fx.reason ? `<p class="planned-effect-reason">${escape(fx.reason)}</p>` : ''}
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        ${cp.initialSelection ? `
          <div class="confirmation-footer">
            <span class="meta-label">CREATOR SELECTION / INSTRUCTION:</span>
            <span class="meta-value">${escape(cp.initialSelection)}</span>
          </div>
        ` : ''}
      </div>

      <!-- 2. Final Slice Frame Confirmation -->
      <div class="confirmation-card ${hasStage2 ? 'confirmed' : 'pending'}">
        <div class="confirmation-header">
          <div class="confirmation-title-wrap">
            <span class="step-num">2</span>
            <div>
              <h3>Final Slice Frame Confirmation</h3>
              <p class="confirmation-subtitle">Actual rendered video frame slices & verification</p>
            </div>
          </div>
          <span class="badge ${cp.approved ? 'success' : 'pending'}">${cp.approved ? '✓ Frames Approved & Verified' : 'Approval pending'}</span>
        </div>

        ${(cp.sliceFrames && cp.sliceFrames.length) ? `
          <div class="slice-frames-section">
            <div class="micro-label">VERIFIED SLICE FRAMES AT EXACT TIMESTAMPS</div>
            <div class="slice-frames-grid">
              ${cp.sliceFrames.map(f => `
                <div class="slice-frame-card">
                  <a href="${escape(f.url)}" target="_blank" rel="noreferrer" class="slice-frame-thumb" title="View full frame">
                    <img loading="lazy" src="${escape(f.url)}" alt="${escape(f.name)}" class="slice-frame-img">
                    ${f.time ? `<span class="slice-frame-tag">${escape(f.time)}</span>` : ''}
                  </a>
                  <div class="slice-frame-meta">
                    <span class="slice-frame-name">${escape(f.name.split('/').pop())}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : (p.previews && p.previews.length) ? `
          <div class="slice-frames-section">
            <div class="micro-label">PREVIEW FRAMES</div>
            <div class="slice-frames-grid">
              ${p.previews.map(f => `
                <div class="slice-frame-card">
                  <a href="${escape(f.url)}" target="_blank" rel="noreferrer" class="slice-frame-thumb" title="View full frame">
                    <img loading="lazy" src="${escape(f.url)}" alt="${escape(f.name)}" class="slice-frame-img">
                  </a>
                  <div class="slice-frame-meta">
                    <span class="slice-frame-name">${escape(f.name.split('/').pop())}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        ` : empty('No preview slice frames generated yet. Generate preview frames in your AI chat before approval.')}

        ${cp.approval ? `
          <div class="approval-card-details">
            <div class="approval-detail-item">
              <span class="detail-label">APPROVAL DECISION</span>
              <strong class="detail-text">“${escape(cp.approval.user_message || cp.approval.message || 'Approved')}”</strong>
            </div>
            <div class="approval-detail-item">
              <span class="detail-label">PREVIEW FINGERPRINT</span>
              <code class="detail-code" title="${escape(cp.previewId || '')}">${escape((cp.previewId || '').slice(0, 16))}…</code>
            </div>
            <div class="approval-detail-item">
              <span class="detail-label">VERIFIED AT</span>
              <span class="detail-date">${date(cp.approval.at)} ${cp.approval.at ? new Date(cp.approval.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
            </div>
          </div>
        ` : ''}
      </div>

      <!-- Feedback History if present -->
      ${cp.feedbackSubmissions && cp.feedbackSubmissions.length ? `
        <div class="feedback-card">
          <div class="micro-label">REVISION & FEEDBACK HISTORY</div>
          <ul class="feedback-list">
            ${cp.feedbackSubmissions.map(sub => `
              <li class="feedback-item">
                <div class="feedback-item-header">
                  <span class="badge ${sub.status === 'handled' ? 'success' : 'warn'}">${escape(sub.status || 'submitted')}</span>
                  <span class="feedback-date">${date(sub.at)}</span>
                </div>
                <p class="feedback-text">“${escape(sub.text)}”</p>
                ${sub.result ? `<div class="feedback-result">↳ ${escape(sub.result)}</div>` : ''}
              </li>
            `).join('')}
          </ul>
        </div>
      ` : ''}

      <!-- Interactive Storyboard iframe if document exists -->
      ${p.plans && p.plans.length ? `
        <details class="storyboard-details">
          <summary class="storyboard-summary">
            <span>Interactive Storyboard Document</span>
            <span class="badge">${escape(p.plans[0].name)}</span>
          </summary>
          <iframe class="preview-frame" title="Interactive Storyboard" sandbox="" loading="lazy" src="${escape(p.plans[0].url)}"></iframe>
        </details>
      ` : ''}
    </div>
  </section>`;
}

function content(p, tab) {
  if (tab === 'overview') return `<div class="overview-layout">${mediaPanel(p)}<section class="panel cover-panel"><div class="panel-title"><div><div class="section-label">YOUR THUMBNAIL</div><h2>Cover image</h2></div></div>${p.cover ? `<a class="cover-link" href="${escape(p.cover.url)}" target="_blank" rel="noreferrer"><img class="cover overview-cover" src="${escape(p.cover.url)}" alt="${escape(p.title)} cover"></a>${revealButton(p.cover, 'Show cover in folder', { className: 'cover-action' })}` : empty('No cover yet. Existing cover images will appear here when added to the project.')}</section><aside class="project-sidebar">${uploadChecklist(p)}</aside>${captionsPanel(p)}</div>`;
  if (tab === 'plan') return planPanel(p);
  if (tab === 'previews') return `<section class="panel"><div class="panel-title"><div><div class="section-label">ACTUAL REVIEW FRAMES</div><h2>Previews</h2></div>${p.kind === 'ai-reels' ? '' : '<button data-review="frames">Review & approve frames ↗</button>'}</div>${p.previews.length ? `<div class="frame-grid">${p.previews.map(f => `<figure><a href="${escape(f.url)}" target="_blank" rel="noreferrer"><img loading="lazy" src="${escape(f.url)}" alt="${escape(f.name)}"></a><figcaption>${escape(f.name)} <a href="${escape(download(f))}" download aria-label="Download ${escape(f.name)}">↓</a></figcaption></figure>`).join('')}</div>` : empty('No preview frames yet. Generate them in your AI chat before approving an export.')}</section>`;
  if (tab === 'exports') return `<section class="panel"><div class="section-label">SAVED ON THIS DEVICE</div><h2>Videos</h2>${fileList(p.exports, true)}</section><section class="panel"><h2>Covers</h2>${fileList(p.covers, true)}</section>${captionsPanel(p)}`;
  const originals = p.files.filter(f => f.name.startsWith('raw/') || f.path === p.source?.path);
  const supporting = p.files.filter(f => !originals.includes(f));
  return `<section class="panel"><div class="section-label">YOUR ORIGINAL RECORDINGS</div><h2>Original footage</h2>${fileList(originals)}</section><section class="panel"><h2>Supporting files</h2><p class="muted">Plans, assets, saved checks, and exports. Runtime caches and composition source folders are omitted.</p>${fileList(supporting)}</section>`;
}

async function copy(button, text, html = '') {
  try {
    const richCopied = await writeCaptionClipboard({ text, clipboardHtml: html }) === 'formatted';
    const old = button.textContent; button.textContent = richCopied ? 'Copied formatted' : html ? 'Copied plain text' : 'Copied';
    setTimeout(() => { if (button.isConnected) button.textContent = old; }, 1800);
  } catch { document.querySelector('#folder-status').textContent = 'Copy unavailable. Select and copy the text directly.'; }
}

function renderProject(p, tab) {
  const key = `${p.kind}/${p.id}/${tab}`;
  const nextSignature = JSON.stringify(p);
  if (key === routeKey && signature === nextSignature) return;
  const focusedUpload = key === routeKey && document.activeElement?.dataset.upload;
  const oldVideo = key === routeKey ? document.querySelector('#reel-video') : null;
  const wasPlaying = oldVideo && !oldVideo.paused;
  const oldTime = oldVideo?.currentTime;
  const openCaptions = new Set(key === routeKey ? [...document.querySelectorAll('details[data-caption-section][open]')].map(item => item.dataset.captionSection) : []);
  app.innerHTML = `<a class="back" href="#"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg> ALL PROJECTS</a><div class="project-heading"><div><div class="eyebrow"><span class="eyebrow-dot"></span>${libraryKind(p) === 'reels' ? 'Combined reel' : p.kind === 'videos' ? 'YouTube video' : 'Single-video edit'}</div><h1>${escape(p.title)}</h1><div class="path">${escape(p.path)}/</div></div><div class="heading-actions"><button class="secondary button-icon" id="open-folder"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg> Open project folder</button><button class="secondary button-icon" id="copy-path"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg> Copy folder path</button><span id="folder-status" role="status"></span></div></div><nav class="tabs" aria-label="Project sections">${tabs.map(t => `<a class="${tab === t ? 'active' : ''}"${tab === t ? ' aria-current="page"' : ''} href="${href(p, t)}">${t[0].toUpperCase() + t.slice(1)}</a>`).join('')}</nav><div id="content">${content(p, tab)}</div>`;
  const newVideo = document.querySelector('#reel-video');
  if (oldVideo && newVideo && oldVideo.getAttribute('src') === newVideo.getAttribute('src')) {
    newVideo.replaceWith(oldVideo);
    if (Number.isFinite(oldTime)) oldVideo.currentTime = oldTime;
    if (wasPlaying) oldVideo.play().catch(() => {});
  }
  document.querySelectorAll('details[data-caption-section]').forEach(item => { item.open = openCaptions.has(item.dataset.captionSection); });
  routeKey = key; signature = nextSignature;
  document.querySelectorAll('[data-upload]').forEach(input => {
    input.addEventListener('change', () => saveUpload(p, input));
    if (input.dataset.upload === focusedUpload) input.focus({ preventScroll: true });
  });
  document.querySelectorAll('[data-review]').forEach(button=>button.addEventListener('click',async()=>{
    button.disabled=true;
    try {
      const response=await fetch(`/api/reviews/${p.kind}/${encodeURIComponent(p.id)}/prepare`,{method:'POST',headers:{'Content-Type':'application/json','X-Dashboard-Action':'review'},body:JSON.stringify({stage:button.dataset.review})});
      const data=await response.json();if(!response.ok)throw Error(data.error);
      location.href=`/review/${p.kind}/${encodeURIComponent(p.id)}`;
    }catch(error){document.querySelector('#folder-status').textContent=error.message;button.disabled=false;}
  }));
  document.querySelector('#copy-path').addEventListener('click', e => copy(e.currentTarget, `${p.path}/`));
  document.querySelector('#open-folder').addEventListener('click', async () => {
    const status = document.querySelector('#folder-status');
    try {
      const response = await fetch(`/api/projects/${p.kind}/${encodeURIComponent(p.id)}/open`, { method: 'POST', headers: { 'X-Dashboard-Action': 'open-folder' } });
      status.textContent = response.ok ? 'Opened on this device.' : 'Could not open the folder on this device.';
    } catch { status.textContent = 'Dashboard disconnected. Check the terminal.'; }
  });
  document.querySelectorAll('[data-reveal-file]').forEach(button => button.addEventListener('click', async () => {
    const status = document.querySelector('#folder-status');
    button.disabled = true;
    status.textContent = 'Opening file location…';
    try {
      const response = await fetch(`/api/projects/${p.kind}/${encodeURIComponent(p.id)}/reveal`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Dashboard-Action': 'reveal-file' },
        body: JSON.stringify({ path: button.dataset.revealFile }),
      });
      status.textContent = response.ok ? 'File shown in its folder.' : 'Could not show the file in its folder on this device.';
    } catch { status.textContent = 'Dashboard disconnected. Check the terminal.'; }
    finally { button.disabled = false; }
  }));
  document.querySelector('#video-select')?.addEventListener('change', e => {
    selectedVideos.set(`${p.kind}/${p.id}`, e.target.value);
    const f = p.exports.find(f => f.path === e.target.value);
    document.querySelector('#reel-video').src = f.url;
    document.querySelector('#video-reveal').dataset.revealFile = f.path;
  });
  document.querySelectorAll('[data-caption]').forEach(button => button.addEventListener('click', () => {
    const [file, section] = button.dataset.caption.split(':').map(Number);
    const formatted = formatCaption(captionSections(p.captions[file].text)[section]);
    copy(button, formatted.text, formatted.clipboardHtml);
  }));
}

function render() {
  if (location.hash === '#guide') {
    if (routeKey !== 'guide') {
      app.replaceChildren(document.querySelector('#studio-guide').content.cloneNode(true));
      routeKey = 'guide';
      app.querySelector('h1').focus();
    }
    return;
  }
  let kind, id, tab;
  try { [kind, id, tab = 'overview'] = decodeURIComponent(location.hash.slice(1)).split('/'); }
  catch { kind = 'invalid'; }
  if (!kind) return renderHome();
  const p = projects.find(p => p.kind === kind && p.id === id);
  if (p) renderProject(p, tabs.includes(tab) ? tab : 'overview');
  else { app.innerHTML = '<div class="empty">Project not found. <a href="#">Back to your library</a></div>'; routeKey = 'missing'; }
}

async function refresh() {
  const revision = uploadRevision;
  try {
    const response = await fetch('/api/projects');
    if (!response.ok) throw Error('Unavailable');
    const latest = await response.json();
    if (revision !== uploadRevision || savingUploads.size) return;
    projects = latest; loaded = true;
    connection.textContent = 'Up to date'; connection.className = '';
    render();
  } catch {
    connection.textContent = 'Disconnected · retrying'; connection.className = 'error';
    if (!loaded && location.hash !== '#guide') app.innerHTML = '<div class="empty">Cannot read projects. Check the dashboard terminal. Retrying automatically…</div>';
  } finally { setTimeout(refresh, 5000); }
}
window.addEventListener('hashchange', render);
if (location.hash === '#guide') render();
refresh();
