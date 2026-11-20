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
const approvedScenes = new Set();

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
      <div class="feedback-btn-row">
        <button type="button" class="single-feedback-btn secondary" data-scope="${scope}" data-target="${esc(target)}" data-scene="${esc(scene)}">Submit feedback</button>
        <span class="saved-draft"></span>
      </div>
      ${badgeHtml}
    </div>
  `;
}

function projectLights(request) {
  const panel = request.projectLighting;
  if (!panel) return '';
  const editable = ['script', 'plan'].includes(request.stage);
  const active = panel.options.find(o => o.id === panel.selected);
  if (!editable) return `<h2>Project lighting</h2><p>${esc(active?.name || (panel.selected === 'none' ? 'Off' : panel.selected))}</p>`;
  const cards = panel.options.map(o =>
    `<label class="lighting-choice"><img src="${esc(o.image)}" alt="${esc(o.name)} example">
      <span><input type="radio" name="project-look" value="${esc(o.id)}" ${panel.selected === o.id ? 'checked' : ''}>
      <strong>${esc(o.name)}</strong><small>${esc(o.description)}</small></span></label>`).join('');
  const saved = !active && panel.selected !== 'none' ? `<p>Current preset · ${esc(panel.selected)}</p>` : '';
  return `<fieldset class="lighting-field"><legend>Project lighting</legend>
    <p>Choose once for every camera shot. Review the result on your footage before export.</p>
    <div class="lighting-options">${cards}</div>${saved}
    <label><input type="radio" name="project-look" value="none" ${panel.selected === 'none' ? 'checked' : ''}> Off</label></fieldset>`;
}

function effectCell(scene) {
  const effects = state.effectsCatalogue || [];
  const selectedId = scene.effects?.effects?.[0]?.id ? String(scene.effects.effects[0].id) : (scene.effects?.status === 'none' ? 'none' : '');
  const activeEffect = effects.find(e => e.id === selectedId);

  // Group effects by category
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

function updateStepper(stage, isExported, isApproved) {
  const s1 = $('step-1'), s2 = $('step-2'), s3 = $('step-3');
  const l1 = $('line-1'), l2 = $('line-2');
  if (!s1 || !s2 || !s3) return;

  [s1, s2, s3].forEach(el => el.classList.remove('active', 'completed', 'loading'));
  if (l1) l1.classList.remove('completed', 'loading');
  if (l2) l2.classList.remove('completed', 'loading');

  if (isExported || stage === 'exported') {
    s1.classList.add('completed');
    s1.querySelector('.step-num').textContent = '✓';
    s1.querySelector('.step-label').textContent = 'Initial plan';
    if (l1) l1.classList.add('completed');
    s2.classList.add('completed');
    s2.querySelector('.step-num').textContent = '✓';
    s2.querySelector('.step-label').textContent = 'Final plan';
    if (l2) l2.classList.add('completed');
    s3.classList.add('active', 'completed');
    s3.querySelector('.step-num').textContent = '✓';
    s3.querySelector('.step-label').textContent = 'Final release';
    if ($('sticky-step-badge')) $('sticky-step-badge').textContent = 'Step 3: Final release';
  } else if (stage === 'frames') {
    s1.classList.add('completed');
    s1.querySelector('.step-num').textContent = '✓';
    s1.querySelector('.step-label').textContent = 'Initial plan';
    if (l1) l1.classList.add('completed');

    if (isApproved) {
      s2.classList.add('completed');
      s2.querySelector('.step-num').textContent = '✓';
      s2.querySelector('.step-label').textContent = 'Final plan';
      if (l2) l2.classList.add('completed', 'loading');
      s3.classList.add('active', 'loading');
      s3.querySelector('.step-num').innerHTML = '<span class="step-spinner"></span>';
      s3.querySelector('.step-label').textContent = 'Rendering release…';
      if ($('sticky-step-badge')) $('sticky-step-badge').textContent = 'Step 3: Rendering export';
    } else {
      s2.classList.add('active');
      s2.querySelector('.step-num').textContent = '2';
      s2.querySelector('.step-label').textContent = 'Final plan';
      s3.querySelector('.step-num').textContent = '3';
      s3.querySelector('.step-label').textContent = 'Final release';
      if ($('sticky-step-badge')) $('sticky-step-badge').textContent = 'Step 2: Final plan';
    }
  } else {
    // stage === 'plan' or 'script'
    if (isApproved) {
      s1.classList.add('completed');
      s1.querySelector('.step-num').textContent = '✓';
      s1.querySelector('.step-label').textContent = 'Initial plan';
      if (l1) l1.classList.add('completed', 'loading');
      s2.classList.add('active', 'loading');
      s2.querySelector('.step-num').innerHTML = '<span class="step-spinner"></span>';
      s2.querySelector('.step-label').textContent = 'Generating previews…';
      s3.querySelector('.step-num').textContent = '3';
      s3.querySelector('.step-label').textContent = 'Final release';
      if ($('sticky-step-badge')) $('sticky-step-badge').textContent = 'Step 2: Generating previews';
    } else {
      s1.classList.add('active');
      s1.querySelector('.step-num').textContent = '1';
      s1.querySelector('.step-label').textContent = 'Initial plan';
      s2.querySelector('.step-num').textContent = '2';
      s2.querySelector('.step-label').textContent = 'Final plan';
      s3.querySelector('.step-num').textContent = '3';
      s3.querySelector('.step-label').textContent = 'Final release';
      if ($('sticky-step-badge')) $('sticky-step-badge').textContent = 'Step 1: Initial plan';
    }
  }
}

function updateSceneApprovalButtons() {
  const isApproved = Boolean(state?.submissions?.some(s => s.action === 'approve' && s.requestId === state.request?.id));
  const isExported = Boolean(state?.request?.isExported || state?.request?.stage === 'exported');
  const total = state?.request?.scenes?.length || 0;
  const count = approvedScenes.size;
  document.querySelectorAll('.scene-approve-btn').forEach(btn => {
    const sc = btn.dataset.scene;
    if (approvedScenes.has(sc)) {
      btn.classList.add('approved');
      btn.textContent = `✓ Scene ${sc} Approved`;
    } else {
      btn.classList.remove('approved');
      btn.textContent = `Approve Scene ${sc}`;
    }
  });

  const statusEl = $('sticky-status-text');
  if (statusEl) {
    if (isExported) {
      statusEl.textContent = '✓ Final release exported and ready!';
    } else if (isApproved) {
      if (state?.request?.stage === 'frames') {
        statusEl.textContent = '✓ Final plan approved! Rendering 4K release export...';
      } else {
        statusEl.textContent = '✓ Initial plan approved. Agent is generating preview frames & effects...';
      }
    } else if (count === total && total > 0) {
      statusEl.textContent = `All ${total} scenes approved! Ready to submit.`;
    } else if (count > 0) {
      statusEl.textContent = `${count} of ${total} scenes approved`;
    } else {
      statusEl.textContent = state?.request?.stage === 'frames' ? 'Reviewing final frames & effects' : 'Reviewing initial plan';
    }
  }
}

function controls() {
  const stage = state?.request?.stage;
  const isExported = Boolean(state?.request?.isExported || stage === 'exported');
  const isApproved = Boolean(state?.submissions?.some(s => s.action === 'approve' && s.requestId === state.request?.id));
  const blocked = sending || !connected || !state || state.stale || isApproved || isExported;
  const textareas = [...document.querySelectorAll('.target-feedback textarea')];
  const hasFeedbackText = textareas.some(t => t.value.trim().length > 0);
  const isPlan = stage === 'plan' || stage === 'script';

  if ($('submit-all-feedback')) {
    $('submit-all-feedback').disabled = Boolean(blocked || !hasFeedbackText);
  }
  if ($('sticky-submit-feedback')) {
    $('sticky-submit-feedback').disabled = Boolean(blocked || !hasFeedbackText);
  }

  let approveText = '';
  if (isExported) {
    approveText = '✓ Release Exported';
  } else if (isApproved) {
    if (isPlan) {
      approveText = '✓ Plan Approved · Generating Previews…';
    } else {
      approveText = '✓ Final Plan Approved · Rendering…';
    }
  } else if (isPlan) {
    approveText = hasFeedbackText ? 'Submit feedback & update plan' : 'Approve initial plan';
  } else if (stage === 'frames') {
    approveText = hasFeedbackText ? 'Submit feedback & update frames' : 'Approve final plan';
  } else {
    approveText = 'Approve current plan';
  }

  const approveButtons = [$('approve'), $('sticky-approve')].filter(Boolean);
  approveButtons.forEach(btn => {
    if (isApproved && !isExported) {
      btn.innerHTML = `<span class="btn-spinner"></span> ${esc(approveText)}`;
      btn.disabled = true;
      btn.classList.add('btn-processing');
    } else {
      btn.textContent = approveText;
      btn.disabled = Boolean(blocked || isApproved || isExported);
      btn.classList.remove('btn-processing');
    }
  });

  document.querySelectorAll('[data-music],[data-reading]').forEach(button => {
    button.disabled = Boolean(blocked);
  });
  document.querySelectorAll('.effect-dropdown, input[name="project-look"]').forEach(select => {
    select.disabled = Boolean(blocked);
  });
  document.querySelectorAll('.single-feedback-btn').forEach(btn => {
    btn.disabled = Boolean(isApproved || isExported || sending);
  });
}

function readings(scene) {
  if (!scene.audition) return scene.voice === 'kokoro' ? '<small>Selected Kokoro narration</small>' : '';
  return ['A', 'B'].map(key => `<div><audio controls preload="none" src="${esc(scene.audition.takes[key])}" aria-label="Scene ${esc(scene.id)} reading ${key}"></audio>
    <button type="button" data-reading="${key}" data-scene="${esc(scene.id)}" data-audition="${esc(scene.audition.id)}">Use reading ${key}</button></div>`).join('');
}

function renderFinalPlanScenes(r) {
  if (!r.scenes?.length) return '';
  return `
    <h2>Scene-by-scene final plan & frames</h2>
    <p class="review-note">Check the dialogue and actual frame with applied effect for each scene. Approve each scene or submit feedback.</p>
    <div class="final-plan-cards">
      ${r.scenes.map(s => {
        const sceneFrames = r.frames.filter(f => f.scene === s.id);
        const keyFrame = sceneFrames[Math.floor(sceneFrames.length / 2)] || sceneFrames[0] || null;
        let effectTitle = 'Standard framing';
        if (s.effects?.effects?.[0]?.id) {
          const ef = state.effectsCatalogue?.find(e => e.id === String(s.effects.effects[0].id));
          effectTitle = `#${s.effects.effects[0].id} · ${ef?.name || 'Vibha effect'}`;
        } else if (s.finish) {
          effectTitle = s.finish;
        }

        const priorFeedback = (state?.submissions || []).filter(sub => sub.scene === s.id && sub.action === 'feedback');
        const isApproved = approvedScenes.has(s.id);

        return `
          <article class="final-scene-card" data-scene="${esc(s.id)}">
            <div class="final-scene-header">
              <div>
                <span class="scene-badge">SCENE ${esc(s.id)}</span>
                <span class="scene-timing-badge">${s.timeline ? s.timeline.map(n => Number(n).toFixed(2)).join('–') + 's' : ''}</span>
              </div>
              <button type="button" class="scene-approve-btn ${isApproved ? 'approved' : ''}" data-scene="${esc(s.id)}">
                ${isApproved ? '✓ Scene ' + esc(s.id) + ' Approved' : 'Approve Scene ' + esc(s.id)}
              </button>
            </div>

            <div class="final-scene-body">
              <div class="final-scene-meta">
                <div class="dialogue-box">
                  <label class="meta-label">Spoken dialogue:</label>
                  <p class="final-dialogue-text">"${esc(s.text)}"</p>
                </div>
                <div class="effect-box">
                  <label class="meta-label">Applied visual effect:</label>
                  <p class="final-effect-text"><strong>${esc(effectTitle)}</strong></p>
                </div>
                ${priorFeedback.length ? `
                  <div class="scene-history-box">
                    <label class="meta-label">Feedback addressed from earlier revision:</label>
                    ${priorFeedback.map(item => `
                      <div class="history-item">
                        <span class="history-status">${esc(item.status || 'handled')}</span>
                        <p>${esc(item.text)}</p>
                      </div>
                    `).join('')}
                  </div>
                ` : ''}
              </div>

              <div class="final-scene-preview">
                <label class="meta-label">Actual preview frame with effect:</label>
                ${keyFrame ? `
                  <a href="${esc(keyFrame.url)}" target="_blank" rel="noreferrer" title="Click to view full size">
                    <img class="final-preview-img" src="${esc(keyFrame.url)}" alt="Actual frame for scene ${esc(s.id)} with effect">
                  </a>
                  <span class="preview-caption">1 keyframe shown · click to view full size</span>
                ` : `
                  <p class="muted">Actual frame generating…</p>
                `}
              </div>
            </div>

            <div class="final-scene-feedback-wrap">
              ${feedback('scene', s.id, s.id, `Scene ${s.id}`)}
            </div>
          </article>
        `;
      }).join('')}
    </div>
  `;
}

function render() {
  const r = state.request;
  const isApproved = Boolean(state.submissions?.some(s => s.action === 'approve' && s.requestId === r.id));
  const isExported = Boolean(r.isExported || r.stage === 'exported');

  $('title').textContent = r.title;
  $('stage').textContent = isExported ? 'STEP 3: FINAL RELEASE' : r.stage === 'frames' ? 'FINAL PLAN & ACTUAL FRAMES' : r.stage === 'script' ? 'SCRIPT AND SHOOTING PLAN' : 'INITIAL PRODUCTION PLAN';
  $('revision').textContent = `Revision ${r.id.slice(0, 8)} · ${new Date(r.createdAt).toLocaleString()}`;
  $('native-studio').hidden = !state.studioAvailable;

  updateStepper(r.stage, isExported, isApproved);

  const bannerEl = $('status-banner');
  if (bannerEl) {
    if (isExported) {
      bannerEl.innerHTML = `
        <div class="final-release-box">
          <div class="release-header-row">
            <div>
              <span class="release-status-badge">✓ STEP 3: FINAL RELEASE READY</span>
              <h2>Exported 4K Video</h2>
              <p class="release-desc">All approved scenes, dialogue, captions, and visual effects have been baked into the final release.</p>
            </div>
            ${r.exportInfo?.videoUrl ? `<a href="${esc(r.exportInfo.videoUrl)}" download class="button primary release-download-btn">⬇ Download Final Video</a>` : ''}
          </div>
          ${r.exportInfo?.videoUrl ? `
            <div class="release-video-wrapper">
              <video controls playsinline preload="metadata" class="final-release-video" src="${esc(r.exportInfo.videoUrl)}"></video>
            </div>
          ` : ''}
          <div class="release-meta-bar">
            <span class="spec-tag accent">4K UHD</span>
            <span class="spec-tag">${r.outputProfile?.width || 2160}×${r.outputProfile?.height || 3840}</span>
            <span class="spec-tag">${r.outputProfile?.fps || '60'} FPS</span>
            ${r.exportInfo?.duration ? `<span class="spec-tag">${Number(r.exportInfo.duration).toFixed(2)}s duration</span>` : ''}
          </div>
        </div>
      `;
    } else if (isApproved) {
      bannerEl.innerHTML = `
        <div class="approval-working-banner">
          <span class="banner-spinner"></span>
          <div>
            <strong>${r.stage === 'frames' ? 'Final plan approved · Rendering in progress' : 'Initial plan approved · Generating previews'}</strong>
            <p>${r.stage === 'frames' ? 'The editing agent is rendering the final 4K video export and packaging assets. This page updates automatically.' : 'The editing agent is generating actual preview frames with your applied effects. This page updates automatically.'}</p>
          </div>
        </div>
      `;
    } else {
      bannerEl.innerHTML = '';
    }
  }

  if (displayed !== r.id) {
    const quality = r.outputProfile;
    $('quality').innerHTML = quality ? `<div class="spec-tags-row"><span class="spec-tag">${quality.width > quality.height ? 'Landscape' : 'Portrait'}</span><span class="spec-tag accent">${Math.min(quality.width, quality.height) === 2160 ? '4K UHD' : Math.min(quality.width, quality.height) === 1080 ? '1080p HD' : ''}</span><span class="spec-tag">${quality.width}×${quality.height}</span><span class="spec-tag">${quality.fps} FPS</span></div>` : 'Output quality will be confirmed from the recordings.';
    // Crop notice removed as requested
    $('crop').textContent = '';

    if (r.stage === 'frames') {
      // Step 2: Final plan with 1 key actual preview frame per scene, dialogue and effect
      $('script').innerHTML = feedback('script', '', '', 'overall final plan');
      $('project-lighting').innerHTML = '';
      $('scene-summary').innerHTML = renderFinalPlanScenes(r);
      $('frames-panel').hidden = true;
      if ($('audio')) $('audio').hidden = true;
      if ($('final-plan-history')) $('final-plan-history').hidden = false;
    } else {
      // Step 1: Initial plan with full script and production plan table
      $('script').innerHTML = `<h2>Full script</h2><div class="script-card">${r.scenes.map(s => `<p class="script-line"><strong class="script-scene-num">Scene ${esc(s.id)}</strong> <span class="script-text">${esc(s.text)}</span></p>`).join('')}</div>${feedback('script')}${r.referenceStyle ? `<aside><h3>Reference style · ${esc(r.referenceStyle.name)}</h3><p>${esc(r.referenceStyle.summary)}</p><p>Style notes guide the proposed scene treatments. Review their actual appearance in the frames below.</p></aside>` : ''}`;
      $('project-lighting').innerHTML = projectLights(r);
      $('scene-summary').innerHTML = r.scenes.length ? `<h2>Scene-by-scene production plan</h2><div class="table-scroll"><table><thead><tr><th class="col-time">Scene / timing</th><th class="col-dialogue">Dialogue</th><th class="col-footage">Footage / shooting notes</th><th class="col-captions">Spoken captions</th><th class="col-effects">Effects</th></tr></thead><tbody>${r.scenes.map(s => `<tr><td><strong class="scene-id">Scene ${esc(s.id)}</strong><span class="scene-timing-badge">${s.timeline ? s.timeline.map(n => Number(n).toFixed(2)).join('–') + 's' : 'Record after approval'}</span><div style="margin-top:10px;"><button type="button" class="scene-approve-btn ${approvedScenes.has(s.id) ? 'approved' : ''}" data-scene="${esc(s.id)}">${approvedScenes.has(s.id) ? '✓ Scene ' + esc(s.id) + ' Approved' : 'Approve Scene ' + esc(s.id)}</button></div></td><td><p class="scene-dialogue-text">${esc(s.text)}</p>${readings(s)}${feedback('scene', s.id, s.id)}</td><td><strong class="footage-name">${esc(s.source)}</strong>${s.shootingNote ? `<p class="shooting-note">${esc(s.shootingNote)}</p>` : ''}${s.sourceFrame ? `<img class="source-frame" src="${esc(s.sourceFrame)}" alt="Original scene ${esc(s.id)} before effects">` : ''}</td><td>${s.captions?.length ? `<div class="caption-pages-wrap">${s.captions.map(c => `<span class="caption-pill">${esc(c)}</span>`).join('')}</div>` : '<span class="muted">Pending speech verification</span>'}</td><td>${effectCell(s)}</td></tr>`).join('')}</tbody></table></div>` : '';
      $('frames-panel').hidden = true;
      if ($('audio')) $('audio').hidden = true;
      if ($('final-plan-history')) $('final-plan-history').hidden = true;
    }

    if (r.comparison) {
      $('lighting-comparison').innerHTML = `<p>Original on the left · Studio lighting on the right</p><video controls playsinline preload="metadata" style="width:100%;max-height:65vh" aria-label="Lighting comparison with recorded audio" src="${esc(r.comparison)}"></video>`;
      $('frames-panel').hidden = false;
    }

    displayed = r.id;
  }

  const pending = state.submissions.filter(s => s.status === 'pending');
  let statusMsg = '';
  if (state.stale) {
    statusMsg = 'Content changed. Publish a fresh review before approval.';
  } else if (isExported) {
    statusMsg = '✓ Final release exported and ready. You can watch the full video above.';
  } else if (isApproved) {
    statusMsg = r.stage === 'frames'
      ? '✓ Final plan approved! Rendering 4K release export. This page updates automatically.'
      : '✓ Initial plan approved! Generating actual preview frames and effects. This page updates automatically.';
  } else if (pending.length) {
    statusMsg = `${pending.length} feedback item(s) submitted for the editing agent.`;
  } else {
    statusMsg = 'Review the current script, scenes and preview frames. Submit feedback or approve this plan.';
  }
  $('review-status').textContent = statusMsg;

  if ($('history')) {
    $('history').innerHTML = state.submissions.slice().reverse().map(s => `<article class="feedback-event"><strong>${s.action === 'approve' ? 'Approval' : esc(s.scope || 'scene') + ' ' + esc(s.frame || s.scene || 'full script')}</strong><p>${esc(s.text)}</p><small>${s.status === 'pending' ? 'Pending' : esc(s.result)}${s.requestId !== r.id ? ' · earlier revision' : ''}</small></article>`).join('') || '<p>No submissions yet.</p>';
  }

  updateSceneApprovalButtons();
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
  if (event.target.name === 'project-look' && !sending) {
    sending = true;
    controls();
    const drafts = [...document.querySelectorAll('.target-feedback')].map(form => ({
      ...form.dataset, text: form.querySelector('textarea').value
    }));
    try {
      const updated = await post('lighting', { requestId: state.request.id, look: event.target.value });
      state = { ...state, ...updated, stale: false };
      for (const item of drafts) {
        if (item.text) localStorage.setItem(key(item.scope, item.target), item.text);
      }
      displayed = '';
      render();
    } catch (error) {
      displayed = '';
      render();
      $('review-status').textContent = error.message;
    } finally {
      sending = false;
      controls();
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
    state = { ...state, ...updated };
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
  // Single feedback button per scene/script/frame
  const singleBtn = event.target.closest('.single-feedback-btn');
  if (singleBtn && !sending) {
    const scope = singleBtn.dataset.scope || 'scene';
    const target = singleBtn.dataset.target || '';
    const scene = singleBtn.dataset.scene || '';
    const form = singleBtn.closest('.target-feedback');
    const textarea = form?.querySelector('textarea');
    const text = textarea?.value?.trim();
    if (!text) return;

    sending = true;
    controls();
    singleBtn.disabled = true;
    singleBtn.textContent = 'Submitting…';
    $('review-status').textContent = `Submitting feedback for ${scope === 'script' ? 'script' : 'scene ' + scene}…`;
    try {
      const value = await post('submit', {
        id: crypto.randomUUID(),
        requestId: state.request.id,
        action: 'feedback',
        scope,
        scene,
        frame: scope === 'frame' ? target : '',
        text
      });
      state.submissions.push(value);
      try { localStorage.removeItem(key(scope, target)); } catch {}
      if (textarea) textarea.value = '';
      const savedSpan = form?.querySelector('.saved-draft');
      if (savedSpan) savedSpan.textContent = '';
      displayed = '';
      render();
      $('review-status').textContent = `Feedback submitted for ${scope === 'script' ? 'script' : 'scene ' + scene}.`;
    } catch (error) {
      $('review-status').textContent = error.message;
    } finally {
      sending = false;
      controls();
    }
    return;
  }

  // Scene approve button
  const approveBtn = event.target.closest('.scene-approve-btn');
  if (approveBtn) {
    const sceneId = approveBtn.dataset.scene;
    if (approvedScenes.has(sceneId)) {
      approvedScenes.delete(sceneId);
    } else {
      approvedScenes.add(sceneId);
    }
    updateSceneApprovalButtons();
    return;
  }

  const voiceBtn = event.target.closest('[data-reading]');
  if (voiceBtn && !sending) {
    sending = true;
    controls();
    $('review-status').textContent = 'Applying your voice reading…';
    try {
      await post('voice', { requestId: state.request.id, scene: voiceBtn.dataset.scene, auditionId: voiceBtn.dataset.audition, take: voiceBtn.dataset.reading });
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
  }
});

// Submit all feedback
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

// Sticky submit feedback button
$('sticky-submit-feedback')?.addEventListener('click', () => {
  $('submit-all-feedback')?.click();
});

// Approve plan / final plan
$('approve')?.addEventListener('click', async () => {
  if (sending || !state) return;
  sending = true;
  controls();
  const isPlan = state?.request?.stage === 'plan' || state?.request?.stage === 'script';
  $('review-status').textContent = isPlan ? 'Approving initial plan & generating actual preview frames…' : 'Submitting final plan approval…';
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
    $('review-status').textContent = isPlan ? 'Initial plan approved! Generating actual preview frames and effects...' : 'Final plan approved! Ready for export.';
  } catch (error) {
    $('review-status').textContent = error.message;
  } finally {
    sending = false;
    controls();
  }
});

// Sticky approve button
$('sticky-approve')?.addEventListener('click', () => {
  $('approve')?.click();
});

$('launch-studio')?.addEventListener('click', async () => {
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

if (kind !== 'plans' && $('back-link')) $('back-link').href = `/#${kind}/${encodeURIComponent(id)}/plan`;
refresh();
