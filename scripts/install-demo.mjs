// A pre-rendered synthetic example; no renderer, AI service or private media needed.
import {constants,copyFileSync,existsSync,lstatSync,mkdirSync,readFileSync,realpathSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export function installDemo(root=fileURLToPath(new URL('../',import.meta.url))){
 root=realpathSync(root);
 const source=join(root,'examples/demo'),parent=join(root,'outputs/reels'),target=join(parent,'synthetic-demo');
 for(const path of [join(root,'outputs'),parent,target])if(lstatSync(path,{throwIfNoEntry:false})?.isSymbolicLink())throw Error('Demo output folders cannot use symlinks.');
 if(existsSync(target))throw Error('synthetic-demo already exists. Nothing was overwritten; open it in the dashboard.');
 const scan=path=>{
  if(lstatSync(path).isSymbolicLink())throw Error('Demo assets cannot use symlinks.');
 };
 const files=['README.md','export.json','export/demo.mp4','export/cover.png','export/caption.txt'];
 scan(join(root,'examples'));scan(source);scan(join(source,'export'));for(const name of files)scan(join(source,name));
 const record=JSON.parse(readFileSync(join(source,'export.json'),'utf8'));
 if(record.synthetic!==true)throw Error('The bundled example must be labelled synthetic.');
 mkdirSync(parent,{recursive:true});
 mkdirSync(target);mkdirSync(join(target,'export'));
 for(const name of files)copyFileSync(join(source,name),join(target,name),constants.COPYFILE_EXCL);
 return {project:'synthetic-demo',folder:target,message:'Synthetic demo installed. Run npm run dashboard and open http://127.0.0.1:4173. This example contains no personal footage or speech.'};
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{console.log(JSON.stringify(installDemo(),null,2));}
 catch(error){console.error(error.message);process.exitCode=1;}
}
