import { initTheme, initSettingsModal } from './settings.mjs';

initTheme();
initSettingsModal();

const [, , kind, id] = location.pathname.split('/');
const api = `/api/reviews/${encodeURIComponent(kind)}/${encodeURIComponent(id)}`;
const $ = name => document.getElementById(name);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const media = name => '/media/' + name.split('/').map(encodeURIComponent).join('/');
let state = null, displayed = '', sending = false, connected = false;
const storagePrefix = `reel-feedback:${kind}/${id}:`;
const key = (scope, target) => `${storagePrefix}${state.request.id}:${scope}:${target}`;
const draft = (scope, target) => { try { return localStorage.getItem(key(scope, target)) || ''; } catch { return ''; } };

// Audio and video playback mutual exclusion
document.addEventListener('play', event => {
  const target = event.target;
  if (target && (target.tagName === 'AUDIO' || target.tagName === 'VIDEO')) {
    document.querySelectorAll('audio, video').forEach(mediaEl => {
      if (mediaEl !== target && !mediaEl.paused) {
        mediaEl.pause();
      }
    });
  }
}, true);

function feedback(scope, target = '', scene = '', label = '') {
  const targetLabel = label || (scope === 'script' ? 'full script' : scope === 'frame' ? 'this frame' : 'scene ' + scene);
  const submitted = (state?.submissions || []).filter(s =>
    s.action === 'feedback' &&
    s.scope === scope &&
    ((scope === 'frame' && s.frame === target) ||
     (scope === 'scene' && s.scene === scene) ||
     (scope === 'script' && s.scope === 'script'))
  );

  const badgeHtml = submitted.length ? `
    <div class="submitted-feedback-list">
      ${submitted.map(s => `
        <div class="submitted-feedback-badge ${esc(s.status)}">
          <span class="badge-title">Submitted feedback (${esc(s.status)}):</span>
          <p class="badge-text">${esc(s.text)}</p>
        </div>
      `).join('')}
    </div>
  ` : '';

  return `
    <div class="target-feedback" data-scope="${scope}" data-target="${esc(target)}" data-scene="${esc(scene)}">
      <label>Feedback · ${esc(targetLabel)}</label>
      <textarea aria-label="Feedback on ${scope} ${esc(target)}" maxlength="8000" rows="3" placeholder="Describe what to change here…">${esc(draft(scope, target))}</textarea>
      <span class="saved-draft"></span>
      ${badgeHtml}
    </div>
  `;
}

function effectCell(scene) {
  const effects = state.effectsCatalogue || [];
  const selectedId = scene.effects?.effects?.[0]?.id ? String(scene.effects.effects[0].id) : (scene.effects?.status === 'none' ? 'none' : '');
  const activeEffect = effects.find(e => e.id === selectedId);

  // Group effects by category (e.g. "Vibha Effects", "Techno Ravan Effects")
  const categories = {};
  for (const e of effects) {
    const cat = e.category || 'Vibha Effects';
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(e);
  }

  const optgroups = Object.entries(categories).map(([catName, list]) => {
    const opts = list.map(e => {
      const isSelected = e.id === selectedId;
      const subtitle = e.subtitle || e.use || '';
      const label = `#${esc(e.id)} · ${esc(e.name)}${subtitle ? ' · ' + esc(subtitle) : ''}`;
      return `<option value="${esc(e.id)}" ${isSelected ? 'selected' : ''}>${label}</option>`;
    }).join('');
    return `<optgroup label="${esc(catName)}">${opts}</optgroup>`;
  }).join('');

  let card = '';
  if (activeEffect) {
    const categoryName = activeEffect.category || 'Vibha Effects';
    const subtitle = activeEffect.subtitle || activeEffect.use || '';
    card = `
      <div class="effect-preview-card">
        <img class="effect-preview-thumb" src="${esc(activeEffect.previewUrl)}" alt="${esc(activeEffect.name)} preview">
        <div class="effect-info">
          <span class="effect-category-pill">${esc(categoryName)}</span>
          <strong>#${esc(activeEffect.id)} · ${esc(activeEffect.name)}</strong>
          ${subtitle ? `<span class="effect-subtitle">${esc(subtitle)}</span>` : ''}
          <p class="effect-desc">${esc(activeEffect.desc)}</p>
          <span class="effect-use">Best for: ${esc(activeEffect.use || subtitle)}</span>
        </div>
      </div>
    `;
  } else if (selectedId === 'none') {
    card = `<div class="effect-preview-card none"><span class="muted">No effect applied</span></div>`;
  } else {
    card = `<div class="effect-preview-card pending"><span class="muted">Choose an effect from the dropdown</span></div>`;
  }

  return `
    <div class="effect-selector-wrap" data-scene="${esc(scene.id)}">
      <label class="effect-select-label" for="effect-select-${esc(scene.id)}">Effect</label>
      <select id="effect-select-${esc(scene.id)}" class="effect-dropdown" data-scene="${esc(scene.id)}">
        <option value="" ${!selectedId ? 'selected' : ''} disabled>Select effect…</option>
        <option value="none" ${selectedId === 'none' ? 'selected' : ''}>None (no effect)</option>
        ${optgroups}
      </select>
      ${card}
    </div>
  `;
}

