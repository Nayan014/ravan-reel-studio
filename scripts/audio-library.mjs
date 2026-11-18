import {readFileSync,realpathSync,lstatSync} from 'node:fs';
import {join,relative,sep} from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {readReview,prepareReview,ReviewError} from './review-store.mjs';
import {mediaPath} from './dashboard-library.mjs';
const bundled=fileURLToPath(new URL('../',import.meta.url));
const selecting=new Set();
export function audioCatalogue(){return JSON.parse(readFileSync(join(bundled,'assets/audio/catalogue.json'),'utf8')).entries;}
const voicePresets = JSON.parse(readFileSync(join(bundled, 'assets/audio/voices.json'), 'utf8'));

export function settingsAudioOptions() {
  const music = audioCatalogue().filter(item => item.kind === 'music' && item.license === 'CC0-1.0'
    && item.license_url === 'https://creativecommons.org/publicdomain/zero/1.0/' && item.author
    && item.popularity?.scope === 'recording' && ['favorites', 'downloads'].includes(item.popularity.metric)
    && Number.parseFloat(String(item.popularity.display_count).replaceAll(',', '')) > 0
    && Number.isFinite(Date.parse(item.popularity.checked)) && item.popularity.source?.startsWith('https://'));
  return {
    music: [...music.map(item => ({id: item.id, name: item.title, preview: '/audio/' + item.id})),
      {id: 'none', name: 'No background music', preview: null}],
    voices: voicePresets.map(({id, name}) => ({id, name, preview: '/voice-preview/' + id}))
  };
}

export function voicePreviewFile(id) {
  if (!voicePresets.some(voice => voice.id === id)) throw new ReviewError('Unknown voice.', 404);
  const path = join(bundled, 'assets/audio/voices', id + '.mp3');
  if (realpathSync(path) !== path) throw new ReviewError('Invalid voice preview path.', 404);
  return path;
}
export function libraryAudio(id){
 const item=audioCatalogue().find(t=>t.id===id);if(!item)throw new ReviewError('Unknown audio track.',404);
 const base=realpathSync(join(bundled,'tools/techno-reel/public'));const path=join(bundled,item.file);
 let current=base;for(const part of relative(base,path).split(sep)){current=join(current,part);if(lstatSync(current).isSymbolicLink())throw new ReviewError('Library symlinks are not allowed.');}
 if(!realpathSync(path).startsWith(base+sep))throw new ReviewError('Invalid library path.');return path;
}
export async function selectAudio(root,kind,id,value,action){
 const key=`${kind}/${id}`;
 if(selecting.has(key))throw new ReviewError('An audio selection is already being prepared. Wait for the refreshed review.',409);
 const state=readReview(root,kind,id);
 if(!['reels','videos'].includes(kind)||!state.request.audio)throw new ReviewError('Audio selection requires a v2 Hyperframes project.');
 if(state.stale||state.request.id!==value.requestId)throw new ReviewError('Reload the latest review before selecting audio.',409);
 let args;
 if(action==='voice'){
   const scene=state.request.scenes.find(s=>s.id===value.scene);
   if(!scene?.audition || scene.audition.id!==value.auditionId || !['A','B'].includes(value.take))throw new ReviewError('Choose a reading from this scene and revision.');
   args=['select-voice','--scene',scene.id,'--audition-id',scene.audition.id,'--take',value.take];
 }else{
   if(value.track!==null&&!audioCatalogue().some(t=>t.id===value.track&&t.kind==='music'))throw new ReviewError('Choose a catalogued music track or no music.');
   args=['audio','--track',value.track??'none'];
 }
 mediaPath(root,`outputs/${kind}/${id}/plan.json`);
 // CLI owns audio preparation and approval fingerprints; no command text comes from the client.
 if(realpathSync(root)!==realpathSync(bundled))throw new ReviewError('Audio preparation requires this studio workspace.');
 const python=join(bundled,'skills/effects/.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
 selecting.add(key);
 try{
  await promisify(execFile)(python,[join(bundled,'scripts/reel_workflow.py'),...args,'--kind',kind,'--project',id],{cwd:bundled,timeout:120000,maxBuffer:1024*1024});
  return prepareReview(root,{kind,id,stage:action==='voice'?'plan':state.request.stage,document:state.request.document});
 }finally{selecting.delete(key);}
}

// Keep the existing music-only interface for other dashboard integrations.
export function selectMusic(root,kind,id,value) {
 return selectAudio(root,kind,id,value,'music');
}
