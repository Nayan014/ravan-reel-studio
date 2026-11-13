// One foreground process: prepare the local reel runtime, install the demo, open it.
import {spawn,spawnSync,execFile} from 'node:child_process';
import {createHash} from 'node:crypto';
import {existsSync,lstatSync,mkdirSync,readFileSync,realpathSync,writeFileSync} from 'node:fs';
import {delimiter,dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createDashboard,workspaceId} from './dashboard.mjs';
import {installDemo} from './install-demo.mjs';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export function supportedNode(version){
 const [major,minor]=version.replace(/^v/,'').split('.').map(Number);return major>22||major===22&&minor>=18;
}

function run(command,args,{root=ROOT,env=process.env}={}){
 return new Promise((done,fail)=>{
  const child=spawn(command,args,{cwd:root,env,stdio:'inherit',shell:false,windowsHide:true});
  const interrupt=()=>child.kill('SIGINT'),terminate=()=>child.kill('SIGTERM');
  process.once('SIGINT',interrupt);process.once('SIGTERM',terminate);
  const clean=()=>{process.removeListener('SIGINT',interrupt);process.removeListener('SIGTERM',terminate);};
  child.once('error',error=>{clean();fail(error);});
  child.once('exit',(code,signal)=>{clean();code===0?done():fail(Error(signal?`Stopped (${signal}).`:`${command} exited with code ${code}. See the output above; rerun npm start after fixing it.`));});
 });
}

function probe(command,args,env){
 const result=spawnSync(command,args,{env,encoding:'utf8',timeout:15000,windowsHide:true});
 return result.status===0;
}

function safeDirectory(root,path){
 let current=root;
 for(const part of path.slice(root.length+1).split(/[\\/]/)){
  current=join(current,part);if(lstatSync(current,{throwIfNoEntry:false})?.isSymbolicLink())throw Error(`Setup refuses a symlinked runtime folder: ${current}`);
 }
}

export function installPlan(platform,{python,ffmpeg},available,{rootUser=false}={}){
 if(!python&&!ffmpeg)return [];
 if(platform==='darwin'){
  if(!available.has('brew'))throw Error('Install Homebrew (https://brew.sh), or install Python3.12/3.13 and ffmpeg yourself. Then rerun npm start.');
  return [['brew',['install',...(python?['python@3.13']:[]),...(ffmpeg?['ffmpeg']:[])]]];
 }
 if(platform==='win32'){
  if(!available.has('winget'))throw Error('Install Python3.13 and ffmpeg, or enable Windows Package Manager (winget). Then reopen your terminal and rerun npm start.');
  return [...(python?[['winget',['install','--exact','--id','Python.Python.3.13','--source','winget']]]:[]),...(ffmpeg?[['winget',['install','--exact','--id','Gyan.FFmpeg','--source','winget']]]:[])];
 }
 if(platform==='linux'&&available.has('apt-get')){
  if(!rootUser&&!available.has('sudo'))throw Error('Install python3, python3-venv and ffmpeg with administrator access, then rerun npm start.');
  const prefix=rootUser?[]:['sudo'];
  return [['apt-get',['update']],['apt-get',['install','-y',...(python?['python3','python3-venv']:[]),...(ffmpeg?['ffmpeg']:[])]]].map(([cmd,args])=>prefix.length?[prefix[0],[cmd,...args]]:[cmd,args]);
 }
 throw Error('Install compatible Python3.12/3.13 and ffmpeg/ffprobe with your system package manager, then rerun npm start. See docs/SETUP.md.');
}

function findPython(env,platform,venv){
 const check=['-c','import sys; sys.exit(0 if sys.version_info[:2] >= (3,10) else 1)'];
 const options=[...(existsSync(venv)?[[venv,[]]]:[]),...(platform==='win32'?[['py',['-3.13']],['py',['-3.12']],['py',['-3']]]:[['python3.12',[]],['python3.13',[]],['python3.11',[]],['python3.10',[]],['python3',[]]])];
 return options.find(([cmd,args])=>probe(cmd,[...args,...check],env));
}

