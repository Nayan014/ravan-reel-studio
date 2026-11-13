import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {existsSync} from 'node:fs';
const root=fileURLToPath(new URL('.',import.meta.url));
const env={...process.env,DO_NOT_TRACK:'1',HYPERFRAMES_NO_UPDATE_CHECK:'1',
 HYPERFRAMES_CONFIG_DIR:resolve(root,'.cache/config'),HYPERFRAMES_CACHE_DIR:resolve(root,'.cache/runtime'),PRODUCER_EXPERIMENTAL_FAST_CAPTURE:'false'};
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
if(!env.HYPERFRAMES_BROWSER_PATH&&existsSync(chrome))env.HYPERFRAMES_BROWSER_PATH=chrome;
// Idempotent: saved visual-editor layers feed actual previews and final exports.
if(['render','preview','play','screenshot','export'].includes(process.argv[2])&&!process.argv.some(arg=>['--help','--status','--stop','--list','--kill-all','--context','--selection'].includes(arg))) {
 const python=resolve(root,'../../skills/effects/.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
 const sync=spawnSync(python,[resolve(root,'../../scripts/sync_text_layers.py'),process.cwd()],{encoding:'utf8'});
 if(sync.status!==0){console.error(sync.stderr||sync.error?.message||'Text layer sync failed.');process.exit(sync.status??1);}
}
const r=spawnSync(process.execPath,[resolve(root,'node_modules/hyperframes/bin/hyperframes.mjs'),...process.argv.slice(2)],{stdio:'inherit',env});
process.exit(r.status??1);
