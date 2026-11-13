import { existsSync, lstatSync, readdirSync, readFileSync, realpathSync, statSync } from 'node:fs';
import { basename, extname, isAbsolute, join, relative, resolve, sep } from 'node:path';

export const mediaTypes = {
  '.html': 'text/html; charset=utf-8', '.json': 'application/json',
  '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8',
  '.log': 'text/plain; charset=utf-8', '.srt': 'text/plain; charset=utf-8', '.vtt': 'text/vtt',
  '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.m4v': 'video/mp4', '.webm': 'video/webm',
  '.mkv': 'video/x-matroska', '.avi': 'video/x-msvideo',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.pdf': 'application/pdf',
};
const video = /\.(mp4|mov|m4v|webm|mkv|avi)$/i;
const image = /\.(png|jpe?g|webp|gif|svg)$/i;
const ignored = new Set(['node_modules', '__pycache__', 'voicestudio', 'models']);
const categories = new Set(['raw', 'assets', 'working', 'previews', 'analysis', 'renders', 'export', 'publishing']);
export const validId = id => /^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(id);
const inside = (base, path) => path.startsWith(base + sep);
const slash = path => path.split(sep).join('/');

/** One boundary for both discovery and HTTP. No symlinked files or directories are served. */
export function mediaPath(root, name) {
  if (typeof name !== 'string' || name.includes('\\') || name.includes('\0') || isAbsolute(name)) throw Error('Invalid path');
  const parts = name.split('/');
  if (parts.some(p => !p || p === '.' || p.startsWith('.') || ignored.has(p))) throw Error('Invalid path');
  const [top, group, id] = parts;
  const projectMedia = top === 'outputs' && ['reels', 'edits'].includes(group) && validId(id || '') && parts.length >= 4;
  const inputMedia = top === 'inputs' && parts.length >= 2 && (video.test(name) || image.test(name) || /\.(wav|mp3|m4a)$/i.test(name));
  const reference = (name.startsWith('skills/effects/assets/reference-previews/') || name.startsWith('docs/effect-gallery/')) && image.test(name);
  if (!projectMedia && !inputMedia && !reference) throw Error('Outside media locations');
  if (!mediaTypes[extname(name).toLowerCase()]) throw Error('Unsupported file');
  const base = realpathSync(root);
  let path = base;
  for (const part of parts) {
    path = join(path, part);
    if (lstatSync(path).isSymbolicLink()) throw Error('Symlinks are not served');
  }
  path = realpathSync(path);
  if (!inside(base, path) || !statSync(path).isFile()) throw Error('Missing media');
  return path;
}

export const mediaUrl = name => '/media/' + name.split('/').map(encodeURIComponent).join('/');

function readRecord(path, warnings) {
  if (!existsSync(path)) return null;
  try {
    if (lstatSync(path).isSymbolicLink() || statSync(path).size > 2 * 1024 * 1024) throw Error('Invalid metadata');
    const data = JSON.parse(readFileSync(path, 'utf8'));
    if (!data || Array.isArray(data) || typeof data !== 'object') throw Error('Expected an object');
    return data;
  } catch { warnings.push(`Cannot read ${basename(path)}.`); return null; }
}

function directories(path) {
  try { return readdirSync(path, { withFileTypes: true }).filter(e => e.isDirectory() && validId(e.name)); }
  catch { return []; }
}

