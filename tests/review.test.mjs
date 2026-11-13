import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync,realpathSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {randomUUID} from 'node:crypto';
import {prepareReview,readReview,submitReview,acknowledgeReview,suggestedReview} from '../scripts/review-store.mjs';
import {readVisual,saveVisual,validateLayers} from '../scripts/visual-editor.mjs';
import {waitForSubmission} from '../scripts/review.mjs';
import {createDashboard} from '../scripts/dashboard.mjs';
import {studioProject,openNativeStudio} from '../scripts/native-studio.mjs';

const layer={id:'headline',text:'BUILD WITH AI',color:'#ffcc00',fontSize:88,x:.08,y:.15};
function fixture(t){
 const root=realpathSync(mkdtempSync(join(tmpdir(),'studio-review-')));t.after(()=>rmSync(root,{recursive:true,force:true}));
 const put=(name,data)=>{const p=join(root,name);mkdirSync(dirname(p),{recursive:true});writeFileSync(p,typeof data==='object'?JSON.stringify(data):data);return p;};
 put('outputs/reels/demo/plan.json',{title:'Demo reel',shots:[{id:'01',say:'Real spoken words',text_layers:[]}]});
 put('outputs/reels/demo/review.html','<h1>Demo</h1><h3>Take 01</h3>');
 return {root,put,prepare:(stage='plan')=>prepareReview(root,{kind:'reels',id:'demo',stage,document:'outputs/reels/demo/review.html'})};
}

test('feedback is bound to a scene/revision and is consumed by a bounded wait',async t=>{
 const {root,prepare}=fixture(t),r=prepare().request;
 assert.equal((await waitForSubmission(root,'reels','demo',0)).status,'no_submission');
 await assert.rejects(waitForSubmission(root,'reels','demo',46),/45/);
 const id=randomUUID(),event=submitReview(root,'reels','demo',{id,requestId:r.id,action:'feedback',scene:'01',text:'Move the label above my head.'});
 assert.equal(submitReview(root,'reels','demo',{id,requestId:r.id,action:'feedback'}).id,id);
 const result=await waitForSubmission(root,'reels','demo',0);
 assert.equal(result.status,'submitted');assert.equal(result.submission.scene,'01');
 assert.throws(()=>submitReview(root,'reels','demo',{id:randomUUID(),requestId:r.id,action:'approve'}),/Resolve/);
 acknowledgeReview(root,'reels','demo',event.id,'Moved label and generated a fresh review.');
 assert.equal((await waitForSubmission(root,'reels','demo',0)).status,'no_submission');
});

test('plan approval cannot become frame approval and changed documents reject stale clicks',t=>{
 const {root,put,prepare}=fixture(t),plan=prepare().request;
 const approved=submitReview(root,'reels','demo',{id:randomUUID(),requestId:plan.id,action:'approve'});
 assert.equal(approved.stage,'plan');assert.equal(approved.previewId,null);
 assert.throws(()=>prepare('frames'),/preview frames/);
 put('outputs/reels/demo/review.html','Updated review');
 assert.equal(readReview(root,'reels','demo').stale,true);
 acknowledgeReview(root,'reels','demo',approved.id,'Plan accepted.');
 assert.throws(()=>submitReview(root,'reels','demo',{id:randomUUID(),requestId:plan.id,action:'approve'}),/changed/);
 put('outputs/reels/demo/previews/01.png','frame');
 put('outputs/reels/demo/preview.json',{id:'verified-preview-id',files:['outputs/reels/demo/previews/01.png']});
 const frames=prepare('frames').request;
 const action=submitReview(root,'reels','demo',{id:randomUUID(),requestId:frames.id,action:'approve'});
 assert.equal(action.previewId,'verified-preview-id');assert.equal(action.stage,'frames');
 put('outputs/reels/demo/previews/01.png','changed actual frame');
 assert.equal(readReview(root,'reels','demo').stale,true);
});