function setupEnvironment(root){
 const env={...process.env};
 const extra=process.platform==='win32'?[env.LOCALAPPDATA&&join(env.LOCALAPPDATA,'Microsoft/WinGet/Links'),env.LOCALAPPDATA&&join(env.LOCALAPPDATA,'Programs/Python/Python313')]:['/opt/homebrew/bin','/usr/local/bin','/opt/homebrew/opt/python@3.13/bin','/usr/local/opt/python@3.13/bin'];
 // Keep the running Node ahead of global versions; PATH changes are process-local.
 env.PATH=[dirname(process.execPath),...extra.filter(Boolean),env.PATH||''].join(delimiter);
 env.PIP_CACHE_DIR=join(root,'skills/effects/.cache/pip');env.MPLCONFIGDIR=join(root,'skills/effects/.cache/matplotlib');
 env.HF_HOME ||= join(root,'skills/effects/.cache/huggingface');env.HF_HUB_DISABLE_TELEMETRY='1';
 return env;
}

export async function prepareWorkspace(root=ROOT,{log=console.log}={}){
 root=realpathSync(root);const env=setupEnvironment(root),platform=process.platform;
 const effects=join(root,'skills/effects'),hf=join(root,'tools/hyperframes'),venv=join(effects,'.venv',platform==='win32'?'Scripts/python.exe':'bin/python');
 for(const name of ['.cache/start/hyperframes.sha256','skills/effects/.venv','skills/effects/.cache','tools/hyperframes/node_modules','tools/hyperframes/.cache'])safeDirectory(root,join(root,name));
 let python=findPython(env,platform,venv);
 const missing={python:!python,ffmpeg:!probe('ffmpeg',['-version'],env)||!probe('ffprobe',['-version'],env)};
 log('[1/5] Checking Python and ffmpeg…');
 const available=new Set(['brew','winget','apt-get','sudo'].filter(cmd=>probe(cmd,['--version'],env)));
 for(const [command,args] of installPlan(platform,missing,available,{rootUser:process.getuid?.()===0}))await run(command,args,{root,env});
 python=findPython(env,platform,venv);
 if(!python||!probe('ffmpeg',['-version'],env)||!probe('ffprobe',['-version'],env))throw Error('Python or ffmpeg is still unavailable. Reopen your terminal after system installation and rerun npm start.');
 log('[2/5] Preparing the effects and speech environment…');
 if(platform!=='win32')await run('bash',[join(effects,'scripts/setup.sh'),'--reel'],{root,env});
 else{
  if(!existsSync(venv))await run(python[0],[...python[1],'-m','venv',join(effects,'.venv')],{root,env});
  const base=probe(venv,['-c','import mediapipe,cv2,PIL,numpy'],env),speech=probe(venv,['-c','import faster_whisper;from importlib.metadata import version;assert version("faster-whisper")=="1.2.1"'],env);
  if(!base||!speech)await run(venv,['-m','pip','install','-r',join(effects,'requirements-reel.txt')],{root,env});
  if(!probe(venv,['-c','import mediapipe,cv2,PIL,numpy'],env)||!probe(venv,['-c','import faster_whisper'],env))throw Error('The Python environment is incomplete. See the installation output.');
 }
 log('[3/5] Preparing Hyperframes and Chrome/Chromium…');
 const cache=join(root,'.cache/start');mkdirSync(cache,{recursive:true});
 const signature=createHash('sha256').update(readFileSync(join(hf,'package.json'))).update(readFileSync(join(hf,'package-lock.json'))).digest('hex');
 const stamp=join(cache,'hyperframes.sha256'),wrapper=join(hf,'hyperframes.mjs');
 const ready=existsSync(stamp)&&readFileSync(stamp,'utf8')===signature&&probe(process.execPath,[wrapper,'--version'],env);
 if(!ready){
  const npm=process.env.npm_execpath;if(!npm||!existsSync(npm))throw Error('Run this launcher with npm start so npm can install the local renderer.');
  await run(process.execPath,[npm,'--prefix',hf,'ci'],{root,env});writeFileSync(stamp,signature);
 }
 await run(process.execPath,[wrapper,'browser','ensure'],{root,env});
 log('[4/5] Caching the default English speech model (first run may download it)…');
 await run(venv,[join(root,'scripts/prepare-speech.py')],{root,env});
 log('[5/5] Loading the synthetic demo…');
 const target=join(root,'outputs/reels/synthetic-demo');
 if(existsSync(target)){safeDirectory(root,target);if(!lstatSync(target).isDirectory())throw Error('synthetic-demo is occupied by a file. Move it yourself, then rerun npm start.');log('Existing synthetic-demo project kept as-is.');}
 else installDemo(root);
 return {root,env};
}