function projectData(root, kind, id) {
  const local = `outputs/${kind}/${id}`, folder = join(root, local), warnings = [];
  const record = name => readRecord(join(folder, name), warnings);
  const plan = record('plan.json'), session = kind === 'edits' ? record('session.json') : null;
  const exported = record('export.json'), preview = record('preview.json');
  const approval = record('approval.json'), checks = record('checks.json'), selfReview = record('self-review.json');
  const provenance = record('Provenance.json');
  const files = new Map();
  const add = path => {
    try {
      const rel = slash(relative(root, path));
      const safe = mediaPath(root, rel), info = statSync(safe);
      if (!files.has(rel)) files.set(rel, {
        path: rel, name: slash(relative(folder, safe)), url: mediaUrl(rel),
        size: info.size, modified: info.mtime.toISOString(),
        type: video.test(rel) ? 'video' : image.test(rel) ? 'image' : 'document',
      });
      return files.get(rel);
    } catch { return null; }
  };
  const walk = (path, depth = 0) => {
    if (depth > 8) return;
    let entries;
    try { entries = readdirSync(path, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (e.name.startsWith('.') || ignored.has(e.name) || e.isSymbolicLink()) continue;
      const target = join(path, e.name);
      if (e.isDirectory()) {
        if (depth || categories.has(e.name) || /^preview-/.test(e.name)) walk(target, depth + 1);
      } else if (e.isFile() && mediaTypes[extname(e.name).toLowerCase()]) add(target);
    }
  };
  walk(folder);
  // Legacy records use either absolute paths, studio-relative paths or project-relative paths.
  const referenced = (name, label, allowInput = false, type) => {
    if (typeof name !== 'string' || !name) return null;
    let target = isAbsolute(name) ? resolve(name) : resolve(name.startsWith('outputs/') || name.startsWith('inputs/') ? root : folder, name);
    const inProject = inside(folder, target);
    const inInputs = allowInput && inside(join(root, 'inputs'), target);
    const found = (inProject || inInputs) ? add(target) : null;
    if (!found) warnings.push(`${label} is missing or outside this project's media locations.`);
    else if (type && found.type !== type) { warnings.push(`${label} is not a ${type} file.`); return null; }
    return found;
  };
  const explicitVideo = referenced(session?.render || exported?.file, 'Recorded export', false, 'video');
  const source = referenced(session?.source, 'Original recording', true);
  const explicitCover = referenced(typeof exported?.cover === 'string' ? exported.cover : exported?.cover?.png || exported?.cover?.jpg, 'Recorded cover', false, 'image');
  const explicitReview = referenced(preview?.review, 'Recorded frame review');
  const frameRecord = session?.preview || preview;
  const recordedFrames = (Array.isArray(frameRecord?.frames) ? frameRecord.frames : Array.isArray(frameRecord?.files) ? frameRecord.files : [])
    .filter(v => typeof v === 'string' && image.test(v)).map(p => referenced(p, 'Recorded preview')).filter(Boolean);
  if (session?.preview?.overview) referenced(session.preview.overview, 'Preview contact sheet');
  if (session?.plan) referenced(session.plan, 'Effect plan');
  const all = [...files.values()].sort((a, b) => b.modified.localeCompare(a.modified) || a.name.localeCompare(b.name));
  const exports = all.filter(f => f.type === 'video' && (/^(export|renders)\/[^/]+$/.test(f.name) || !f.name.includes('/')));
  if (explicitVideo && !exports.includes(explicitVideo)) exports.unshift(explicitVideo);
  const primary = explicitVideo || exports[0] || null;
  const covers = all.filter(f => f.type === 'image' && /(?:cover|thumbnail)/i.test(basename(f.name)) && !/(?:source|contact|snapshot)/i.test(f.name));
  if (explicitCover && !covers.includes(explicitCover)) covers.unshift(explicitCover);
  const cover = explicitCover || [...covers].sort((a, b) => Number(/\.png$/i.test(b.name)) - Number(/\.png$/i.test(a.name)) || b.modified.localeCompare(a.modified))[0] || null;
  const captions = all.filter(f => /\.(md|txt)$/i.test(f.name) && /(?:captions?|social[_ -]?copy)/i.test(basename(f.name))).map(f => {
    try {
      if (f.size > 256 * 1024) throw Error('Too large');
      return { ...f, text: readFileSync(mediaPath(root, f.path), 'utf8') };
    } catch { warnings.push(`Cannot display ${f.name}.`); return { ...f, text: '' }; }
  });
  const plans = all.filter(f => /(?:^|\/)(?:review|plan)\.html$/i.test(f.name));
  if (explicitReview && !plans.includes(explicitReview)) plans.push(explicitReview);
  const previews = recordedFrames.length ? recordedFrames : all.filter(f => f.type === 'image' && /^(previews\/|preview-|analysis\/|working\/analysis\/)/.test(f.name));
  const records = [
    ['Workflow stage', session ? { stage: session.stage } : null],
    ['Saved approval', approval || session?.approval], ['Saved checks', checks],
    ['Saved self-review', selfReview], ['Export record', exported], ['Package provenance', provenance],
  ].filter(([, data]) => data).map(([label, data]) => ({ label, data }));
  const title = typeof plan?.title === 'string' ? plan.title : session?.source ? basename(String(session.source), extname(String(session.source))) : id.replace(/[-_]/g, ' ');
  return {
    id, kind, title, path: local, updated: all[0]?.modified || statSync(folder).mtime.toISOString(),
    status: session?.stage ? String(session.stage).replace(/_/g, ' ') : primary ? 'export available' : plan ? 'planning' : 'files available',
    renderer: typeof plan?.renderer === 'string' ? plan.renderer : kind === 'edits' ? 'Vibha effects' : plan ? 'remotion' : null,
    primary, cover, covers, exports, captions, plans, previews, source, files: all, records, warnings: [...new Set(warnings)],
  };
}

export function listProjects(root) {
  root = realpathSync(root);
  return ['reels', 'edits'].flatMap(kind => {
    const parent = join(root, 'outputs', kind);
    // Do not follow a symlink used in place of outputs/ or one of its libraries.
    try {
      if (lstatSync(join(root, 'outputs')).isSymbolicLink() || lstatSync(parent).isSymbolicLink()) return [];
    } catch { return []; }
    return directories(parent).flatMap(entry => {
      try {
        const data = projectData(root, kind, entry.name);
        return data.files.length || data.warnings.length ? [data] : [];
      } catch { return []; }
    });
  }).sort((a, b) => b.updated.localeCompare(a.updated) || a.id.localeCompare(b.id));
}
