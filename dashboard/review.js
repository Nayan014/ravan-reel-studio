const [, , kind, id] = location.pathname.split('/');
const api = `/api/reviews/${encodeURIComponent(kind)}/${encodeURIComponent(id)}`;
const $ = name => document.getElementById(name);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
const media = name => '/media/' + name.split('/').map(encodeURIComponent).join('/');
let state=null,displayed='',sending=false,connected=false;
const storagePrefix=`reel-feedback:${kind}/${id}:`;
const key=(scope,target)=>`${storagePrefix}${state.request.id}:${scope}:${target}`;
const draft=(scope,target)=>{try{return localStorage.getItem(key(scope,target))||'';}catch{return '';}};
function feedback(scope,target='',scene=''){
 return `<form class="target-feedback" data-scope="${scope}" data-target="${esc(target)}" data-scene="${esc(scene)}"><label>Your feedback · ${scope==='script'?'full script':scope==='frame'?'this frame':'scene '+esc(scene)}</label><textarea aria-label="Feedback on ${scope} ${esc(target)}" maxlength="8000" rows="3" placeholder="Describe what to change here…">${esc(draft(scope,target))}</textarea><button type="submit">Submit feedback</button><span class="saved-draft"></span></form>`;
}
function controls(){
 const blocked=sending||!connected||!state||state.stale;
 document.querySelectorAll('.target-feedback').forEach(form=>{form.querySelector('button').disabled=Boolean(blocked||!form.querySelector('textarea').value.trim());});
 const dirty=[...document.querySelectorAll('.target-feedback textarea')].some(t=>t.value.trim());
 $('approve').disabled=Boolean(blocked||dirty||state?.submissions.some(s=>s.status==='pending'));
 document.querySelectorAll('[data-music]').forEach(button=>{button.disabled=Boolean(blocked);});
}
function audioPanel(r){
 if(!r.audio)return '';
 const tracks=state.catalogue.filter(t=>t.kind==='music');const recommended=tracks.find(t=>t.id===r.audio.recommended_music)||tracks[0];
 const track=t=>`<article class="audio-track"><div><strong>${esc(t.title)}</strong><p>${esc(t.moods.join(' · '))} · ${t.duration.toFixed(1)}s</p><small>${esc(t.author)} · ${esc(t.license)} · <a href="${esc(t.source)}" target="_blank" rel="noreferrer">Source</a></small></div><audio controls preload="none" src="/audio/${encodeURIComponent(t.id)}" aria-label="Play ${esc(t.title)}"></audio><button type="button" data-music="${esc(t.id)}" aria-pressed="${r.audio.music===t.id}">${r.audio.music===t.id?'Selected':'Choose'}</button></article>`;
 const cues=(r.audio.sfx||[]).map(c=>{const t=state.catalogue.find(t=>t.id===c.sound);return t?`<article class="sound-cue">Scene ${esc(c.scene)} · ${esc(t.title)}<audio controls preload="none" src="/audio/${encodeURIComponent(t.id)}" aria-label="Sound cue ${esc(t.title)}"></audio></article>`:'';}).join('');
 return `<h2>Music and sound</h2><h3>Recommended music</h3>${recommended?track(recommended):''}<h3>Other music</h3>${tracks.filter(t=>t!==recommended).map(track).join('')}<button type="button" data-music="none" aria-pressed="${!r.audio.music}">${!r.audio.music?'No music · selected':'No music'}</button><h3>Selected music mixed with your voice</h3>${r.audio.mixSample?`<audio controls preload="metadata" src="${esc(r.audio.mixSample)}" aria-label="Selected music mixed with voice"></audio>`:'<p>A voice mix sample will appear after speech analysis and preview preparation.</p>'}<h3>Suggested sound cues</h3>${cues||'<p>No sound cues selected. Your agent can suggest cues for the scenes.</p>'}<details><summary>Sound effect library · 23 sounds</summary>${state.catalogue.filter(t=>t.kind==='sfx').map(t=>`<article class="sound-cue">${esc(t.title)} · ${esc(t.license)}<audio controls preload="none" src="/audio/${encodeURIComponent(t.id)}" aria-label="Audition ${esc(t.title)}"></audio></article>`).join('')}</details><p class="muted">Playing a track does not approve it. Selecting music creates a fresh review revision.</p>`;
}
function render(){
 const r=state.request;
 $('title').textContent=r.title;$('stage').textContent=r.stage==='frames'?'ACTUAL FRAMES AND AUDIO':r.stage==='script'?'SCRIPT AND SHOOTING PLAN':'PRODUCTION PLAN';
 $('revision').textContent=`Revision ${r.id.slice(0,8)} · ${new Date(r.createdAt).toLocaleString()}`;
 $('native-studio').hidden=!state.studioAvailable;
 $('approve').textContent=r.stage==='frames'?'Approve current frames and audio':r.stage==='script'?'Approve script':'Approve plan and visual choices';
 if(displayed!==r.id){
  const quality=r.outputProfile;
  $('quality').textContent=quality?`Output: ${quality.width>quality.height?'Landscape':'Portrait'}${Math.min(quality.width,quality.height)===2160?' 4K':Math.min(quality.width,quality.height)===1080?' 1080p':''} · ${quality.width}×${quality.height} · ${quality.fps} FPS`:'Output quality will be confirmed from the recordings.';
  $('crop').textContent=quality?'Framing follows the reviewed crop or fit choice. Changing aspect ratio can crop the picture or add padding. The actual frames below show the result.':'';
  $('script').innerHTML=`<h2>Full script</h2>${r.scenes.map(s=>`<p><strong>Scene ${esc(s.id)}</strong> ${esc(s.text)}</p>`).join('')}${feedback('script')}${r.referenceStyle?`<aside><h3>Reference style · ${esc(r.referenceStyle.name)}</h3><p>${esc(r.referenceStyle.summary)}</p><p>Style notes guide the proposed scene treatments. Review their actual appearance in the frames below.</p></aside>`:''}`;
  $('scene-summary').innerHTML=r.scenes.length?`<h2>Scene-by-scene production plan</h2><div class="table-scroll"><table><thead><tr><th>Scene / timing</th><th>Dialogue</th><th>Footage / shooting notes</th><th>Spoken captions</th><th>Vibha effects</th><th>Hyperframes finish</th></tr></thead><tbody>${r.scenes.map(s=>`<tr><td><strong>${esc(s.id)}</strong><p>${s.timeline?s.timeline.map(n=>Number(n).toFixed(2)).join('–')+'s':'Record after approval'}</p></td><td><p>${esc(s.text)}</p>${feedback('scene',s.id,s.id)}</td><td>${esc(s.source)}<p>${esc(s.framing||'')}</p><p>${esc(s.shootingNote)}</p>${s.sourceFrame?`<img class="source-frame" src="${esc(s.sourceFrame)}" alt="Original scene ${esc(s.id)} before effects">`:''}</td><td>${s.captions.map(esc).join(' / ')||'Pending speech verification'}</td><td>${s.effects.status==='pending'?'Choose effects with the agent':s.effects.status==='none'?'None':(s.effects.effects||[]).map(e=>`#${esc(e.id)} · ${esc(e.start)}–${esc(e.end)}s<br>${esc(Object.entries(e.options||{}).map(([k,v])=>k+': '+v).join(' · '))}`).join('<hr>')}</td><td>${esc(s.finish)}${s.referenceNote?`<p><strong>Reference treatment</strong><br>${esc(s.referenceNote)}</p>`:''}</td></tr>`).join('')}</tbody></table></div>`:'';
  $('document').innerHTML=r.document?`<details ${!r.scenes.length?'open':''}><summary>Original HTML plan and visual references</summary><iframe title="Production plan with visual references" class="review-document" sandbox="" src="${esc(media(r.document))}?revision=${r.fingerprint}"></iframe></details>`:'';
  $('frames').innerHTML=r.frames.map(f=>`<figure><a href="${esc(f.url)}" target="_blank" rel="noreferrer"><img loading="lazy" src="${esc(f.url)}" alt="Actual preview ${esc(f.id)}"></a><figcaption>${f.scene?'Scene '+esc(f.scene):esc(f.name)}${f.time!==null?' · '+Number(f.time).toFixed(2)+'s':''}</figcaption>${feedback('frame',f.id,f.scene)}</figure>`).join('');
  $('audio').innerHTML=audioPanel(r);
  displayed=r.id;
 }
 const pending=state.submissions.filter(s=>s.status==='pending');
 $('review-status').textContent=state.stale?'Content changed. The agent must publish a fresh review before approval. Your drafts are retained.':pending.length?`${pending.length} submission(s) saved for the editing agent. You can submit feedback on other scenes and frames independently.`:'Review the current script, scenes and frames. Submit changes here or approve below.';
 $('history').innerHTML=state.submissions.slice().reverse().map(s=>`<article class="feedback-event"><strong>${s.action==='approve'?'Approval':esc(s.scope||'scene')+' '+esc(s.frame||s.scene||'full script')}</strong><p>${esc(s.text)}</p><small>${s.status==='pending'?'Pending':esc(s.result)}${s.requestId!==r.id?' · earlier revision':''}</small></article>`).join('')||'<p>No submissions yet.</p>';
 // Drafts from earlier revisions remain recoverable without silently applying them to changed frames.
 const archived=[];try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith(storagePrefix)&&!k.startsWith(storagePrefix+r.id+':')&&localStorage.getItem(k)?.trim())archived.push([k,localStorage.getItem(k)]);}}catch{}
 $('draft-history').innerHTML=archived.map(([k,v])=>`<article><small>${esc(k.slice(storagePrefix.length))}</small><p>${esc(v)}</p></article>`).join('')||'<p>No earlier drafts.</p>';
 controls();
}
async function refresh(){try{const response=await fetch(api),data=await response.json();if(!response.ok)throw Error(data.error);state=data;connected=true;render();}catch(error){connected=false;$('review-status').textContent=error.message;controls();}finally{setTimeout(refresh,5000);}}
async function post(action,value){const response=await fetch(api+'/'+action,{method:'POST',headers:{'Content-Type':'application/json','X-Dashboard-Action':'review'},body:JSON.stringify(value)});const data=await response.json();if(!response.ok)throw Error(data.error);return data;}
document.addEventListener('input',event=>{const form=event.target.closest('.target-feedback');if(!form)return;try{localStorage.setItem(key(form.dataset.scope,form.dataset.target),event.target.value);}catch{}form.querySelector('.saved-draft').textContent='Draft saved on this device';controls();});
document.addEventListener('submit',async event=>{const form=event.target.closest('.target-feedback');if(!form)return;event.preventDefault();if(sending)return;sending=true;controls();try{const value=await post('submit',{id:crypto.randomUUID(),requestId:state.request.id,action:'feedback',scope:form.dataset.scope,scene:form.dataset.scene,frame:form.dataset.scope==='frame'?form.dataset.target:'',text:form.querySelector('textarea').value});state.submissions.push(value);try{localStorage.removeItem(key(form.dataset.scope,form.dataset.target));}catch{}form.querySelector('textarea').value='';render();}catch(error){$('review-status').textContent=error.message;}finally{sending=false;controls();}});
document.addEventListener('click',async event=>{const button=event.target.closest('[data-music]');if(!button||sending)return;sending=true;controls();$('review-status').textContent='Preparing the selected music and voice sample locally…';try{await post('music',{requestId:state.request.id,track:button.dataset.music==='none'?null:button.dataset.music});const response=await fetch(api);state=await response.json();render();}catch(error){$('review-status').textContent=error.message;}finally{sending=false;controls();}});
$('approve').addEventListener('click',async()=>{if(sending)return;sending=true;controls();try{state.submissions.push(await post('submit',{id:crypto.randomUUID(),requestId:state.request.id,action:'approve',text:''}));render();}catch(error){$('review-status').textContent=error.message;}finally{sending=false;controls();}});
$('launch-studio').addEventListener('click',async()=>{const button=$('launch-studio');button.disabled=true;try{const data=await post('studio',{});$('studio-link').href=data.url;$('studio-link').hidden=false;$('studio-status').textContent='Studio ready. Publish fresh actual frames after editing.';}catch(error){$('studio-status').textContent=error.message;}finally{button.disabled=false;}});
if(kind!=='plans')$('back-link').href=`/#${kind}/${encodeURIComponent(id)}/plan`;
refresh();