function controls() {
  const blocked = sending || !connected || !state || state.stale;
  const textareas = [...document.querySelectorAll('.target-feedback textarea')];
  const hasFeedbackText = textareas.some(t => t.value.trim().length > 0);
  const isPlan = state?.request?.stage === 'plan';

  if ($('submit-all-feedback')) {
    if (isPlan) {
      $('submit-all-feedback').style.display = 'none';
    } else {
      $('submit-all-feedback').style.display = '';
      $('submit-all-feedback').disabled = Boolean(blocked || !hasFeedbackText);
    }
  }

  if (isPlan) {
    $('approve').textContent = hasFeedbackText ? 'Submit feedback and generate previews' : 'Approve plan and generate previews';
  } else if (state?.request?.stage === 'frames') {
    $('approve').textContent = 'Approve current frames and audio';
  } else if (state?.request?.stage === 'script') {
    $('approve').textContent = 'Approve script';
  }
  const pendingReading = state?.request?.stage !== 'script' && state?.request?.scenes.some(s => s.audition);
  $('approve').disabled = Boolean(blocked || (pendingReading && !hasFeedbackText));

  document.querySelectorAll('[data-music],[data-reading]').forEach(button => {
    button.disabled = Boolean(blocked);
  });
  document.querySelectorAll('.effect-dropdown').forEach(select => {
    select.disabled = Boolean(blocked);
  });
  if ($('music-select')) {
    $('music-select').disabled = Boolean(blocked);
  }
  if ($('apply-music-btn')) {
    const val = $('music-select')?.value;
    const current = state?.request?.audio?.music || 'none';
    $('apply-music-btn').disabled = Boolean(blocked || val === current);
  }
}

