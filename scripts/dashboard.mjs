// Adapted from Techno Reel by Nayan V. See ../dashboard/LICENSE.
import { createServer } from 'node:http';
import {createHash} from 'node:crypto';
import { createReadStream, realpathSync, statSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { basename, dirname, extname, join, resolve, win32 } from 'node:path';
import { fileURLToPath } from 'node:url';
import { listProjects, mediaPath, mediaTypes, setUploaded, uploadPlatforms } from './dashboard-library.mjs';
import { readReview, submitReview, suggestedReview, reviewDocument, prepareReview, selectLighting } from './review-store.mjs';
import { audioCatalogue,libraryAudio,selectAudio,settingsAudioOptions,voicePreviewFile } from './audio-library.mjs';
import { studioProject, openNativeStudio } from './native-studio.mjs';

export const studioRoot = fileURLToPath(new URL('../', import.meta.url));
export const workspaceId = root => createHash('sha256').update(realpathSync(root)).digest('hex');
const ui = fileURLToPath(new URL('../dashboard/', import.meta.url));
const openFolder = (path, done) => execFile(process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'explorer.exe' : 'xdg-open', [path], done);
export function fileLocationCommand(path, platform = process.platform) {
  if (platform === 'darwin') return ['open', ['-R', path]];
  if (platform === 'win32') return ['explorer.exe', [win32.dirname(path)]];
  return ['xdg-open', [dirname(path)]];
}
const showFile = (path, done) => {
  const [command, args] = fileLocationCommand(path);
  return execFile(command, args, done);
};
const pagePolicy = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";

export function defaultSettings() {
  return {
    channelName: 'Techno Ravan',
    creatorName: 'Nayan',
    niche: 'Developer Tutorials, AI Engineering, Full-Stack Architecture',
    targetAudience: 'Developers, Software Engineers, AI Builders',
    youtubeHandle: '@TechnoRavan',
    instagramHandle: '@technoravan',
    linkedinUrl: 'https://www.linkedin.com/in/nayanv',
    bio: 'Bite-sized developer workflows, AI systems, and modern software engineering.',
    primaryRatio: '9:16 (Portrait Reel)',
    targetResolution: '4K UHD (2160x3840)',
    targetFps: 60,
    aesthetic: 'Developer Dark (Deep Slate, Clean Accents, Terminal Highlighting)',
    preferredEffectCategory: 'Techno Ravan Effects',
    tone: 'Direct, punchy, pragmatic, high developer empathy, zero fluff',
    pacing: 'Fast hook in 0-3s, rapid transitions every 3-5s, code/terminal proof first',
    noEmDashes: true,
    callToAction: 'Follow @TechnoRavan for more developer systems',
    defaultMusicMood: 'Tech Minimal / Coding Focus',
    defaultMusicTrack: 'music-lofi',
    defaultNarrationVoice: 'af_heart',
    voiceDucking: '-18 dB during dialogue',
    sfxStyle: 'Subtle mechanical clicks, terminal beeps, soft risers',
    theme: 'system'
  };
}

export function getEffectsCatalogue() {
  const catPath = join(studioRoot, 'skills/effects/references/catalogue.json');
  const customPath = join(studioRoot, 'skills/effects/references/custom-catalogue.json');
  const effects = [];
  try {
    const list = JSON.parse(readFileSync(catPath, 'utf8'));
    for (const e of list) {
      effects.push({
        id: String(e.id),
        name: e.name,
        desc: e.desc,
        use: e.use,
        category: e.category || 'Vibha Effects',
        author: e.author || 'Vibha',
        subtitle: e.subtitle || e.use || '',
        previewUrl: `/media/skills/effects/${e.preview}`
      });
    }
  } catch {}
  if (existsSync(customPath)) {
    try {
      const customList = JSON.parse(readFileSync(customPath, 'utf8'));
      for (const e of customList) {
        effects.push({
          id: String(e.id),
          name: e.name,
          desc: e.desc,
          use: e.use,
          category: e.category || 'Techno Ravan Effects',
          author: e.author || 'Techno Ravan',
          subtitle: e.subtitle || e.use || '',
          previewUrl: e.preview ? `/media/skills/effects/${e.preview}` : ''
        });
      }
    } catch {}
  }
  return effects;
}

export async function selectEffect(root, kind, id, value) {
  const planPath = join(root, 'outputs', kind, id, 'plan.json');
  if (!existsSync(planPath)) throw new Error('Plan not found');
  const plan = JSON.parse(readFileSync(planPath, 'utf8'));
  const shot = plan.shots?.find(s => String(s.id) === String(value.scene));
  if (!shot) throw new Error('Scene not found');
  const catalogue = getEffectsCatalogue();
  const venvPython = join(studioRoot, 'skills/effects/.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const python = existsSync(venvPython) ? venvPython : (process.env.PYTHON || 'python3');

  if (value.effectId && value.effectId !== 'none') {
    const item = catalogue.find(e => String(e.id) === String(value.effectId));
    if (!item) throw new Error('Unknown effect');
    const duration = shot.clip ? (shot.clip[1] - shot.clip[0]) : (shot.estimated_duration || 3);

    let tailoredOptions = {};
    try {
      const { stdout } = await promisify(execFile)(python, ['-c', `
import sys, json
sys.path.insert(0, 'scripts')
from effect_tailor import tailor_effect_options
opts = tailor_effect_options(
    effect_id_or_name=${JSON.stringify(value.effectId)},
    speech=${JSON.stringify(shot.say || shot.expected_say || '')},
    topic=${JSON.stringify(plan.title || '')},
    creator=${JSON.stringify(plan.creator || 'Nayan')},
    handle=${JSON.stringify(plan.handle || '@TechnoRavan')},
    channel=${JSON.stringify(plan.channel || 'Techno Ravan')}
)
print(json.dumps(opts))
`], { cwd: studioRoot });
      tailoredOptions = JSON.parse(stdout.trim());
    } catch (e) {
      console.error('Error tailoring effect options:', e);
    }

    shot.vibha = {
      status: 'selected',
      category: item.category,
      author: item.author,
      effects: [{
        id: String(item.id),
        name: item.name,
        category: item.category,
        start: 0,
        end: Math.round(duration * 100) / 100,
        options: tailoredOptions
      }]
    };
  } else {
    shot.vibha = { status: 'none', effects: [] };
  }
  const current = JSON.parse(readFileSync(planPath, 'utf8'));
  const currentShot = current.shots?.find(s => String(s.id) === String(value.scene));
  if (!currentShot) throw new Error('The selected scene changed.');
  currentShot.vibha = shot.vibha;
  const pending = current.shots?.some(s => s.vibha?.status === 'pending');
  if (!pending) {
    current.visual_selection = current.shots.map(s => `Scene ${s.id}: ${s.vibha?.effects?.[0]?.name || 'none'}`).join('; ');
  }
  writeFileSync(planPath, JSON.stringify(current, null, 2) + '\n');
  const projectDir = join(root, 'outputs', kind, id);
  await promisify(execFile)(python, ['-c', `
import sys, json
sys.path.insert(0, 'scripts')
from pathlib import Path
from reel_workflow import make_html
plan = json.loads(Path(r'${planPath}').read_text())
make_html(Path(r'${projectDir}'), plan)
`], { cwd: studioRoot });
  return prepareReview(root, { kind, id, stage: readReview(root, kind, id).request.stage, document: readReview(root, kind, id).request.document });
}

export function createDashboard({ root = studioRoot, revealFolder = openFolder, revealFile = showFile, launchStudio = openNativeStudio } = {}) {
  root = realpathSync(root);
  return createServer((req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Referrer-Policy', 'no-referrer');
    res.setHeader('Content-Security-Policy', pagePolicy);
    const finish = (code, message = '') => { res.writeHead(code); res.end(req.method === 'HEAD' ? undefined : message); };
    const host = req.headers.host || '';
    if (host !== `127.0.0.1:${req.socket.localPort}`) return finish(403, 'Local dashboard only');
    if (req.headers.origin && req.headers.origin !== `http://${host}`) return finish(403, 'Cross-origin request blocked');
    try {
      const url = new URL(req.url, `http://${host}`);
      const uploadRoute = /^\/api\/projects\/(reels|ai-reels|videos|edits)\/([A-Za-z0-9_-]+)\/uploads\/([a-z]+)$/.exec(url.pathname);
      if (uploadRoute && (req.method === 'PUT' || req.method === 'DELETE')) {
        const [, kind, id, platform] = uploadRoute;
        if (!uploadPlatforms.includes(platform)) return finish(404);
        if (req.headers.origin !== `http://${host}` || req.headers['x-dashboard-action'] !== 'track-upload') return finish(403);
        const project = listProjects(root).find(p => p.kind === kind && p.id === id);
        if (!project) return finish(404, 'Project not found');
        try { setUploaded(root, project, platform, req.method === 'PUT'); }
        catch { return finish(500, 'Could not save upload status.'); }
        return finish(204);
      }
      const reviewMatch = /^\/api\/reviews\/(reels|videos|edits|plans)\/([A-Za-z0-9_-]+)(?:\/(submit|prepare|music|voice|studio|effect|lighting))?$/.exec(url.pathname);
      if (reviewMatch) {
        const [, kind, id, action] = reviewMatch;
        const sendJson = (status, data) => { res.setHeader('Content-Type', 'application/json'); finish(status, JSON.stringify(data)); };
        if (['GET', 'HEAD'].includes(req.method) && !action) {
          try { sendJson(200, { ...readReview(root, kind, id), catalogue: audioCatalogue(), effectsCatalogue: getEffectsCatalogue(), studioAvailable: Boolean(studioProject(root, kind, id)) }); }
          catch (error) { sendJson(error.status || 404, { error: error.message }); }
          return;
        }
        if (req.method !== 'POST' || !action) return finish(405);
        if (req.headers.origin !== `http://${host}` || req.headers['x-dashboard-action'] !== 'review' || !/^application\/json(?:;|$)/i.test(req.headers['content-type'] || '')) return finish(403);
        let length = 0, chunks = [];
        req.on('data', chunk => { length += chunk.length; if (length <= 32768) chunks.push(chunk); });
        req.on('end', async () => {
          try {
            if (length > 32768) return sendJson(413, { error: 'Review submission is too large.' });
            const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
            let result;
            if (action === 'studio') {
              result = await launchStudio(root, kind, id);
            } else if (action === 'prepare') {
              result = suggestedReview(root, kind, id, value.stage || 'plan');
            } else if (action === 'music' || action === 'voice') {
              result = await selectAudio(root, kind, id, value, action);
            } else if (action === 'lighting') {
              result = selectLighting(root, kind, id, value);
            } else if (action === 'effect') {
              result = await selectEffect(root, kind, id, value);
            } else {
              result = submitReview(root, kind, id, value);
              if (value.action === 'approve') {
                const currentReview = readReview(root, kind, id);
                if (currentReview?.request?.stage === 'plan') {
                  const planPath = join(root, 'outputs', kind, id, 'plan.json');
                  if (existsSync(planPath)) {
                    try {
                      const plan = JSON.parse(readFileSync(planPath, 'utf8'));
                      if (!plan.visual_selection) {
                        plan.visual_selection = plan.shots?.map(s => `Scene ${s.id}: ${s.vibha?.effects?.[0]?.name || 'none'}`).join('; ') || 'Approved plan and visual choices';
                        writeFileSync(planPath, JSON.stringify(plan, null, 2) + '\n');
                      }
                      const venvPython = join(studioRoot, 'skills/effects/.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
                      const python = existsSync(venvPython) ? venvPython : (process.env.PYTHON || 'python3');
                      execFile(python, ['scripts/reel_workflow.py', 'preview', '--kind', kind, '--project', id], { cwd: studioRoot }, (err, stdout) => {
                        if (err) {
                          console.error('Auto-preview error:', err);
                        } else {
                          try {
                            const out = JSON.parse(stdout.trim());
                            prepareReview(root, { kind, id, stage: 'frames', document: out.review });
                          } catch (e) {
                            console.error('Auto-preview parse error:', e);
                          }
                        }
                      });
                    } catch (e) {
                      console.error('Auto-preview setup error:', e);
                    }
                  }
                }
              }
            }
            sendJson(200, result);
          } catch (error) { sendJson(error.status || 400, { error: error.message }); }
        });
        return;
      }
      if (url.pathname === '/api/settings') {
        if (['GET', 'HEAD'].includes(req.method)) {
          const settingsPath = join(root, 'settings.json');
          let settings = defaultSettings();
          if (existsSync(settingsPath)) {
            try {
              const fileData = JSON.parse(readFileSync(settingsPath, 'utf8'));
              settings = { ...settings, ...fileData };
            } catch {}
          }
          res.setHeader('Content-Type', 'application/json');
          return finish(200, JSON.stringify(settings));
        }
        if (req.method === 'POST') {
          if (req.headers.origin !== `http://${host}`) {
            return finish(403);
          }
          if (req.headers['x-dashboard-action'] !== 'settings') {
            return finish(405);
          }
          if (!/^application\/json(?:;|$)/i.test(req.headers['content-type'] || '')) {
            return finish(400);
          }
          let length = 0, chunks = [];
          req.on('data', chunk => { length += chunk.length; if (length <= 32768) chunks.push(chunk); });
          req.on('end', () => {
            if (length > 32768) {
              res.setHeader('Content-Type', 'application/json');
              return finish(413, JSON.stringify({ error: 'Settings payload is too large.' }));
            }
            try {
              const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
              const current = defaultSettings();
              const settingsPath = join(root, 'settings.json');
              if (existsSync(settingsPath)) {
                try { Object.assign(current, JSON.parse(readFileSync(settingsPath, 'utf8'))); } catch {}
              }
              const options = settingsAudioOptions();
              for (const [key, choices] of [['defaultMusicTrack', options.music], ['defaultNarrationVoice', options.voices]]) {
                if (key in value) {
                  if (!choices.some(choice => choice.id === value[key])) throw new Error('Choose a listed music track and narration voice.');
                  current[key] = value[key];
                }
              }
              const allowedKeys = [
                'channelName', 'creatorName', 'niche', 'targetAudience',
                'youtubeHandle', 'instagramHandle', 'linkedinUrl', 'bio',
                'primaryRatio', 'targetResolution', 'targetFps', 'aesthetic',
                'preferredEffectCategory', 'tone', 'pacing', 'noEmDashes',
                'callToAction', 'defaultMusicMood', 'voiceDucking', 'sfxStyle', 'theme'
              ];
              for (const k of allowedKeys) {
                if (k in value) {
                  if (typeof current[k] === 'boolean') {
                    current[k] = Boolean(value[k]);
                  } else if (typeof current[k] === 'number') {
                    const num = Number(value[k]);
                    if (Number.isFinite(num)) current[k] = num;
                  } else if (typeof value[k] === 'string') {
                    current[k] = value[k].replace(/—/g, ' - ').trim();
                  }
                }
              }
              writeFileSync(settingsPath, JSON.stringify(current, null, 2) + '\n');
              res.setHeader('Content-Type', 'application/json');
              return finish(200, JSON.stringify(current));
            } catch (error) {
              res.setHeader('Content-Type', 'application/json');
              return finish(400, JSON.stringify({ error: error.message || 'Invalid settings data.' }));
            }
          });
          return;
        }
        return finish(405);
      }
      if (req.method === 'POST') {
        const match = /^\/api\/projects\/(reels|ai-reels|videos|edits)\/([A-Za-z0-9_-]+)\/(open|reveal)$/.exec(url.pathname);
        if (!match) return finish(405, 'Review only');
        const action = match[3];
        if (req.headers.origin !== `http://${host}` || req.headers['x-dashboard-action'] !== (action === 'reveal' ? 'reveal-file' : 'open-folder')) return finish(403);
        if (action === 'reveal' && !/^application\/json(?:;|$)/i.test(req.headers['content-type'] || '')) return finish(403);
        const project = listProjects(root).find(p => p.kind === match[1] && p.id === match[2]);
        if (!project) return finish(404, 'Project not found');
        if (action === 'reveal') {
          let length = 0, chunks = [];
          req.on('data', chunk => { length += chunk.length; if (length <= 32768) chunks.push(chunk); });
          req.on('end', () => {
            if (length > 32768) return finish(413, 'Request is too large.');
            let value;
            try { value = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
            catch { return finish(400, 'Choose an exported video or cover.'); }
            if (typeof value?.path !== 'string' || !value.path) return finish(400, 'Choose an exported video or cover.');
            const file = [...project.exports, ...project.covers].find(f => f.path === value.path);
            if (!file) return finish(404, 'File not found in this project.');
            let path;
            // Recheck the exact discovered media immediately before the OS action.
            try { path = mediaPath(root, file.path); }
            catch { return finish(404, 'File not found in this project.'); }
            const failed = 'Could not show the file in its folder on this device.';
            try { revealFile(path, error => finish(error ? 500 : 204, error ? failed : '')); }
            catch { finish(500, failed); }
          });
          return;
        }
        const path = join(root, project.path);
        // Recheck the project directory after discovery, before starting the platform opener.
        if (realpathSync(path) !== path || !statSync(path).isDirectory()) return finish(404);
        revealFolder(path, error => finish(error ? 500 : 204, error ? 'Could not open the folder on this device.' : ''));
        return;
      }
      if (!['GET', 'HEAD'].includes(req.method)) return finish(405, 'Review only');
      if (url.pathname === '/api/settings/audio-options') {
        res.setHeader('Content-Type', 'application/json');
        return finish(200, JSON.stringify(settingsAudioOptions()));
      }
      if(url.pathname==='/api/health'){
        res.setHeader('Content-Type','application/json');
        return finish(200,JSON.stringify({app:'ravan-reel-studio',workspace:workspaceId(root)}));
      }
      if (url.pathname === '/api/projects') {
        res.setHeader('Content-Type', 'application/json');
        return finish(200, JSON.stringify(listProjects(root)));
      }
      let path;
      if(url.pathname.startsWith('/audio/')){path=libraryAudio(decodeURIComponent(url.pathname.slice(7)));}
      else if (url.pathname.startsWith('/voice-preview/')) { path = voicePreviewFile(url.pathname.slice('/voice-preview/'.length)); }
      else if (url.pathname.startsWith('/media/')) {
        const name = decodeURIComponent(url.pathname.slice(7));
        path = name.startsWith('docs/') && name.endsWith('.html') ? reviewDocument(root, name) : mediaPath(root, name);
        // Plans are documents, never applications. Relative images and media still load.
        res.setHeader('Content-Security-Policy', `sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src http://${host} data:; media-src http://${host}; object-src 'none'; base-uri 'none'; form-action 'none'`);
        if (url.searchParams.has('download')) {
          res.setHeader('Content-Disposition', `attachment; filename="download${extname(path)}"; filename*=UTF-8''${encodeURIComponent(basename(path)).replace(/['()*]/g, c => '%' + c.charCodeAt(0).toString(16))}`);
        }
      } else {
        const reviewPage = /^\/review\/(reels|videos|edits|plans)\/[A-Za-z0-9_-]+$/.test(url.pathname);
        const name = reviewPage ? 'review.html' : { '/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/captions.mjs': 'captions.mjs', '/review.js': 'review.js', '/review.css': 'review.css', '/settings.mjs': 'settings.mjs' }[url.pathname];
        if (!name) return finish(404, 'Not found');
        path = join(ui, name);
      }
      const info = statSync(path);
      if (!info.isFile()) return finish(404);
      res.setHeader('Content-Type', mediaTypes[extname(path).toLowerCase()] || ({ '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.ttf': 'font/ttf' })[extname(path)] || 'application/octet-stream');
      res.setHeader('Accept-Ranges', 'bytes');
      let start = 0, end = info.size - 1;
      if (req.headers.range) {
        const match = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
        if (!match || (!match[1] && !match[2]) || !info.size) {
          res.setHeader('Content-Range', `bytes */${info.size}`); return finish(416);
        }
        if (match[1]) { start = Number(match[1]); end = match[2] ? Math.min(Number(match[2]), end) : end; }
        else start = Math.max(0, info.size - Number(match[2]));
        if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start > end || start >= info.size) {
          res.setHeader('Content-Range', `bytes */${info.size}`); return finish(416);
        }
        res.statusCode = 206;
        res.setHeader('Content-Range', `bytes ${start}-${end}/${info.size}`);
      }
      res.setHeader('Content-Length', Math.max(0, end - start + 1));
      if (req.method === 'HEAD' || !info.size) return res.end();
      const stream = createReadStream(path, { start, end });
      stream.on('error', () => res.destroy());
      res.on('close', () => stream.destroy());
      stream.pipe(res);
    } catch { finish(404, 'Not found'); }
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.DASHBOARD_PORT || 4173);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw Error('DASHBOARD_PORT must be a port number.');
  const server = createDashboard();
  server.on('error', error => {
    console.error(error.code === 'EADDRINUSE' ? `Port ${port} is busy. Stop the other dashboard or set DASHBOARD_PORT to another port.` : error.message);
    process.exitCode = 1;
  });
  server.listen(port, '127.0.0.1', () => console.log(`Ravan Reel Studio · http://127.0.0.1:${server.address().port}\nSubmit targeted feedback and approval here; use Hyperframes Studio for visual editing. Ctrl+C to stop.`));
}
