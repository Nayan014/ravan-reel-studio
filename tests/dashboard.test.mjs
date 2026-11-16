import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, symlinkSync, utimesSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { request } from 'node:http';
import { listProjects, mediaPath } from '../scripts/dashboard-library.mjs';
import { createDashboard, fileLocationCommand } from '../scripts/dashboard.mjs';
import { captionSections } from '../dashboard/captions.mjs';

function fixture(t) {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'studio-dashboard-')));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const put = (name, value = '') => {
    const path = join(root, name); mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, typeof value === 'object' ? JSON.stringify(value) : value);
    return path;
  };
  return { root, put };
}

async function serverFixture(t, root, options = {}) {
  const server = createDashboard({ root, ...options });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  t.after(() => new Promise(r => { server.closeAllConnections(); server.close(r); }));
  return `http://127.0.0.1:${server.address().port}`;
}

test('discovers reels, Hyperframes, export packages and edits without changing working directory', t => {
  const { root, put } = fixture(t);
  put('outputs/reels/first/plan.json', { title: 'First reel', renderer: 'hyperframes' });
  put('outputs/reels/first/export/old.mp4', 'old');
  put('outputs/reels/first/export/new.mp4', 'new');
  put('outputs/reels/first/export.json', { file: 'export/old.mp4', cover: { png: 'publishing/cover.png' } });
  put('outputs/reels/first/publishing/cover.png', 'cover');
  put('outputs/reels/first/publishing/captions.md', '## Instagram\nMy caption');
  put('outputs/reels/package/Creative_Final.mp4', 'package');
  put('outputs/reels/package/Creative_Cover.jpg', 'cover');
  put('outputs/reels/package/Social_Copy.md', '## Reel caption\nHello');
  put('inputs/take with spaces.MOV', 'original');
  put('outputs/edits/20261113T123000Z_test/session.json', {
    source: 'inputs/take with spaces.MOV', stage: 'rendered',
    render: 'outputs/edits/20261113T123000Z_test/renders/effect.mp4',
    preview: { frames: ['outputs/edits/20261113T123000Z_test/preview-abc/frame.png'] },
    approval: { preview_id: 'old', user_message: 'approved' },
  });
  put('outputs/edits/20261113T123000Z_test/renders/effect.mp4', 'edit');
  put('outputs/edits/20261113T123000Z_test/preview-abc/frame.png', 'frame');
  const all = listProjects(root);
  assert.equal(all.length, 3);
  const first = all.find(p => p.id === 'first');
  assert.equal(first.renderer, 'hyperframes');
  assert.equal(first.primary.name, 'export/old.mp4', 'explicit export wins over newer alternatives');
  assert.equal(first.exports.length, 2);
  assert.equal(first.cover.name, 'publishing/cover.png');
  assert.equal(first.captions[0].text, '## Instagram\nMy caption');
  assert.equal(first.status, 'export available');
  assert.deepEqual(first.warnings, []);
  const edit = all.find(p => p.kind === 'edits');
  assert.equal(edit.title, 'take with spaces');
  assert.equal(edit.primary.name, 'renders/effect.mp4');
  assert.equal(edit.source.path, 'inputs/take with spaces.MOV');
  assert.equal(edit.previews.length, 1);
  assert.equal(edit.records.find(r => r.label === 'Saved approval').data.preview_id, 'old');
  assert.equal(edit.records.some(r => 'current' in r), false);
  assert.equal(all.find(p => p.id === 'package').primary.name, 'Creative_Final.mp4');
});