test('visual edits persist constrained scene fields, preserve speech and reject stale writes/approvals',t=>{
 const {root,prepare}=fixture(t),r=prepare().request,visual=readVisual(root,'reels','demo');
 const value={requestId:r.id,revision:visual.revision,scene:'01',layers:[layer]};
 const saved=saveVisual(root,'reels','demo',value);
 const plan=JSON.parse(readFileSync(join(root,'outputs/reels/demo/plan.json')));
 assert.deepEqual(plan.shots[0].text_layers,[layer]);assert.equal(plan.shots[0].say,'Real spoken words');
 assert.equal(saved.submission.action,'visual_edit');assert.equal(readReview(root,'reels','demo').stale,true);
 assert.throws(()=>saveVisual(root,'reels','demo',value),/changed elsewhere/);
 assert.throws(()=>submitReview(root,'reels','demo',{id:randomUUID(),requestId:r.id,action:'approve'}),/changed/);
 for(const patch of [{color:'red;display:none'},{fontSize:1e8},{x:-1},{text:''},{id:'../escape'}])assert.throws(()=>validateLayers([{...layer,...patch}]));
 assert.throws(()=>validateLayers([layer,layer]),/distinct/);
});

test('single edits and standalone draft plans retain their visual layers',t=>{
 const {root,put}=fixture(t);
 put('outputs/edits/edit/session.json',{source:'inputs/clip.mp4',plan:'outputs/edits/edit/preview-a/plan.json'});
 put('outputs/edits/edit/preview-a/plan.json',{effects:[{fx:'spotlight',start:0,end:1}]});
 let r=prepareReview(root,{kind:'edits',id:'edit'}).request;
 saveVisual(root,'edits','edit',{requestId:r.id,revision:readVisual(root,'edits','edit').revision,scene:'clip',layers:[layer]});
 assert.deepEqual(readVisual(root,'edits','edit').scenes[0].layers,[layer]);
 put('docs/draft.html','<h1>Script</h1><h2>Take 01</h2>');
 r=prepareReview(root,{kind:'plans',id:'draft',document:'docs/draft.html'}).request;
 saveVisual(root,'plans','draft',{requestId:r.id,revision:readVisual(root,'plans','draft').revision,scene:'01',layers:[layer]});
 assert.equal(readReview(root,'plans','draft').stale,true);
 assert.deepEqual(readVisual(root,'plans','draft').scenes[0].layers,[layer]);
 prepareReview(root,{kind:'plans',id:'draft',document:'docs/draft.html'});
 assert.deepEqual(readVisual(root,'plans','draft').scenes[0].layers,[layer]);
 assert.equal(readFileSync(join(root,'docs/draft.html'),'utf8'),'<h1>Script</h1><h2>Take 01</h2>');
});

test('review storage and documents reject traversal, cross-project paths and symlinks',t=>{
 const {root,put}=fixture(t);
 assert.throws(()=>prepareReview(root,{kind:'reels',id:'../escape'}));
 assert.throws(()=>prepareReview(root,{kind:'reels',id:'demo',document:'outputs/reels/other/review.html'}));
 const outside=put('private.html','Private');mkdirSync(join(root,'docs'));
 symlinkSync(outside,join(root,'docs/leak.html'));
 assert.throws(()=>prepareReview(root,{kind:'plans',id:'draft',document:'docs/leak.html'}));
 mkdirSync(join(root,'outputs/.workflow'),{recursive:true});symlinkSync(join(root,'docs'),join(root,'outputs/.workflow/reviews'));
 assert.throws(()=>prepareReview(root,{kind:'reels',id:'demo'}),/symlinks/);
});

test('review HTTP actions require origin, JSON and custom header; no render or acknowledgement endpoint exists',async t=>{
 const {root,prepare}=fixture(t),r=prepare().request;
 const server=createDashboard({root});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 t.after(()=>new Promise(resolve=>{server.closeAllConnections();server.close(resolve);}));
 const base=`http://127.0.0.1:${server.address().port}`,endpoint=base+'/api/reviews/reels/demo/submit';
 const body=JSON.stringify({id:randomUUID(),requestId:r.id,action:'feedback',text:'Larger headline please.'});
 assert.equal((await fetch(endpoint,{method:'POST',body})).status,403);
 const headers={origin:base,'content-type':'application/json','x-dashboard-action':'review'};
 assert.equal((await fetch(endpoint,{method:'POST',headers:{...headers,origin:'https://evil.example'},body})).status,403);
 assert.equal((await fetch(endpoint,{method:'POST',headers,body})).status,200);
 assert.equal((await fetch(endpoint,{method:'POST',headers,body:'x'.repeat(33000)})).status,413);
 for(const action of ['render','ack'])assert.equal((await fetch(base+`/api/reviews/reels/demo/${action}`,{method:'POST',headers,body:'{}'})).status,405);
 const state=await (await fetch(base+'/api/reviews/reels/demo')).json();assert.equal(state.submissions.length,1);
 assert.equal((await fetch(base+'/review/reels/demo')).status,200);
 assert.equal((await fetch(base+'/visual-editor.js')).status,404);
 assert.equal((await fetch(base+'/api/reviews/reels/demo/visual',{method:'POST',headers,body:'{}'})).status,405);
 assert.equal(state.catalogue.filter(t=>t.kind==='music').length,4);
 assert.equal((await fetch(base+'/audio/music-lofi',{headers:{range:'bytes=0-15'}})).status,206);
 assert.equal((await fetch(base+'/audio/not-a-track')).status,404);
 const html=await fetch(base+'/media/outputs/reels/demo/review.html');assert.match(html.headers.get('content-security-policy'),/sandbox;/);
});

