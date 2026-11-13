import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,realpathSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createServer} from 'node:http';
import {installPlan,launchDashboard,openLocalBrowser,supportedNode} from '../scripts/start.mjs';

function fixture(t){const root=realpathSync(mkdtempSync(join(tmpdir(),'ravan-start-')));t.after(()=>rmSync(root,{recursive:true,force:true}));return root;}
function close(server){return new Promise(resolve=>{server.closeAllConnections();server.close(resolve);});}

test('supported Node selection checks the documented minimum',()=>{
 assert.equal(supportedNode('v22.17.1'),false);assert.equal(supportedNode('22.18.0'),true);assert.equal(supportedNode('24.1.0'),true);assert.equal(supportedNode('20.19.0'),false);
});
test('system install plans install only missing tools and never auto-accept licences',()=>{
 assert.deepEqual(installPlan('darwin',{python:false,ffmpeg:false},new Set()),[]);
 assert.deepEqual(installPlan('darwin',{python:false,ffmpeg:true},new Set(['brew'])),[['brew',['install','ffmpeg']]]);
 const windows=installPlan('win32',{python:true,ffmpeg:true},new Set(['winget']));assert.equal(windows.length,2);assert.ok(windows.every(([,args])=>!args.some(s=>s.startsWith('--accept'))));
 const linux=installPlan('linux',{python:true,ffmpeg:true},new Set(['apt-get','sudo']));assert.equal(linux[0][0],'sudo');assert.ok(linux[1][1].includes('python3-venv'));
 assert.equal(installPlan('linux',{python:true,ffmpeg:false},new Set(['apt-get']),{rootUser:true})[0][0],'apt-get');
 assert.throws(()=>installPlan('darwin',{python:true},new Set()),/Homebrew/);assert.throws(()=>installPlan('linux',{python:true},new Set(['apt-get'])),/administrator/);
});
test('launch binds only loopback, opens the demo after listening, and identifies its workspace',async t=>{
 const root=fixture(t);let url;
 const result=await launchDashboard({root,port:0,opener:async value=>{url=value;const response=await fetch(value.split('/#')[0]+'/api/health');assert.equal(response.status,200);}});
 t.after(()=>close(result.server));assert.equal(result.server.address().address,'127.0.0.1');assert.equal(result.opened,true);assert.equal(url,result.url);assert.match(url,/#reels\/synthetic-demo\/overview$/);
 const health=await(await fetch(result.url.split('/#')[0]+'/api/health')).json();assert.equal(health.app,'ravan-reel-studio');assert.match(health.workspace,/^[a-f0-9]{64}$/);assert.equal('root' in health,false);
});
test('a second launch reuses only the same workspace, avoiding duplicate servers',async t=>{
 const root=fixture(t),first=await launchDashboard({root,port:0,open:false});t.after(()=>close(first.server));
 const again=await launchDashboard({root,port:first.server.address().port,open:false});assert.equal(again.reused,true);assert.equal(again.server,null);assert.equal(again.url,first.url);
 const other=fixture(t),separate=await launchDashboard({root:other,port:first.server.address().port,open:false});t.after(()=>close(separate.server));assert.equal(separate.reused,false);assert.notEqual(separate.url,first.url);
});
test('occupied unrelated ports and unavailable browser openers preserve the existing service',async t=>{
 const unrelated=createServer((_req,res)=>res.end('other app'));await new Promise(resolve=>unrelated.listen(0,'127.0.0.1',resolve));t.after(()=>close(unrelated));
 const result=await launchDashboard({root:fixture(t),port:unrelated.address().port,opener:async()=>{throw Error('headless');}});t.after(()=>close(result.server));assert.notEqual(result.server.address().port,unrelated.address().port);assert.equal(result.opened,false);
 assert.equal(await(await fetch('http://127.0.0.1:'+unrelated.address().port)).text(),'other app');
});
test('browser opening accepts only the generated local demo URL and uses argument arrays',async()=>{
 for(const [platform,expected] of [['darwin','open'],['win32','rundll32.exe'],['linux','xdg-open']]){
  await openLocalBrowser('http://127.0.0.1:4173/#reels/synthetic-demo/overview',{platform,execute:(command,args,options,done)=>{assert.equal(command,expected);assert.ok(args.at(-1).startsWith('http://127.0.0.1:'));assert.equal(options.timeout,15000);done(null);}});
 }
 await assert.rejects(openLocalBrowser('https://example.com'),/local demo/);
});
