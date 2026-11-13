import {execFile} from 'node:child_process';
import {existsSync,lstatSync,readFileSync,realpathSync,statSync} from 'node:fs';
import {join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {ReviewError} from './review-store.mjs';
import {validId,mediaPath} from './dashboard-library.mjs';

export function studioProject(root,kind,id){
 if(!['reels','videos'].includes(kind)||!validId(id||''))return null;
 const project=join(realpathSync(root),`outputs/${kind}`,id);
 try{
  if(realpathSync(project)!==project)return null;
  if(JSON.parse(readFileSync(mediaPath(root,`outputs/${kind}/${id}/plan.json`),'utf8')).renderer!=='hyperframes')return null;
  const candidates=['hyperframes-4k','hyperframes'].map(n=>join(project,n)).filter(p=>existsSync(join(p,'index.html')));
  const safe=candidates.filter(p=>{
   let at=project;
   for(const part of relative(project,join(p,'index.html')).split(sep)){at=join(at,part);if(lstatSync(at).isSymbolicLink())return false;}
   return true;
  });
  let preferred=null;
  try{const value=JSON.parse(readFileSync(mediaPath(root,`outputs/${kind}/${id}/export.json`),'utf8')).project;preferred=typeof value==='string'?(value.startsWith(project+sep)?value:join(project,value)):null;}catch{}
  return safe.includes(preferred)?preferred:safe.sort((a,b)=>statSync(join(b,'index.html')).mtimeMs-statSync(join(a,'index.html')).mtimeMs)[0]||null;
 }catch{return null;}
}

export async function openNativeStudio(root,kind,id,{execute=execFile}={}){
 const cwd=studioProject(root,kind,id);
 if(!cwd)throw new ReviewError('No editable Hyperframes composition is available for this project.',404);
 const wrapper=fileURLToPath(new URL('../tools/hyperframes/hyperframes.mjs',import.meta.url));
 const output=await new Promise((resolve,reject)=>execute(process.execPath,[wrapper,'preview',cwd,'--background','--no-open','--json'],{cwd,timeout:30000,maxBuffer:1024*1024},(error,stdout,stderr)=>error?reject(new ReviewError(stderr?.trim()||error.message,500)):resolve(stdout)));
 const match=String(output).match(/http:\/\/(?:127\.0\.0\.1|localhost):\d+\/#project\/[^\s"<>]+/);
 if(!match)throw new ReviewError('Studio did not return a local project URL. Check the terminal.',500);
 return {url:match[0],composition:relative(realpathSync(root),cwd).split(sep).join('/')};
}