function audioPanel(r) {
  if (!r.audio) return '';
  const tracks = state.catalogue.filter(t => t.kind === 'music' && (t.popularity?.scope === 'recording' || t.id === r.audio.music));
  const sfxTracks = state.catalogue.filter(t => t.kind === 'sfx' && t.popularity?.scope === 'recording');
  const selectedTrackId = r.audio.music || 'none';
  const recommendedTrackId = r.audio.recommended_music || (tracks[0]?.id || '');

  const musicOptions = [
    `<option value="none" ${selectedTrackId === 'none' ? 'selected' : ''}>No background music</option>`,
    ...tracks.map(t => {
      const isRec = t.id === recommendedTrackId;
      const label = `${t.title}${isRec ? ' (Recommended)' : ''} · ${t.moods.join(', ')} · ${t.duration.toFixed(0)}s`;
      return `<option value="${esc(t.id)}" ${t.id === selectedTrackId ? 'selected' : ''}>${esc(label)}</option>`;
    })
  ].join('');

  const sfxOptions = sfxTracks.map(t => {
    return `<option value="${esc(t.id)}">${esc(t.title)} (${esc(t.moods.join(', '))} · ${t.duration.toFixed(2)}s)</option>`;
  }).join('');

  const cues = (r.audio.sfx || []).map(c => {
    const t = state.catalogue.find(t => t.id === c.sound);
    return t ? `<span class="sound-cue-pill">Scene ${esc(c.scene)}: ${esc(t.title)}</span>` : '';
  }).filter(Boolean).join('');

  const activeTrack = tracks.find(t => t.id === selectedTrackId);

  return `
    <h2>Music and sound</h2>
    <div class="audio-controls-grid">
      <div class="audio-selector-card">
        <label for="music-select"><strong>Background music</strong></label>
        <div class="audio-dropdown-row">
          <select id="music-select" class="audio-dropdown">
            ${musicOptions}
          </select>
          <button type="button" id="apply-music-btn" class="audio-apply-btn" data-music="${esc(selectedTrackId)}" disabled>
            Selected
          </button>
        </div>
        <div id="music-preview-box" class="audio-preview-box">
          ${activeTrack ? `
            <audio id="music-audio-player" controls preload="none" src="/audio/${encodeURIComponent(activeTrack.id)}" aria-label="Play ${esc(activeTrack.title)}"></audio>
            <p class="audio-meta"><strong>${esc(activeTrack.title)}</strong> · ${esc(activeTrack.moods.join(' · '))} · ${activeTrack.duration.toFixed(1)}s · <small>${esc(activeTrack.author)} · ${esc(activeTrack.license)}</small></p>
          ` : `
            <p class="muted">No background music selected.</p>
          `}
        </div>
      </div>

      ${r.audio.mixSample ? `
        <div class="audio-mix-card">
          <label><strong>${r.audio.fullMix ? 'Full audio mix' : 'Archived audio sample'}</strong></label>
          <audio controls preload="metadata" src="${esc(r.audio.mixSample)}" aria-label="Selected music mixed with voice"></audio>
          ${r.audio.fullMix ? r.scenes.map(scene => `<div><label>Scene ${esc(scene.id)} · ${Number(scene.timeline[0]).toFixed(1)}–${Number(scene.timeline[1]).toFixed(1)}s</label><audio controls preload="none" aria-label="Mix for scene ${esc(scene.id)}" src="${esc(r.audio.mixSample)}#t=${Number(scene.timeline[0])},${Number(scene.timeline[1])}"></audio></div>`).join('') : ''}
          <p class="audio-meta">${r.audio.fullMix ? 'Play any scene to hear its speech, music and sound effects.' : 'Generate fresh frames to review the full mix.'}</p>
        </div>
      ` : ''}
    </div>

    ${cues ? `
      <div class="sound-cues-bar">
        <strong>Suggested scene sound cues:</strong> ${cues}
      </div>
    ` : ''}

    <details class="sfx-library-details">
      <summary>Audition sound effects (${sfxTracks.length} sounds)</summary>
      <div class="sfx-audition-box">
        <select id="sfx-select" class="audio-dropdown">
          <option value="" disabled selected>Choose a sound effect to audition…</option>
          ${sfxOptions}
        </select>
        <audio id="sfx-audio-player" controls preload="none" style="display:none; width: 100%;"></audio>
      </div>
    </details>
  `;
}

function readings(scene) {
  if (!scene.audition) return scene.voice === 'kokoro' ? '<small>Selected Kokoro narration</small>' : '';
  return ['A','B'].map(key => `<div><audio controls preload="none" src="${esc(scene.audition.takes[key])}" aria-label="Scene ${esc(scene.id)} reading ${key}"></audio>
    <button type="button" data-reading="${key}" data-scene="${esc(scene.id)}" data-audition="${esc(scene.audition.id)}">Use reading ${key}</button></div>`).join('');
}

