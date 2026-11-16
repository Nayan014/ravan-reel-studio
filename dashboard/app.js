// Adapted from Techno Reel by Nayan V. See LICENSE in this directory.
import { captionSections } from './captions.mjs';

const app = document.querySelector('#app');
const connection = document.querySelector('#connection');
const tabs = ['overview', 'plan', 'previews', 'exports', 'files'];
let projects = [], search = '', filter = 'all', routeKey = '', signature = '', loaded = false;
const selectedVideos = new Map();
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const date = value => value ? new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '';
const bytes = n => n < 1024 * 1024 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / (1024 * 1024)).toFixed(1)} MB`;
const href = (p, tab = 'overview') => `#${p.kind}/${encodeURIComponent(p.id)}/${tab}`;
const download = f => `${f.url}?download=1`;
const badge = text => `<span class="badge">${escape(text)}</span>`;
const empty = text => `<p class="empty-state">${escape(text)}</p>`;
const fileLink = f => `<a href="${escape(f.url)}" target="_blank" rel="noreferrer">${escape(f.name)}</a>`;

function revealButton(file, label = 'Show in folder', { id = '', className = '' } = {}) {
  return `<button class="button secondary ${escape(className)}"${id ? ` id="${escape(id)}"` : ''} data-reveal-file="${escape(file.path)}" title="Show ${escape(file.name)} in its folder">${escape(label)} ↗</button>`;
}

function fileList(files, reveal = false) {
  return files.length ? `<ul class="files">${files.map(f => `<li><div>${fileLink(f)}<small>${bytes(f.size)} · ${date(f.modified)}</small></div>${reveal ? revealButton(f) : `<a class="button secondary" href="${escape(download(f))}" download aria-label="Download ${escape(f.name)}">↓ Download</a>`}</li>`).join('')}</ul>` : empty('No files here yet.');
}

function renderCards() {
  const filtered = projects.filter(p => (filter === 'all' || p.kind === filter) && `${p.title} ${p.id}`.toLowerCase().includes(search.toLowerCase()));
  document.querySelector('#project-count').textContent = `${filtered.length} OF ${projects.length} PROJECT${projects.length === 1 ? '' : 'S'}`;
  document.querySelector('#cards').innerHTML = filtered.map(p => {
    const poster = p.cover || p.previews[0];
    return `<a class="card" href="${href(p)}"><div class="poster">${poster ? `<img loading="lazy" src="${escape(poster.url)}" alt="${escape(p.title)}${p.cover ? ' cover' : ' preview'}">` : `<span class="placeholder">${escape(p.title.slice(0, 2).toLowerCase())}.</span>`}<span class="poster-kind">${p.kind === 'reels' ? 'REEL' : p.kind === 'videos' ? 'YOUTUBE VIDEO' : 'SINGLE-VIDEO EDIT'}</span></div><div class="card-body"><div class="tag-list">${badge(p.status)}${p.warnings.length ? '<span class="badge warn">Missing files</span>' : ''}</div><h2>${escape(p.title)}</h2><div class="card-meta"><span>${p.exports.length ? `${p.exports.length} export${p.exports.length === 1 ? '' : 's'}` : 'In progress'}</span><span>${date(p.updated)}</span></div></div></a>`;
  }).join('') || `<div class="empty">${projects.length ? 'No projects match your search or filter.' : 'Your library is ready. Create a reel with /wf-reel or edit a video with /wf-video in your AI chat. Finished work and previews will appear here.'}</div>`;
}