export function openLocalBrowser(url,{platform=process.platform,execute=execFile}={}){
 if(!/^http:\/\/127\.0\.0\.1:\d+\/#reels\/synthetic-demo\/overview$/.test(url))return Promise.reject(Error('Only the local demo URL may be opened.'));
 const [command,args]=platform==='darwin'?['open',[url]]:platform==='win32'?['rundll32.exe',['url.dll,FileProtocolHandler',url]]:['xdg-open',[url]];
 return new Promise((done,fail)=>execute(command,args,{timeout:15000,windowsHide:true},error=>error?fail(error):done()));
}

export async function launchDashboard({root=ROOT,port=Number(process.env.DASHBOARD_PORT||4173),open=true,opener=openLocalBrowser}={}){
 root=realpathSync(root);
 if(!Number.isInteger(port)||port<0||port>65535)throw Error('DASHBOARD_PORT must be a valid port.');
 const identity=workspaceId(root);
 for(let attempt=0;attempt<10;attempt++){
  const candidate=port===0?0:port+attempt;if(candidate>65535)break;
  const server=createDashboard({root});
  const error=await new Promise(done=>{server.once('error',done);server.listen(candidate,'127.0.0.1',()=>done(null));});
  let reused=false,actualPort;
  if(error){
   if(error.code!=='EADDRINUSE')throw error;
   try{const response=await fetch(`http://127.0.0.1:${candidate}/api/health`,{signal:AbortSignal.timeout(1500)}),data=await response.json();reused=response.ok&&data.app==='ravan-reel-studio'&&data.workspace===identity;}catch{}
   if(!reused)continue;actualPort=candidate;
  }else actualPort=server.address().port;
  const url=`http://127.0.0.1:${actualPort}/#reels/synthetic-demo/overview`;
  let opened=false;
  if(open){try{await opener(url);opened=true;}catch{console.log('Could not launch a browser here. Open the printed URL manually.');}}
  return {url,server:reused?null:server,reused,opened};
 }
 throw Error('No available dashboard port. Set DASHBOARD_PORT and rerun npm start.');
}

async function main(){
 const args=process.argv.slice(2);if(args.some(arg=>arg!=='--no-open'))throw Error('Usage: npm start [-- --no-open]');
 if(!supportedNode(process.version)){
  if(process.env.RAVAN_MANAGED_NODE)throw Error('Could not select Node22.18+. Install a supported Node version and rerun npm start.');
  const npm=process.env.npm_execpath;if(!npm)throw Error('Use npm start, or install Node22.18+ first.');
  console.log('Preparing an isolated Node22 runtime; your global Node installation is unchanged…');
  await run(process.execPath,[npm,'exec','--prefer-offline','--yes','--package=node@22','--','node',fileURLToPath(import.meta.url),...args],{env:{...process.env,RAVAN_MANAGED_NODE:'1'}});return;
 }
 console.log('Ravan Reel Studio · setup and launch\n');
 const prepared=await prepareWorkspace();
 const result=await launchDashboard({root:prepared.root,open:!args.includes('--no-open')});
 console.log(`\n${result.reused?'Dashboard already running':'Dashboard ready'} · ${result.url}\n${result.server?'Keep this terminal open. Ctrl+C stops this dashboard.':'The existing dashboard was reused.'}`);
 if(result.server){const stop=()=>{result.server.closeAllConnections();result.server.close(()=>process.exit(0));};process.once('SIGINT',stop);process.once('SIGTERM',stop);}
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))main().catch(error=>{console.error(`\nSetup stopped: ${error.message}`);process.exitCode=1;});