function render() {
  const r = state.request;
  $('title').textContent = r.title;
  $('stage').textContent = r.stage === 'frames' ? 'ACTUAL FRAMES AND AUDIO' : r.stage === 'script' ? 'SCRIPT AND SHOOTING PLAN' : 'PRODUCTION PLAN';
  $('revision').textContent = `Revision ${r.id.slice(0, 8)} · ${new Date(r.createdAt).toLocaleString()}`;
  $('native-studio').hidden = !state.studioAvailable;
  $('approve').textContent = r.stage === 'frames' ? 'Approve current frames and audio' : r.stage === 'script' ? 'Approve script' : 'Approve plan and visual choices';
  if (displayed !== r.id) {
    const quality = r.outputProfile;
    $('quality').innerHTML = quality ? `<div class="spec-tags-row"><span class="spec-tag">${quality.width > quality.height ? 'Landscape' : 'Portrait'}</span><span class="spec-tag accent">${Math.min(quality.width, quality.height) === 2160 ? '4K UHD' : Math.min(quality.width, quality.height) === 1080 ? '1080p HD' : ''}</span><span class="spec-tag">${quality.width}×${quality.height}</span><span class="spec-tag">${quality.fps} FPS</span></div>` : 'Output quality will be confirmed from the recordings.';
    $('crop').textContent = quality ? 'Framing follows the reviewed crop or fit choice. Changing aspect ratio can crop the picture or add padding. The actual frames below show the result.' : '';
    $('script').innerHTML = `<h2>Full script</h2><div class="script-card">${r.scenes.map(s => `<p class="script-line"><strong class="script-scene-num">Scene ${esc(s.id)}</strong> <span class="script-text">${esc(s.text)}</span></p>`).join('')}</div>${feedback('script')}${r.referenceStyle ? `<aside><h3>Reference style · ${esc(r.referenceStyle.name)}</h3><p>${esc(r.referenceStyle.summary)}</p><p>Style notes guide the proposed scene treatments. Review their actual appearance in the frames below.</p></aside>` : ''}`;
    $('scene-summary').innerHTML = r.scenes.length ? `<h2>Scene-by-scene production plan</h2><div class="table-scroll"><table><thead><tr><th class="col-time">Scene / timing</th><th class="col-dialogue">Dialogue</th><th class="col-footage">Footage / shooting notes</th><th class="col-captions">Spoken captions</th><th class="col-effects">Effects</th></tr></thead><tbody>${r.scenes.map(s => `<tr><td><strong class="scene-id">Scene ${esc(s.id)}</strong><span class="scene-timing-badge">${s.timeline ? s.timeline.map(n => Number(n).toFixed(2)).join('–') + 's' : 'Record after approval'}</span></td><td><p class="scene-dialogue-text">${esc(s.text)}</p>${readings(s)}${feedback('scene', s.id, s.id)}</td><td><strong class="footage-name">${esc(s.source)}</strong>${s.shootingNote ? `<p class="shooting-note">${esc(s.shootingNote)}</p>` : ''}${s.sourceFrame ? `<img class="source-frame" src="${esc(s.sourceFrame)}" alt="Original scene ${esc(s.id)} before effects">` : ''}</td><td>${s.captions.length ? `<div class="caption-pages-wrap">${s.captions.map(c => `<span class="caption-pill">${esc(c)}</span>`).join('')}</div>` : '<span class="muted">Pending speech verification</span>'}</td><td>${effectCell(s)}</td></tr>`).join('')}</tbody></table></div>` : '';
    $('document').innerHTML = r.document ? `<details ${!r.scenes.length ? 'open' : ''}><summary>Original HTML plan and visual references</summary><iframe title="Production plan with visual references" class="review-document" sandbox="" src="${esc(media(r.document))}?revision=${r.fingerprint}"></iframe></details>` : '';
    $('frames').innerHTML = r.frames.map(f => `<figure><a href="${esc(f.url)}" target="_blank" rel="noreferrer"><img loading="lazy" src="${esc(f.url)}" alt="Actual preview ${esc(f.id)}"></a><figcaption>${f.scene ? 'Scene ' + esc(f.scene) : esc(f.name)}${f.time !== null ? ' · ' + Number(f.time).toFixed(2) + 's' : ''}</figcaption>${feedback('frame', f.id, f.scene)}</figure>`).join('');
    $('audio').innerHTML = r.audioReview ? `<h2>Source voice and Nafay effects</h2><p>Review sample from ${Number(r.audioReview.start).toFixed(2)}s in the edited timeline.</p><audio controls preload="metadata" src="${esc(r.audioReview.url)}" aria-label="${esc(r.audioReview.label)}"></audio>` : audioPanel(r);
    displayed = r.id;
  }
  const pending = state.submissions.filter(s => s.status === 'pending');
  $('review-status').textContent = state.stale ? 'Content changed. The agent must publish a fresh review before approval. Your drafts are retained.' : pending.length ? `${pending.length} submission(s) saved for the editing agent. You can submit feedback on other scenes and frames independently.` : 'Review the current script, scenes and frames. Submit feedback or approve below.';
  $('history').innerHTML = state.submissions.slice().reverse().map(s => `<article class="feedback-event"><strong>${s.action === 'approve' ? 'Approval' : esc(s.scope || 'scene') + ' ' + esc(s.frame || s.scene || 'full script')}</strong><p>${esc(s.text)}</p><small>${s.status === 'pending' ? 'Pending' : esc(s.result)}${s.requestId !== r.id ? ' · earlier revision' : ''}</small></article>`).join('') || '<p>No submissions yet.</p>';
  const archived = [];
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k.startsWith(storagePrefix) && !k.startsWith(storagePrefix + r.id + ':') && localStorage.getItem(k)?.trim()) archived.push([k, localStorage.getItem(k)]);
    }
  } catch {}
  $('draft-history').innerHTML = archived.map(([k, v]) => `<article><small>${esc(k.slice(storagePrefix.length))}</small><p>${esc(v)}</p></article>`).join('') || '<p>No earlier drafts.</p>';
  controls();
}

