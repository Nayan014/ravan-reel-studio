import { createHash, randomUUID } from 'node:crypto';
import { existsSync, lstatSync, mkdirSync, readdirSync, readFileSync, realpathSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import {fileURLToPath} from 'node:url';
import { mediaPath, mediaUrl, listProjects, validId } from './dashboard-library.mjs';

const hash = value => createHash('sha256').update(value).digest('hex');
const parse = path => JSON.parse(readFileSync(path, 'utf8'));
const inside = (base, path) => path.startsWith(base + sep);
const slash = path => path.split(sep).join('/');
const bundled=fileURLToPath(new URL('../',import.meta.url));
export class ReviewError extends Error {
  constructor(message, status = 400) { super(message); this.status = status; }
}

function location(root, kind, id) {
  if (!['reels', 'videos', 'edits', 'plans'].includes(kind) || !validId(id || '')) throw new ReviewError('Invalid review identifier.');
  root = realpathSync(root);
  const path = join(root, 'outputs', '.workflow', 'reviews', kind, `${id}.json`);
  let current = root;
  for (const part of relative(root, path).split(sep)) {
    current = join(current, part);
    if (existsSync(current) && lstatSync(current).isSymbolicLink()) throw new ReviewError('Review storage cannot use symlinks.');
  }
  return path;
}

function save(path, data) {
  mkdirSync(dirname(path), { recursive: true });
  const temp = `${path}.${randomUUID()}.tmp`;
  writeFileSync(temp, JSON.stringify(data, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
  renameSync(temp, path);
}

// Draft plans may live in docs/ before recordings have been imported into a project.
export function reviewDocument(root, name) {
  if (typeof name !== 'string' || !name.endsWith('.html')) throw new ReviewError('Choose an HTML review document.');
  if (!name.startsWith('docs/')) return mediaPath(root, name);
  if (isAbsolute(name) || name.includes('\\') || name.split('/').some(p => !p || p.startsWith('.'))) throw new ReviewError('Invalid document path.');
  let path = realpathSync(root);
  for (const part of name.split('/')) {
    path = join(path, part);
    if (lstatSync(path).isSymbolicLink()) throw new ReviewError('Review documents cannot use symlinks.');
  }
  if (!inside(realpathSync(root), realpathSync(path))) throw new ReviewError('Invalid document path.');
  return path;
}

function context(root, kind, id, stage, document) {
  const files = [], add = name => {
    try { const path = mediaPath(root, name); files.push([name, hash(readFileSync(path))]); return parse(path); }
    catch { return null; }
  };
  let title = id.replace(/[-_]/g, ' '), scenes = [], previewId = null, frames = [], outputProfile=null, audio=null, sourceProfiles=[], referenceStyle=null;
  if (kind !== 'plans') {
    const base = `outputs/${kind}/${id}`;
    const plan = add(`${base}/plan.json`), session = add(`${base}/session.json`);
    if(plan?.renderer==='hyperframes'){
      const track=path=>{
        if(!existsSync(path)||lstatSync(path).isSymbolicLink())return;
        for(const entry of readdirSync(path,{withFileTypes:true})){
          if(entry.name.startsWith('.')||entry.name==='node_modules'||entry.isSymbolicLink())continue;
          const file=join(path,entry.name);
          if(entry.isDirectory())track(file);
          else if(entry.isFile()&&/\.(html|css|m?js|json|py|onnx|tflite|png|jpe?g|svg|webp|ttf|mp4|mov|m4v|mkv|avi|webm)$/i.test(entry.name)){
            const signature=/\.(html|css|m?js|json|py|svg|ttf)$/i.test(entry.name)?hash(readFileSync(file)):`${lstatSync(file).size}:${lstatSync(file).mtimeMs}`;
            files.push([slash(relative(root,file)),signature]);
          }
        }
      };
      for(const dir of ['hyperframes','hyperframes-4k','raw','assets'])track(join(root,base,dir));
      if(plan.pipeline_version===2){
        for(const name of ['scripts/reel_workflow.py','scripts/reel_pipeline.py','scripts/media_profile.py','scripts/audio_library.py','assets/audio/catalogue.json']){
          const path=join(bundled,name);files.push([`engine:${name}`,hash(readFileSync(path))]);
        }
        for(const name of ['scripts','fonts','models'])track(join(bundled,'skills/effects',name));
        const catalogue=JSON.parse(readFileSync(join(bundled,'assets/audio/catalogue.json'),'utf8')).entries;
        for(const ident of [plan.audio?.music,...(plan.audio?.sfx||[]).map(c=>c.sound)].filter(Boolean)){
          const item=catalogue.find(t=>t.id===ident);
          if(item){const path=join(bundled,item.file);files.push([`audio:${ident}`,hash(readFileSync(path))]);}
        }
      }
    }
    const preview = kind === 'edits' ? session?.preview : add(`${base}/preview.json`);
    if (!plan && !session) throw new ReviewError('A saved workflow plan or session is required.', 404);
    if(plan) files.push(['project-type',plan.project_type||'reel']);
    if(plan?.reference_style){
      const ref=plan.reference_style;
      referenceStyle={name:String(ref.name||''),summary:String(ref.summary||'')};
      if(typeof ref.profile==='string'&&ref.profile.startsWith('assets/reference-styles/')) add(`${base}/${ref.profile}`);
    }
    title = plan?.title || session?.source?.split('/').at(-1) || title;
    outputProfile=plan?.output_profile||null;sourceProfiles=plan?.source_profiles||[];
    audio=plan?.pipeline_version===2?{...plan.audio,mixSample:preview?.mix_sample?mediaUrl(slash(relative(root,preview.mix_sample))):null}:null;
    let cursor=0;const parts=String(outputProfile?.fps||30).split('/'),fps=Number(parts[0])/Number(parts[1]||1);
    scenes = (Array.isArray(plan?.shots) ? plan.shots : []).map((s,index) => {
      const start=cursor,duration=s.clip?Math.max(1,Math.round((s.clip[1]-s.clip[0])*fps))/fps:s.estimated_duration||0;cursor+=duration;
      const source=sourceProfiles[index],scale=source&&outputProfile?(s.framing==='fit'?Math.min:Math.max)(outputProfile.width/source.width,outputProfile.height/source.height):null;
      const framing=scale ? s.framing==='fit'
        ? `Displayed source ${source.width}×${source.height} · fit with padding · picture ${Math.round(source.width*scale)}×${Math.round(source.height*scale)} · scale ${scale.toFixed(3)}×`
        : `Displayed source ${source.width}×${source.height} · crop ${Math.round(outputProfile.width/scale)}×${Math.round(outputProfile.height/scale)} · scale ${scale.toFixed(3)}×`
        : '';
      return { id: String(s.id), text: String(s.say || s.expected_say || ''),timeline:[start,cursor],
      source:s.source||'Awaiting numbered recording',shootingNote:s.shooting_note||'',referenceNote:String(s.reference_note||''),clip:s.clip||null,
      captions:s.caption_pages||[],effects:s.vibha||{},finish:s.hyperframes_note||'Hyperframes assembly, captions and audio',
      sourceFrame:s.source_frame?mediaUrl(`${base}/${s.source_frame}`):null,focus:s.focus||[.5,.4],framing };});
    if(stage==='frames')for(const file of preview?.audio_files||[]){
      const name=isAbsolute(file)?slash(relative(root,file)):file;
      // Library audio is fingerprinted separately; only project audio may be served as media.
      if(name.startsWith(base+'/')){const path=mediaPath(root,name);files.push([name,hash(readFileSync(path))]);}
    }
    if (session?.plan) {
      const name = isAbsolute(session.plan) ? slash(relative(root, session.plan)) : session.plan.startsWith('outputs/') ? session.plan : `${base}/${session.plan}`;
      if (!name.startsWith(base + '/')) throw new ReviewError('Effect plan is outside this session.');
      const effects = add(name);
      scenes = (Array.isArray(effects?.effects) ? effects.effects : []).map((e, i) => ({ id: String(i + 1).padStart(2, '0'), text: `${e.fx || 'Effect'} · ${e.start ?? 0}–${e.end ?? '?'} seconds` }));
    }
    if (stage === 'frames') {
      if (!preview?.id) throw new ReviewError('Generate actual preview frames before opening a frame approval.');
      previewId = preview.id;
      const source = Array.isArray(preview.frames) ? preview.frames : Array.isArray(preview.files) ? preview.files : [];
      frames = source.filter(p => typeof p === 'string' && /\.(png|jpe?g|webp)$/i.test(p)).map(p => {
        const name = isAbsolute(p) ? slash(relative(root, p)) : p.startsWith('outputs/') ? p : `${base}/${p}`;
        if (!name.startsWith(base + '/')) throw new ReviewError('Preview frame is outside this project.');
        const path = mediaPath(root, name);
        files.push([name, hash(readFileSync(path))]);
        const detail=preview.frame_details?.find(f=>f.file===p);
        return { url: mediaUrl(name), name: name.slice(base.length + 1),id:detail?.id||name.slice(base.length+1),scene:detail?.scene||'',time:detail?.time??null };
      });
      if (!frames.length) throw new ReviewError('No actual preview images are available.');
    }
  }
  if (document) {
    const path = reviewDocument(root, document);
    if (kind !== 'plans' && !document.startsWith(`outputs/${kind}/${id}/`)) throw new ReviewError('Choose a document inside this project.');
    files.push([document, hash(readFileSync(path))]);
    if (!scenes.length) {
      const html = readFileSync(path, 'utf8');
      scenes = [...html.matchAll(/\b(?:Take|Scene)\s+(\d+)\b/gi)].map(m => ({ id: m[1], text: '' }));
      scenes = [...new Map(scenes.map(s => [s.id, s])).values()];
    }
  }
  if (kind === 'plans' && (stage !== 'plan' || !document)) throw new ReviewError('Draft plans require an HTML document and plan review stage.');
  if (kind === 'plans') {
    const stored=location(root,kind,id);
    const design=existsSync(stored)?parse(stored).design||{}:{};
    files.push(['draft-text-layers',hash(JSON.stringify(design))]);
    if (!scenes.length) scenes=[{id:'01',text:'Draft text design'}];
  }
  return { title: String(title), scenes, previewId, frames, outputProfile,sourceProfiles,audio,referenceStyle, fingerprint: hash(JSON.stringify([stage, files])) };
}

export function prepareReview(root, { kind, id, stage = 'plan', document = null }) {
  const path = location(root, kind, id);
  if (!['script','plan', 'frames'].includes(stage)) throw new ReviewError('Choose script, plan or frames review.');
  const snapshot = context(root, kind, id, stage, document);
  let old = null;
  if (existsSync(path)) old = parse(path);
  if (old?.request.fingerprint === snapshot.fingerprint && old.request.document === document) return old;
  const state = {
    request: { id: randomUUID(), kind, project: id, stage, document, createdAt: new Date().toISOString(), ...snapshot },
    submissions: old?.submissions || [],
    ...(kind==='plans'?{design:old?.design||{}}:{}),
  };
  save(path, state);
  return state;
}

export function readReview(root, kind, id) {
  const path = location(root, kind, id);
  if (!existsSync(path)) throw new ReviewError('No review is open. Ask your editing agent to open this plan for review.', 404);
  const state = parse(path), r = state.request;
  let stale = false;
  try { stale = context(root, kind, id, r.stage, r.document).fingerprint !== r.fingerprint; }
  catch { stale = true; }
  return { ...state, stale };
}

export function submitReview(root, kind, id, value) {
  const path = location(root, kind, id), state = readReview(root, kind, id), r = state.request;
  if (!value || !['feedback', 'approve'].includes(value.action) || !/^[a-f0-9-]{36}$/.test(value.id || '')) throw new ReviewError('Invalid review submission.');
  const duplicate = state.submissions.find(s => s.id === value.id);
  if (duplicate) return duplicate;
  if (state.stale || value.requestId !== r.id) throw new ReviewError('This review changed. Reload the latest revision before submitting.', 409);
  if (value.action==='approve'&&state.submissions.some(s=>s.status==='pending')) throw new ReviewError('Resolve submitted feedback before approving.',409);
  const text = typeof value.text === 'string' ? value.text.trim() : '';
  let scene = typeof value.scene === 'string' ? value.scene : '';
  const scope=value.scope|| (scene?'scene':'script'),frame=typeof value.frame==='string'?value.frame:'';
  if(!['script','scene','frame'].includes(scope))throw new ReviewError('Choose script, scene or frame feedback.');
  if(scope==='scene'&&!scene)throw new ReviewError('Scene feedback requires a scene.');
  if(scope==='frame'&&!r.frames.some(f=>f.id===frame&&(!scene||f.scene===scene)))throw new ReviewError('Choose an actual frame in this revision.');
  if(scope==='frame')scene=r.frames.find(f=>f.id===frame).scene;
  if(scope==='script'&&(scene||frame))throw new ReviewError('Full-script feedback cannot target a scene or frame.');
  if (scene && !r.scenes.some(s => s.id === scene)) throw new ReviewError('Choose a scene shown in this review.');
  if (value.action === 'feedback' && (!text || text.length > 8000)) throw new ReviewError('Enter feedback of up to 8,000 characters.');
  if (value.action === 'approve' && text) throw new ReviewError('Submit your requested changes before approving.');
  const submission = {
    id: value.id, requestId: r.id, action: value.action, scene,scope,frame,
    text: value.action === 'approve' ? `Approve the current ${r.stage === 'frames' ? (r.audio?'actual frames, audio, output profile and crop':'actual frames') : r.stage==='script'?'script':'plan and visual choices'} shown in review ${r.id}.` : text,
    stage: r.stage, previewId: r.previewId, fingerprint: r.fingerprint,
    at: new Date().toISOString(), status: 'pending',
  };
  state.submissions.push(submission);
  delete state.stale;
  save(path, state);
  return submission;
}

export function acknowledgeReview(root, kind, id, eventId, message) {
  const path = location(root, kind, id), state = readReview(root, kind, id);
  const event = state.submissions.find(s => s.id === eventId);
  if (!event || !message?.trim()) throw new ReviewError('Choose a submission and describe what was done.');
  event.status = 'handled'; event.result = message.trim(); event.handledAt = new Date().toISOString();
  delete state.stale;
  save(path, state);
  return event;
}

export function recordVisualEdit(root, kind, id, requestId, scene) {
  const path = location(root, kind, id), state = parse(path);
  if (state.request.id !== requestId) throw new ReviewError('The active review changed.', 409);
  const event = { id: randomUUID(), requestId, action: 'visual_edit', scene,
    text: `Saved text-layer edits for scene ${scene}. Generate fresh actual preview frames before approval.`,
    stage: state.request.stage, previewId: null, at: new Date().toISOString(), status: 'pending' };
  state.submissions.push(event); save(path, state); return event;
}

export function saveDraftDesign(root,id,value,layers) {
  const path=location(root,'plans',id),state=readReview(root,'plans',id);
  if (state.request.id!==value.requestId || hash(JSON.stringify(state.design||{}))!==value.revision) throw new ReviewError('Draft changed. Reload before saving.',409);
  if (!state.request.scenes.some(s=>s.id===value.scene)) throw new ReviewError('Scene not found.');
  state.design={...state.design,[value.scene]:layers};delete state.stale;save(path,state);
  return recordVisualEdit(root,'plans',id,value.requestId,value.scene);
}

export function suggestedReview(root, kind, id, stage = 'plan') {
  const project = listProjects(root).find(p => p.kind === kind && p.id === id);
  if (!project) throw new ReviewError('Project not found.', 404);
  if(['reels','videos'].includes(kind)&&stage==='plan'){
    const plan=parse(mediaPath(root,`outputs/${kind}/${id}/plan.json`));
    if(plan.phase==='draft')stage='script';
  }
  let document=(stage==='frames'?project.plans.find(p=>p.path.includes('/previews/')):project.plans.find(p=>p.path===`${project.path}/review.html`))?.path||project.plans[0]?.path||null;
  if(['reels','videos'].includes(kind)&&stage==='frames'){
    try{const record=parse(mediaPath(root,`${project.path}/preview.json`));if(typeof record.review==='string')document=isAbsolute(record.review)?slash(relative(root,record.review)):record.review.startsWith('outputs/')?record.review:`${project.path}/${record.review}`;}catch{}
  }
  return prepareReview(root, { kind, id, stage, document });
}
