// Adapted from Techno Reel by Nayan V. See ../dashboard/LICENSE.
import { createServer } from 'node:http';
import {createHash} from 'node:crypto';
import { createReadStream, realpathSync, statSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { basename, dirname, extname, join, resolve, win32 } from 'node:path';
import { fileURLToPath } from 'node:url';
import { listProjects, mediaPath, mediaTypes } from './dashboard-library.mjs';
import { readReview, submitReview, suggestedReview, reviewDocument } from './review-store.mjs';
import { audioCatalogue,libraryAudio,selectMusic } from './audio-library.mjs';
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
      const reviewMatch = /^\/api\/reviews\/(reels|videos|edits|plans)\/([A-Za-z0-9_-]+)(?:\/(submit|prepare|music|studio))?$/.exec(url.pathname);
      if (reviewMatch) {
        const [, kind, id, action] = reviewMatch;
        const sendJson = (status, data) => { res.setHeader('Content-Type', 'application/json'); finish(status, JSON.stringify(data)); };
        if (['GET', 'HEAD'].includes(req.method) && !action) {
          try { sendJson(200, { ...readReview(root, kind, id), catalogue:audioCatalogue(), studioAvailable: Boolean(studioProject(root,kind,id)) }); }
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
            const result = action === 'studio' ? await launchStudio(root,kind,id) : action === 'prepare' ? suggestedReview(root, kind, id, value.stage || 'plan') : action === 'music' ? await selectMusic(root,kind,id,value) : submitReview(root, kind, id, value);
            sendJson(200, result);
          } catch (error) { sendJson(error.status || 400, { error: error.message }); }
        });
        return;
      }
      if (req.method === 'POST') {
        const match = /^\/api\/projects\/(reels|videos|edits)\/([A-Za-z0-9_-]+)\/(open|reveal)$/.exec(url.pathname);
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
        const name = reviewPage ? 'review.html' : { '/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/captions.mjs': 'captions.mjs', '/review.js': 'review.js', '/review.css': 'review.css' }[url.pathname];
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