async function refresh() {
  try {
    const response = await fetch(api), data = await response.json();
    if (!response.ok) throw Error(data.error);
    const subCountChanged = state && data.submissions?.length !== state.submissions?.length;
    state = data;
    connected = true;
    if (subCountChanged) displayed = '';
    render();
  } catch (error) {
    connected = false;
    $('review-status').textContent = error.message;
    controls();
  } finally {
    setTimeout(refresh, 5000);
  }
}

async function post(action, value) {
  const response = await fetch(api + '/' + action, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Dashboard-Action': 'review' },
    body: JSON.stringify(value)
  });
  const data = await response.json();
  if (!response.ok) throw Error(data.error);
  return data;
}

document.addEventListener('input', event => {
  const form = event.target.closest('.target-feedback');
  if (!form) return;
  try { localStorage.setItem(key(form.dataset.scope, form.dataset.target), event.target.value); } catch {}
  const savedSpan = form.querySelector('.saved-draft');
  if (savedSpan) savedSpan.textContent = event.target.value.trim() ? 'Draft saved on this device' : '';
  controls();
});

document.addEventListener('change', async event => {
  const musicSelect = event.target.closest('#music-select');
  if (musicSelect) {
    const val = musicSelect.value;
    const tracks = state?.catalogue?.filter(t => t.kind === 'music') || [];
    const active = tracks.find(t => t.id === val);
    const box = $('music-preview-box');
    const applyBtn = $('apply-music-btn');
    if (box) {
      if (active) {
        box.innerHTML = `
          <audio id="music-audio-player" controls preload="none" src="/audio/${encodeURIComponent(active.id)}" aria-label="Play ${esc(active.title)}"></audio>
          <p class="audio-meta"><strong>${esc(active.title)}</strong> · ${esc(active.moods.join(' · '))} · ${active.duration.toFixed(1)}s · <small>${esc(active.author)} · ${esc(active.license)}</small></p>
        `;
      } else {
        box.innerHTML = `<p class="muted">No background music selected.</p>`;
      }
    }
    if (applyBtn) {
      const currentMusic = state?.request?.audio?.music || 'none';
      applyBtn.dataset.music = val;
      if (val === currentMusic) {
        applyBtn.disabled = true;
        applyBtn.textContent = 'Selected';
      } else {
        applyBtn.disabled = false;
        applyBtn.textContent = 'Apply to reel';
      }
    }
    return;
  }

  const sfxSelect = event.target.closest('#sfx-select');
  if (sfxSelect) {
    const player = $('sfx-audio-player');
    if (player && sfxSelect.value) {
      player.src = `/audio/${encodeURIComponent(sfxSelect.value)}`;
      player.style.display = 'block';
      player.play().catch(() => {});
    }
    return;
  }

  const select = event.target.closest('.effect-dropdown');
  if (!select || sending) return;
  const scene = select.dataset.scene;
  const effectId = select.value;
  sending = true;
  controls();
  $('review-status').textContent = 'Updating scene effect…';
  try {
    const updated = await post('effect', {
      requestId: state.request.id,
      scene,
      effectId
    });
    state = updated;
    displayed = '';
    render();
    $('review-status').textContent = 'Effect updated.';
  } catch (error) {
    $('review-status').textContent = error.message;
  } finally {
    sending = false;
    controls();
  }
});

