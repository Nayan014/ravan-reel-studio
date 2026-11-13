import { createHash, randomUUID } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync, renameSync } from 'node:fs';
import { isAbsolute, relative } from 'node:path';
import { mediaPath, mediaUrl } from './dashboard-library.mjs';
import { ReviewError, readReview, recordVisualEdit, saveDraftDesign } from './review-store.mjs';

const digest = bytes => createHash('sha256').update(bytes).digest('hex');

export function validateLayers(layers) {
  if (!Array.isArray(layers) || layers.length > 12) throw new ReviewError('Use at most 12 text layers per scene.');
  const ids = new Set();
  return layers.map(layer => {
    if (!layer || !/^[A-Za-z0-9_-]{1,64}$/.test(layer.id || '') || ids.has(layer.id)) throw new ReviewError('Text layers need distinct identifiers.');
    ids.add(layer.id);
    if (typeof layer.text !== 'string' || !layer.text.trim() || layer.text.length > 400) throw new ReviewError('Each text layer needs 1–400 characters.');
    if (!/^#[a-f0-9]{6}$/i.test(layer.color || '')) throw new ReviewError('Choose a valid text colour.');
    if (!Number.isFinite(layer.fontSize) || layer.fontSize < 16 || layer.fontSize > 240) throw new ReviewError('Text size must be between 16 and 240 pixels.');
    if (!Number.isFinite(layer.x) || !Number.isFinite(layer.y) || layer.x < 0 || layer.x > .9 || layer.y < 0 || layer.y > .95) throw new ReviewError('Text position must be inside the portrait canvas.');
    return { id: layer.id, text: layer.text, color: layer.color.toLowerCase(), fontSize: layer.fontSize, x: layer.x, y: layer.y };
  });
}

function source(root, kind, id) {
  if (!['reels', 'edits'].includes(kind)) return null;
  const base = `outputs/${kind}/${id}`;
  let name = `${base}/plan.json`;
  if (kind === 'edits') {
    const session = JSON.parse(readFileSync(mediaPath(root, `${base}/session.json`), 'utf8'));
    if (!session.plan) return null;
    name = isAbsolute(session.plan) ? relative(root, session.plan).split('\\').join('/') : session.plan.startsWith('outputs/') ? session.plan : `${base}/${session.plan}`;
    if (!name.startsWith(base + '/')) throw new ReviewError('The effect plan is outside this session.');
  }
  const path = mediaPath(root, name), bytes = readFileSync(path);
  return { path, data: JSON.parse(bytes), revision: digest(bytes), base };
}

export function readVisual(root, kind, id) {
  if (kind==='plans') {
    const state=readReview(root,kind,id),design=state.design||{};
    return {revision:digest(JSON.stringify(design)),scenes:state.request.scenes.map(s=>({...s,layers:validateLayers(design[s.id]||[]),background:null}))};
  }
  const doc = source(root, kind, id);
  if (!doc) return { revision: null, scenes: [] };
  const scenes = kind === 'reels' ? (doc.data.shots || []).map(s => ({ id: String(s.id), text: s.say || s.expected_say || '', layers: s.text_layers || [], source: s.source_frame })) : [{ id: 'clip', text: 'Entire clip', layers: doc.data.text_layers || [] }];
  return { revision: doc.revision, scenes: scenes.map(s => {
    let background = null;
    if (typeof s.source === 'string') {
      const name = `${doc.base}/${s.source}`;
      try { mediaPath(root, name); background = mediaUrl(name); } catch {}
    }
    return { id: s.id, text: String(s.text), layers: validateLayers(s.layers), background };
  }) };
}

export function saveVisual(root, kind, id, value) {
  const review = readReview(root, kind, id);
  if (value?.requestId !== review.request.id) throw new ReviewError('This review changed. Reload it before saving.', 409);
  if (kind==='plans') {
    const submission=saveDraftDesign(root,id,value,validateLayers(value.layers));
    return {visual:readVisual(root,kind,id),submission};
  }
  const doc = source(root, kind, id);
  if (!doc || doc.revision !== value.revision) throw new ReviewError('The scene changed elsewhere. Reload before saving your edits.', 409);
  const layers = validateLayers(value.layers);
  if (kind === 'reels') {
    const shot = doc.data.shots.find(s => String(s.id) === value.scene);
    if (!shot) throw new ReviewError('Scene not found.');
    shot.text_layers = layers;
  } else {
    if (value.scene !== 'clip') throw new ReviewError('Choose the entire clip.');
    doc.data.text_layers = layers;
  }
  const temp = `${doc.path}.${randomUUID()}.tmp`;
  writeFileSync(temp, JSON.stringify(doc.data, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
  renameSync(temp, doc.path);
  const submission = recordVisualEdit(root, kind, id, review.request.id, value.scene);
  return { visual: readVisual(root, kind, id), submission };
}