test('native Studio uses an existing Hyperframes project and edits invalidate the review',async t=>{
 const {root,put,prepare}=fixture(t);
 put('outputs/reels/demo/plan.json',{renderer:'hyperframes',shots:[{id:'01',say:'Real words'}]});
 put('outputs/reels/demo/hyperframes/index.html','<html><body>Scene</body></html>');
 prepare();const project=studioProject(root,'reels','demo');assert.ok(project.endsWith('/demo/hyperframes'));
 assert.equal(studioProject(root,'edits','demo'),null);
 const result=await openNativeStudio(root,'reels','demo',{execute:(command,args,options,done)=>{
  assert.equal(command,process.execPath);assert.equal(args[2],project);assert.ok(args.includes('--background'));assert.ok(args.includes('--no-open'));assert.equal(options.cwd,project);
  done(null,JSON.stringify({studioUrl:'http://localhost:3002/#project/hyperframes'}),'');
 }});
 assert.equal(result.url,'http://localhost:3002/#project/hyperframes');
 put('outputs/reels/demo/hyperframes/index.html','<html><body>Edited text and colour</body></html>');
 assert.equal(readReview(root,'reels','demo').stale,true);
 await assert.rejects(openNativeStudio(root,'reels','demo',{execute:(_c,_a,_o,done)=>done(null,'https://evil.example/','')}),/local project URL/);
});


test('independent script, scene and frame feedback stays revision-bound and blocks approval across revisions',t=>{
 const {root,put,prepare}=fixture(t);
 put('outputs/reels/demo/previews/frame.png','pixels');
 put('outputs/reels/demo/preview.json',{id:'preview',files:['outputs/reels/demo/previews/frame.png'],frame_details:[{id:'01@0.2',scene:'01',time:.2,file:'outputs/reels/demo/previews/frame.png'}]});
 const r=prepare('frames').request;
 const events=[];
 for(const target of [{scope:'script'},{scope:'scene',scene:'01'},{scope:'frame',frame:'01@0.2',scene:'01'}])events.push(submitReview(root,'reels','demo',{id:randomUUID(),requestId:r.id,action:'feedback',text:'Change this target',...target}));
 assert.equal(readReview(root,'reels','demo').submissions.length,3);
 assert.throws(()=>submitReview(root,'reels','demo',{id:randomUUID(),requestId:r.id,action:'feedback',scope:'frame',frame:'wrong-frame',text:'bad'}),/actual frame/);
 put('outputs/reels/demo/review.html','Refreshed plan');const next=prepare('frames').request;
 assert.notEqual(r.id,next.id);assert.throws(()=>submitReview(root,'reels','demo',{id:randomUUID(),requestId:next.id,action:'approve'}),/Resolve/);
 events.forEach(e=>acknowledgeReview(root,'reels','demo',e.id,'Updated this target'));
 assert.equal(submitReview(root,'reels','demo',{id:randomUUID(),requestId:next.id,action:'approve'}).stage,'frames');
});


test('dashboard opens draft script review and the explicitly recorded frame document',t=>{
 const {root,put}=fixture(t);
 put('outputs/reels/demo/plan.json',{phase:'draft',shots:[{id:'01',expected_say:'Approved wording'}]});
 assert.equal(suggestedReview(root,'reels','demo').request.stage,'script');
 put('outputs/reels/demo/previews/current/review.html','Current reviewed frames');
 put('outputs/reels/demo/previews/newer-but-unreviewed/review.html','Other document');
 put('outputs/reels/demo/previews/current/frame.png','Frame bytes');
 put('outputs/reels/demo/preview.json',{id:'preview',review:'previews/current/review.html',files:['outputs/reels/demo/previews/current/frame.png']});
 const review=suggestedReview(root,'reels','demo','frames');
 assert.equal(review.request.document,'outputs/reels/demo/previews/current/review.html');
 assert.equal(review.request.frames.length,1);
});