test('uses newest fallback and isolates malformed metadata, missing files and duplicate filenames', t => {
  const { root, put } = fixture(t);
  const old = put('outputs/reels/a/export/final.mp4', 'first');
  utimesSync(old, new Date(1000), new Date(1000));
  put('outputs/reels/a/export/later.mp4', 'later');
  put('outputs/reels/a/plan.json', '{broken');
  put('outputs/reels/a/export.json', { file: 'export/missing.mp4' });
  put('outputs/reels/b/export/final.mp4', 'second');
  const all = listProjects(root);
  assert.equal(all.length, 2);
  const a = all.find(p => p.id === 'a'), b = all.find(p => p.id === 'b');
  assert.equal(a.primary.name, 'export/later.mp4');
  assert.notEqual(a.exports.find(f => f.name === 'export/final.mp4').url, b.primary.url);
  assert.equal(a.cover, null);
  assert.deepEqual(a.captions, []);
  assert.equal(a.warnings.length, 2);
  assert.deepEqual(b.warnings, []);
  put('outputs/reels/a/export.json', { file: '../b/export/final.mp4' });
  assert.equal(listProjects(root).find(p => p.id === 'a').primary.name, 'export/later.mp4');
  rmSync(join(root, 'outputs'), { recursive: true });
  assert.deepEqual(listProjects(root), []);
});

test('rejects traversal, private paths, and symlink files, directories and library roots', t => {
  const { root, put } = fixture(t);
  const secret = put('private/secret.txt', 'secret');
  put('outputs/reels/a/export/final.mp4', 'video');
  put('outputs/reels/a/node_modules/leak.txt', 'private dependency');
  symlinkSync(secret, join(root, 'outputs/reels/a/export/leak.txt'));
  symlinkSync(join(root, 'private'), join(root, 'outputs/reels/a/assets'));
  symlinkSync(join(root, 'outputs/reels/a'), join(root, 'outputs/reels/linked'));
  for (const path of ['../private/secret.txt', '/private/secret.txt', 'outputs/reels/a/../../../private/secret.txt', 'outputs/reels/a/.env', 'outputs/reels/a/export/leak.txt', 'outputs/reels/a/assets/secret.txt', 'outputs/reels/a/node_modules/leak.txt', 'outputs/reels/linked/export/final.mp4', 'private/secret.txt']) {
    assert.throws(() => mediaPath(root, path), path);
  }
  assert.equal(listProjects(root).length, 1);
  assert.equal(listProjects(root)[0].files.length, 1);
  rmSync(join(root, 'outputs'), { recursive: true });
  symlinkSync(join(root, 'private'), join(root, 'outputs'));
  assert.deepEqual(listProjects(root), []);
});

test('serves API, byte ranges, Unicode downloads, HEAD, and sandboxed plans with relative assets', async t => {
  const { root, put } = fixture(t);
  put('outputs/reels/test/export/final ü.mp4', '0123456789');
  put('outputs/reels/test/review.html', '<script>parent.alert(1)</script><img src="previews/frame.png">');
  put('outputs/reels/test/previews/frame.png', 'frame');
  const base = await serverFixture(t, root);
  const projects = await (await fetch(`${base}/api/projects`)).json();
  assert.equal(projects[0].id, 'test');
  const video = base + projects[0].primary.url;
  const range = await fetch(video, { headers: { range: 'bytes=2-5' } });
  assert.equal(range.status, 206);
  assert.equal(range.headers.get('content-range'), 'bytes 2-5/10');
  assert.equal(await range.text(), '2345');
  const suffix = await fetch(video, { headers: { range: 'bytes=-3' } });
  assert.equal(await suffix.text(), '789');
  for (const value of ['bytes=11-', 'bytes=5-2', 'bytes=-0', 'bytes=0-1,3-4', 'bytes=9007199254740993-']) {
    assert.equal((await fetch(video, { headers: { range: value } })).status, 416);
  }
  const head = await fetch(video, { method: 'HEAD' });
  assert.equal(head.headers.get('content-length'), '10');
  assert.equal(await head.text(), '');
  const attachment = await fetch(video + '?download=1');
  assert.match(attachment.headers.get('content-disposition'), /filename\*=UTF-8''final%20%C3%BC.mp4/);
  const plan = await fetch(base + '/media/outputs/reels/test/review.html');
  const policy = plan.headers.get('content-security-policy');
  assert.match(policy, /sandbox;/);
  assert.doesNotMatch(policy, /script-src|allow-scripts|allow-same-origin/);
  assert.equal((await fetch(new URL('previews/frame.png', plan.url))).status, 200);
  for (const path of ['/media/private/secret.txt', '/media/outputs/reels/test/%2e%2e/%2e%2e/%2e%2e/private/secret.txt', '/media/outputs/reels/test/%5c..%5csecret.txt', '/media/%E0%A4%A', '/app/unknown.js']) {
    assert.equal((await fetch(base + path)).status, 404);
  }
  assert.equal((await fetch(base + '/')).status, 200);
  assert.equal((await fetch(base + '/app.js')).headers.get('content-type'), 'text/javascript');
});

