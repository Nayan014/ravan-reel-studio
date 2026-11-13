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
export function libraryAudio(id){
 const item=audioCatalogue().find(t=>t.id===id);if(!item)throw new ReviewError('Unknown audio track.',404);
 const base=realpathSync(join(bundled,'tools/techno-reel/public'));const path=join(bundled,item.file);
 let current=base;for(const part of relative(base,path).split(sep)){current=join(current,part);if(lstatSync(current).isSymbolicLink())throw new ReviewError('Library symlinks are not allowed.');}
 if(!realpathSync(path).startsWith(base+sep))throw new ReviewError('Invalid library path.');return path;
}
export async function selectMusic(root,kind,id,value){
 const key=`${kind}/${id}`;
 if(selecting.has(key))throw new ReviewError('A music selection is already being prepared. Wait for the refreshed review.',409);
 const state=readReview(root,kind,id);
 if(!['reels','videos'].includes(kind)||!state.request.audio)throw new ReviewError('Music selection requires a new Hyperframes project.');
 if(state.stale||state.request.id!==value.requestId)throw new ReviewError('Reload the latest review before selecting music.',409);
 if(value.track!==null&&!audioCatalogue().some(t=>t.id===value.track&&t.kind==='music'))throw new ReviewError('Choose a catalogued music track or no music.');
 mediaPath(root,`outputs/${kind}/${id}/plan.json`);
 // CLI owns audio preparation and approval fingerprints; no command text comes from the client.
 if(realpathSync(root)!==realpathSync(bundled))throw new ReviewError('Audio preparation requires this studio workspace.');
 const python=join(bundled,'skills/effects/.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
 selecting.add(key);
 try{
  await promisify(execFile)(python,[join(bundled,'scripts/reel_workflow.py'),'audio','--kind',kind,'--project',id,'--track',value.track??'none'],{cwd:bundled,timeout:120000,maxBuffer:1024*1024});
  return prepareReview(root,{kind,id,stage:state.request.stage,document:state.request.document});
 }finally{selecting.delete(key);}
}
