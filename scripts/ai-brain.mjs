// Connect this workspace to the shared AI Brain (skills, workflows). Best effort: never throws, never blocks long.
import {spawn,spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
const pythons=process.platform==='win32'?['python','py']:['python3','python'];

// wait=true: finish before returning (npm start). wait=false: run in the background (dashboard boot).
export function connectAiBrain({root=ROOT,wait=false,log=()=>{}}={}){
 const script=join(root,'scripts/ai_brain.py');
 if(!existsSync(script))return false;
 for(const python of pythons){
  try{
   if(wait){
    const r=spawnSync(python,[script,'--quiet'],{cwd:root,stdio:'inherit',timeout:180000,windowsHide:true});
    if(!r.error)return r.status===0;
   }else{
    const child=spawn(python,[script,'--quiet'],{cwd:root,stdio:'ignore',detached:true,windowsHide:true});
    child.on('error',()=>{});child.unref();return true;
   }
  }catch(error){log(`AI Brain connect skipped: ${error.message}`);}
 }
 return false;
}