document.addEventListener('click', async event => {
  const button = event.target.closest('[data-music],[data-reading]');
  if (!button || sending) return;
  sending = true;
  controls();
  $('review-status').textContent = 'Applying your audio selection…';
  try {
    if (button.dataset.reading) {
      await post('voice', {requestId:state.request.id,scene:button.dataset.scene,auditionId:button.dataset.audition,take:button.dataset.reading});
    } else await post('music', { requestId: state.request.id, track: button.dataset.music === 'none' ? null : button.dataset.music });
    const response = await fetch(api);
    state = await response.json();
    displayed = '';
    render();
  } catch (error) {
    $('review-status').textContent = error.message;
  } finally {
    sending = false;
    controls();
  }
});

$('submit-all-feedback')?.addEventListener('click', async () => {
  if (sending || !state) return;
  const forms = [...document.querySelectorAll('.target-feedback')];
  const items = [];
  for (const form of forms) {
    const textarea = form.querySelector('textarea');
    const text = textarea?.value?.trim();
    if (text) {
      items.push({
        form,
        textarea,
        scope: form.dataset.scope,
        target: form.dataset.target,
        scene: form.dataset.scene,
        text
      });
    }
  }
  if (!items.length) return;
  sending = true;
  controls();
  $('review-status').textContent = `Submitting feedback (${items.length} item${items.length > 1 ? 's' : ''})…`;
  try {
    for (const item of items) {
      const value = await post('submit', {
        id: crypto.randomUUID(),
        requestId: state.request.id,
        action: 'feedback',
        scope: item.scope,
        scene: item.scene,
        frame: item.scope === 'frame' ? item.target : '',
        text: item.text
      });
      state.submissions.push(value);
      try { localStorage.removeItem(key(item.scope, item.target)); } catch {}
      item.textarea.value = '';
      const savedSpan = item.form.querySelector('.saved-draft');
      if (savedSpan) savedSpan.textContent = '';
    }
    displayed = '';
    render();
    $('review-status').textContent = `Feedback submitted (${items.length} item${items.length > 1 ? 's' : ''}).`;
  } catch (error) {
    $('review-status').textContent = error.message;
  } finally {
    sending = false;
    controls();
  }
});

$('approve').addEventListener('click', async () => {
  if (sending || !state) return;
  sending = true;
  controls();
  const isPlan = state?.request?.stage === 'plan';
  $('review-status').textContent = isPlan ? 'Submitting plan & generating actual preview frames…' : 'Submitting approval…';
  try {
    const textareas = [...document.querySelectorAll('.target-feedback textarea')];
    const items = textareas.map(t => {
      const form = t.closest('.target-feedback');
      return { id: crypto.randomUUID(), scope: form.dataset.scope, scene: form.dataset.scene || '', frame: form.dataset.frame || '', text: t.value.trim() };
    }).filter(i => i.text.length > 0);

    for (const item of items) {
      await post('submit', { ...item, requestId: state.request.id, action: 'feedback' });
    }
    const value = await post('submit', {
      id: crypto.randomUUID(),
      requestId: state.request.id,
      action: 'approve',
      resolvePending: true,
      text: ''
    });
    state.submissions.push(value);
    textareas.forEach(t => {
      const form = t.closest('.target-feedback');
      try { localStorage.removeItem(key(form.dataset.scope, form.dataset.target)); } catch {}
      t.value = '';
    });
    displayed = '';
    render();
    $('review-status').textContent = isPlan ? 'Plan approved! Generating actual preview frames and audio mix...' : (state.request.stage === 'frames' ? 'Frames and audio approved.' : 'Script approved.');
  } catch (error) {
    $('review-status').textContent = error.message;
  } finally {
    sending = false;
    controls();
  }
});

$('launch-studio').addEventListener('click', async () => {
  const button = $('launch-studio');
  button.disabled = true;
  try {
    const data = await post('studio', {});
    $('studio-link').href = data.url;
    $('studio-link').hidden = false;
    $('studio-status').textContent = 'Studio ready. Publish fresh actual frames after editing.';
  } catch (error) {
    $('studio-status').textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

if (kind !== 'plans') $('back-link').href = `/#${kind}/${encodeURIComponent(id)}/plan`;
refresh();