test('folder opening requires same origin, a custom header and an existing project', async t => {
  const { root, put } = fixture(t);
  put('outputs/reels/a/export/final.mp4', 'video');
  let opened = [];
  const base = await serverFixture(t, root, { revealFolder: (path, done) => { opened.push(path); done(null); } });
  const endpoint = base + '/api/projects/reels/a/open';
  assert.equal((await fetch(endpoint, { method: 'POST' })).status, 403);
  assert.equal((await fetch(endpoint, { method: 'POST', headers: { origin: 'https://evil.example', 'x-dashboard-action': 'open-folder' } })).status, 403);
  assert.equal((await fetch(endpoint, { method: 'POST', headers: { origin: base } })).status, 403);
  const action = { method: 'POST', headers: { origin: base, 'x-dashboard-action': 'open-folder' } };
  assert.equal((await fetch(base + '/api/projects/reels/missing/open', action)).status, 404);
  assert.equal((await fetch(endpoint, action)).status, 204);
  assert.deepEqual(opened, [join(root, 'outputs/reels/a')]);
  assert.equal((await fetch(base + '/api/settings', action)).status, 405);
  assert.equal((await fetch(base + '/api/projects', { headers: { origin: 'null' } })).status, 403);
  const status = await new Promise((resolve, reject) => {
    const req = request(base + '/api/projects', { headers: { host: 'evil.example' } }, res => { res.resume(); resolve(res.statusCode); });
    req.on('error', reject); req.end();
  });
  assert.equal(status, 403);
});

test('file location commands select the file on macOS and open the containing folder elsewhere', () => {
  assert.deepEqual(fileLocationCommand('/work/export/My ü video.mp4', 'darwin'), ['open', ['-R', '/work/export/My ü video.mp4']]);
  assert.deepEqual(fileLocationCommand('C:\\work\\export\\My ü video.mp4', 'win32'), ['explorer.exe', ['C:\\work\\export']]);
  assert.deepEqual(fileLocationCommand('/work/export/My ü video.mp4', 'linux'), ['xdg-open', ['/work/export']]);
});

test('reveals the requested export or cover, including alternate exports and Unicode filenames', async t => {
  const { root, put } = fixture(t);
  const video = 'outputs/edits/example/export/Final ü video.mp4';
  const alternate = 'outputs/edits/example/export/Alternate.mp4';
  const cover = 'outputs/edits/example/publishing/cover ü.png';
  for (const file of [video, alternate, cover]) put(file, 'media');
  put('outputs/edits/example/export.json', { file: 'export/Final ü video.mp4', cover: 'publishing/cover ü.png' });
  const opened = [];
  const base = await serverFixture(t, root, { revealFile: (path, done) => { opened.push(path); done(null); } });
  const endpoint = base + '/api/projects/edits/example/reveal';
  const headers = { origin: base, 'x-dashboard-action': 'reveal-file', 'content-type': 'application/json' };
  for (const path of [video, alternate, cover]) {
    assert.equal((await fetch(endpoint, { method: 'POST', headers, body: JSON.stringify({ path }) })).status, 204);
  }
  assert.deepEqual(opened, [video, alternate, cover].map(path => join(root, path)));
});