function renderHome() {
  if (routeKey !== 'home') {
    app.innerHTML = `<div class="eyebrow">Your local studio</div><h1>Your studio. One place.</h1><p class="description">Your footage, your ideas, your finished work. Browse reels, YouTube videos and edits, review the details, and find everything you need to share.</p><div class="toolbar"><div class="library-controls"><input id="search" type="search" placeholder="Find a project…" aria-label="Find a project" value="${escape(search)}"><div class="filters" role="group" aria-label="Project type">${[['all', 'All'], ['reels', 'Reels'], ['videos', 'Videos'], ['edits', 'Edits']].map(([value, label]) => `<button class="filter" data-filter="${value}" aria-pressed="${filter === value}">${label}</button>`).join('')}</div></div><span class="count" id="project-count"></span></div><div id="cards" class="grid"></div><div class="notice"><strong>Your next project starts in your AI chat.</strong><p>Use <code>/wf-reel-plan</code> for a reel, <code>/wf-video-plan</code> for YouTube, or <code>/wf-video</code> for a quick single-video edit. Plans, previews, and exports appear here automatically.</p></div>`;
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

function savedStatus(p) {
  return `<section class="panel status-panel"><div class="section-label">SAVED PROJECT STATUS</div><div class="tag-list">${badge(p.status)}${p.renderer ? badge(p.renderer) : ''}</div><p class="next-action">Approvals and checks below are saved records. Their validity for the current files has not been rechecked.</p>${p.records.map(r => `<details><summary>${escape(r.label)}</summary><pre>${escape(JSON.stringify(r.data, null, 2))}</pre></details>`).join('')}${p.warnings.length ? `<div class="warnings" role="status">${p.warnings.map(w => `<p>${escape(w)}</p>`).join('')}</div>` : ''}<p class="intro-note">Create and revise with your editing agent. Submit feedback and approvals in the interactive review.</p></section>`;
}

function mediaPanel(p) {
  const key = `${p.kind}/${p.id}`, selected = selectedVideos.get(key);
  const current = p.exports.find(f => f.path === selected) || p.primary;
  return `<section class="panel media-panel"><div class="panel-title"><div><div class="section-label">YOUR REEL</div><h2>Video</h2></div>${current ? revealButton(current, 'Show video in folder', { id: 'video-reveal' }) : ''}</div>${current ? `<div class="video-wrap"><video id="reel-video" controls playsinline preload="metadata"${p.cover ? ` poster="${escape(p.cover.url)}"` : ''} src="${escape(current.url)}"></video></div>${p.exports.length > 1 ? `<label class="export-label" for="video-select">Available exports</label><select id="video-select">${p.exports.map(f => `<option value="${escape(f.path)}"${f.path === current.path ? ' selected' : ''}>${escape(f.name)}</option>`).join('')}</select>` : `<p class="media-filename">${escape(current.name)}</p>`}` : empty('No exported video yet. Review your plan and previews below.')}</section>`;
}

function captionsPanel(p) {
  return `<section class="panel caption-panel"><div class="panel-title"><div><div class="section-label">READY TO SHARE</div><h2>Social captions</h2></div></div>${p.captions.length ? p.captions.map((f, fileIndex) => `<div class="caption-source"><p class="muted">${fileLink(f)}</p>${captionSections(f.text).map((section, sectionIndex) => `<details class="caption-item" data-caption-section="${escape(JSON.stringify([f.path, section.label]))}"><summary>${escape(section.label)}</summary><p>${escape(section.text)}</p><button class="secondary copy-part" data-caption="${fileIndex}:${sectionIndex}" aria-label="Copy ${escape(section.label)}">Copy</button></details>`).join('')}</div>`).join('') : empty('No social captions yet. Add caption.txt, captions.md, or Social_Copy.md to this project when your copy is ready.')}</section>`;
}

function content(p, tab) {
  if (tab === 'overview') return `<div class="overview-layout">${mediaPanel(p)}<section class="panel cover-panel"><div class="panel-title"><div><div class="section-label">YOUR THUMBNAIL</div><h2>Cover image</h2></div></div>${p.cover ? `<a class="cover-link" href="${escape(p.cover.url)}" target="_blank" rel="noreferrer"><img class="cover overview-cover" src="${escape(p.cover.url)}" alt="${escape(p.title)} cover"></a>${revealButton(p.cover, 'Show cover in folder', { className: 'cover-action' })}` : empty('No cover yet. Existing cover images will appear here when added to the project.')}</section><aside class="project-sidebar">${savedStatus(p)}</aside>${captionsPanel(p)}</div>`;
  if (tab === 'plan') return `<section class="panel"><div class="panel-title"><div><div class="section-label">THE CREATIVE DIRECTION</div><h2>Plans & frame reviews</h2></div><button data-review="plan">Review plan ↗</button></div><p class="muted">${p.renderer==='nafay'?'The interactive review includes script, scene and frame feedback, voice/effects previews and approval.':'The interactive review includes script, scene and frame feedback, music selection and approval.'} ${p.renderer==='nafay'?'Nafay graphics are edited in chat through the saved story.js.':'Use Hyperframes Studio for visual editing.'}</p>${p.plans.length ? p.plans.map(f => `<details class="plan-document"${f.path === p.plans[0].path ? ' open' : ''}><summary>${escape(f.name)}</summary><p>${fileLink(f)} · <a href="${escape(download(f))}" download>Download HTML</a></p><iframe class="preview-frame" title="${escape(f.name)}" sandbox="" loading="lazy" src="${escape(f.url)}"></iframe></details>`).join('') : empty('No HTML plan yet. Saved JSON plans are available below.')}${fileList(p.files.filter(f => /(?:^|\/)(?:plan|session)\.json$/.test(f.name)))}</section>`;
  if (tab === 'previews') return `<section class="panel"><div class="panel-title"><div><div class="section-label">ACTUAL REVIEW FRAMES</div><h2>Previews</h2></div><button data-review="frames">Review & approve frames ↗</button></div>${p.previews.length ? `<div class="frame-grid">${p.previews.map(f => `<figure><a href="${escape(f.url)}" target="_blank" rel="noreferrer"><img loading="lazy" src="${escape(f.url)}" alt="${escape(f.name)}"></a><figcaption>${escape(f.name)} <a href="${escape(download(f))}" download aria-label="Download ${escape(f.name)}">↓</a></figcaption></figure>`).join('')}</div>` : empty('No preview frames yet. Generate them in your AI chat before approving an export.')}</section>`;
  if (tab === 'exports') return `<section class="panel"><div class="section-label">SAVED ON THIS DEVICE</div><h2>Videos</h2>${fileList(p.exports, true)}</section><section class="panel"><h2>Covers</h2>${fileList(p.covers, true)}</section>${captionsPanel(p)}`;
  const originals = p.files.filter(f => f.name.startsWith('raw/') || f.path === p.source?.path);
  const supporting = p.files.filter(f => !originals.includes(f));
  return `<section class="panel"><div class="section-label">YOUR ORIGINAL RECORDINGS</div><h2>Original footage</h2>${fileList(originals)}</section><section class="panel"><h2>Supporting files</h2><p class="muted">Plans, assets, saved checks, and exports. Runtime caches and composition source folders are omitted.</p>${fileList(supporting)}</section>`;
}

async function copy(button, text) {
  try {
    await navigator.clipboard.writeText(text);
    const old = button.textContent; button.textContent = 'Copied';
    setTimeout(() => { if (button.isConnected) button.textContent = old; }, 1800);
  } catch { document.querySelector('#folder-status').textContent = 'Copy unavailable. Select and copy the text directly.'; }
}

function renderProject(p, tab) {
  const key = `${p.kind}/${p.id}/${tab}`;
  const nextSignature = JSON.stringify(p);
  if (key === routeKey && signature === nextSignature) return;
  const oldVideo = key === routeKey ? document.querySelector('#reel-video') : null;
  const wasPlaying = oldVideo && !oldVideo.paused;
  const oldTime = oldVideo?.currentTime;
  const openCaptions = new Set(key === routeKey ? [...document.querySelectorAll('details[data-caption-section][open]')].map(item => item.dataset.captionSection) : []);
  app.innerHTML = `<a class="back" href="#">← ALL PROJECTS</a><div class="project-heading"><div><div class="eyebrow">${p.kind === 'reels' ? 'Combined reel' : p.kind === 'videos' ? 'YouTube video' : 'Single-video edit'}</div><h1>${escape(p.title)}</h1><div class="path">${escape(p.path)}/</div></div><div class="heading-actions"><button class="secondary" id="open-folder">Open project folder ↗</button><button class="secondary" id="copy-path">Copy folder path</button><span id="folder-status" role="status"></span></div></div><nav class="tabs" aria-label="Project sections">${tabs.map(t => `<a class="${tab === t ? 'active' : ''}"${tab === t ? ' aria-current="page"' : ''} href="${href(p, t)}">${t[0].toUpperCase() + t.slice(1)}</a>`).join('')}</nav><div id="content">${content(p, tab)}</div>`;
  const newVideo = document.querySelector('#reel-video');
  if (oldVideo && newVideo && oldVideo.getAttribute('src') === newVideo.getAttribute('src')) {
    newVideo.replaceWith(oldVideo);
    if (Number.isFinite(oldTime)) oldVideo.currentTime = oldTime;
    if (wasPlaying) oldVideo.play().catch(() => {});
  }
  document.querySelectorAll('details[data-caption-section]').forEach(item => { item.open = openCaptions.has(item.dataset.captionSection); });
  routeKey = key; signature = nextSignature;
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
    copy(button, captionSections(p.captions[file].text)[section].text);
  }));
}

function render() {
  let kind, id, tab;
  try { [kind, id, tab = 'overview'] = decodeURIComponent(location.hash.slice(1)).split('/'); }
  catch { kind = 'invalid'; }
  if (!kind) return renderHome();
  const p = projects.find(p => p.kind === kind && p.id === id);
  if (p) renderProject(p, tabs.includes(tab) ? tab : 'overview');
  else { app.innerHTML = '<div class="empty">Project not found. <a href="#">Back to your library</a></div>'; routeKey = 'missing'; }
}

async function refresh() {
  try {
    const response = await fetch('/api/projects');
    if (!response.ok) throw Error('Unavailable');
    projects = await response.json(); loaded = true;
    connection.textContent = 'Up to date'; connection.className = '';
    render();
  } catch {
    connection.textContent = 'Disconnected · retrying'; connection.className = 'error';
    if (!loaded) app.innerHTML = '<div class="empty">Cannot read projects. Check the dashboard terminal. Retrying automatically…</div>';
  } finally { setTimeout(refresh, 5000); }
}
window.addEventListener('hashchange', render);
refresh();