test('file reveal rejects cross-origin, invalid bodies and paths outside the project media', async t => {
  const { root, put } = fixture(t);
  const video = 'outputs/reels/a/export/final.mp4';
  put(video, 'video');
  put('outputs/reels/a/assets/notes.txt', 'not an export');
  put('outputs/reels/b/export/other.mp4', 'other project');
  const secret = put('private/secret.mp4', 'private');
  symlinkSync(secret, join(root, 'outputs/reels/a/export/linked.mp4'));
  const opened = [];
  const base = await serverFixture(t, root, { revealFile: (path, done) => { opened.push(path); done(null); } });
  const endpoint = base + '/api/projects/reels/a/reveal';
  const headers = { origin: base, 'x-dashboard-action': 'reveal-file', 'content-type': 'application/json' };
  const send = (body, overrides = {}) => fetch(endpoint, { method: 'POST', headers: { ...headers, ...overrides }, body });
  const body = JSON.stringify({ path: video });
  assert.equal((await fetch(endpoint, { method: 'POST', body })).status, 403);
  assert.equal((await send(body, { origin: 'https://evil.example' })).status, 403);
  assert.equal((await send(body, { 'x-dashboard-action': 'open-folder' })).status, 403);
  assert.equal((await send(body, { 'content-type': 'text/plain' })).status, 403);
  for (const value of ['{broken', 'null', '{}', '{"path":42}']) assert.equal((await send(value)).status, 400);
  assert.equal((await send(' '.repeat(32769))).status, 413);
  for (const path of ['/private/secret.mp4', '../private/secret.mp4', 'outputs/reels/b/export/other.mp4',
                      'outputs/reels/a/assets/notes.txt', 'outputs/reels/a/export/linked.mp4',
                      'outputs/reels/a/export/missing.mp4']) {
    assert.equal((await send(JSON.stringify({ path }))).status, 404, path);
  }
  assert.equal((await fetch(base + '/api/projects/reels/missing/reveal', { method: 'POST', headers, body })).status, 404);
  assert.deepEqual(opened, []);
});

test('file reveal reports a launcher failure without claiming that the folder opened', async t => {
  const { root, put } = fixture(t);
  const path = 'outputs/reels/a/export/final.mp4';
  put(path, 'video');
  const base = await serverFixture(t, root, { revealFile: (_path, done) => done(new Error('Launcher failed')) });
  const response = await fetch(base + '/api/projects/reels/a/reveal', {
    method: 'POST', headers: { origin: base, 'x-dashboard-action': 'reveal-file', 'content-type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  assert.equal(response.status, 500);
  assert.equal(await response.text(), 'Could not show the file in its folder on this device.');
});

test('caption sections support Markdown, either platform order, inline titles and legacy plain text', () => {
  const markdown = captionSections('# Posting copy\n\n## YouTube Shorts\n\nTitle: My title\n\nDescription:\nMy description\n#Shorts\n\n## Instagram\nMy caption\n#Reels\n\n## TikTok\nTikTok copy');
  assert.deepEqual(markdown, [
    { label: 'YouTube title', text: 'My title' },
    { label: 'YouTube description', text: 'My description\n#Shorts' },
    { label: 'Instagram', text: 'My caption\n#Reels' },
    { label: 'TikTok', text: 'TikTok copy' },
  ]);
  assert.deepEqual(captionSections('INSTAGRAM\nHello\n----\nYOUTUBE\nTitle:\nA title\nDescription:\nA description'), [
    { label: 'INSTAGRAM', text: 'Hello' }, { label: 'YouTube title', text: 'A title' }, { label: 'YouTube description', text: 'A description' },
  ]);
  assert.deepEqual(captionSections('Plain text\n#VideoEditing'), [{ label: 'Caption', text: 'Plain text\n#VideoEditing' }]);
  assert.deepEqual(captionSections(''), []);
});
