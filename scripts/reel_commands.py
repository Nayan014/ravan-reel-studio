"""Drafts, source attachment and cached speech analysis for new reel runs."""
import copy
import json
import re
import shutil
from pathlib import Path
from video_workflow import probe, digest, read_json, write_json, run, runtime
from media_profile import detect, profile,inspect_source
from audio_library import defaults


def quality(folder, plan):
    sources=[]
    for shot in plan['shots']:
        cache=folder/'working'/f'{shot["source_sha256"]}.profile.json'
        if not cache.exists():write_json(cache,inspect_source(folder/'raw'/shot['source']))
        sources.append(read_json(cache))
    result=detect(sources)
    plan['source_profiles']=sources
    plan['quality_choices']=result
    if not plan.get('output_profile'): plan['output_profile']=result['output']
    return result


def upgrade(folder,plan):
    plan.update(pipeline_version=2, renderer='hyperframes', caption_engine='hyperframes', phase='recorded',audio=defaults())
    for shot in plan['shots']: shot['remotion']={'status':'none'}
    quality(folder,plan)


def draft(rw,slug,file):
    data=read_json(Path(file));folder=rw.project(slug)
    if folder.exists(): raise ValueError('Project already exists. Resume or attach takes instead.')
    shots=data.get('shots',[])
    if not shots or not data.get('title'): raise ValueError('Draft needs a title and shots with expected_say.')
    plan={'version':1,'pipeline_version':2,'renderer':'hyperframes','caption_engine':'hyperframes','phase':'draft',
          'slug':slug,'title':data['title'],'idea':data.get('idea',''),'channel':data.get('channel','Techno Ravan'),
          'language':data.get('language','en'),'style':'flat','palette':'clay','visual_selection':None,'audio':defaults(),'shots':[]}
    for i,item in enumerate(shots):
        if not isinstance(item.get('expected_say'),str) or not item['expected_say'].strip(): raise ValueError('Each scene needs the intended spoken script.')
        plan['shots'].append({'id':f'{i+1:02d}','expected_say':item['expected_say'],'say':'','words':[],
            'shooting_note':item.get('shooting_note',''),'estimated_duration':max(1,len(item['expected_say'].split())/2.5),
            'text_confirmed':False,'caption_pages':[],'layout':'full','focus':[.5,.4],
            'vibha':{'status':'pending','effects':[]},'remotion':{'status':'none'}})
    for name in ['raw','assets','working']: (folder/name).mkdir(parents=True,exist_ok=True)
    write_json(folder/'plan.json',plan);rw.make_html(folder,plan)
    return {'project':slug,'stage':'review_script','review':str(folder/'review.html')}


def attach(rw,slug,source):
    folder,plan=rw.plan_at(slug)
    if plan.get('phase')!='draft': raise ValueError('Only an unrecorded draft can attach takes. Originals are never overwritten.')
    approval=read_json(folder/'script-approval.json') if (folder/'script-approval.json').exists() else {}
    expected=[s['expected_say'] for s in plan['shots']]
    if approval.get('script')!=expected: raise ValueError('Approve the current script review before attaching recordings.')
    source=Path(source).resolve()
    if not source.is_relative_to((rw.STUDIO/'inputs').resolve()): raise ValueError('Choose a recordings folder inside inputs.')
    files=sorted([f for f in source.iterdir() if f.is_file() and not f.is_symlink() and f.suffix.lower() in rw.VIDEO_TYPES],key=rw.natural)
    mapping={}
    for f in files:
        match=re.search(r'(\d+)$',f.stem)
        if not match or f'{int(match[1]):02d}' in mapping: raise ValueError('Use unique numbered take filenames.')
        mapping[f'{int(match[1]):02d}']=f
    if set(mapping)!={s['id'] for s in plan['shots']}: raise ValueError('Take numbers must match the approved scene numbers.')
    infos={k:probe(v) for k,v in mapping.items()}
    if not all(i['has_audio'] for i in infos.values()): raise ValueError('Every take needs recorded source audio.')
    if any((folder/'raw'/f.name).exists() for f in files): raise ValueError('An original already exists. Attach aborted.')
    for shot in plan['shots']:
        f=mapping[shot['id']];shutil.copy2(f,folder/'raw'/f.name)
        shot.update(source=f.name,source_sha256=digest(f),clip=[0,infos[shot['id']]['duration']])
    plan['phase']='recorded';quality(folder,plan);write_json(folder/'plan.json',plan);rw.make_html(folder,plan)
    return {'project':slug,'stage':'analyze_speech','quality':plan['quality_choices']}


def analyze(rw,slug):
    folder,plan=rw.plan_at(slug)
    if plan.get('phase')=='draft': raise ValueError('Attach the numbered recordings first.')
    out=folder/'working/analysis';out.mkdir(exist_ok=True);jobs=[]
    for shot in plan['shots']:
        src=folder/'raw'/shot['source'];sha=digest(src)
        if sha!=shot['source_sha256']: raise ValueError('Original footage changed; re-import it before analysis.')
        wav=out/f'{sha}.wav'
        if not wav.exists(): run(['ffmpeg','-y','-v','error','-i',src,'-vn','-ac','1','-ar','16000',wav])
        job={'wav':str(wav),'cache':str(out/f'{sha}.speech.json'),'source':str(src),'source_sha256':sha}
        if job not in jobs: jobs.append(job)
    manifest=out/'batch.json';write_json(manifest,{'jobs':jobs,'language':plan.get('language','en'),'model':plan.get('speech_model')})
    run([runtime(),Path(__file__).with_name('speech_batch.py'),manifest],out/'batch.log')
    uncertain=[];changed=False
    for shot in plan['shots']:
        cache=read_json(out/f'{shot["source_sha256"]}.speech.json');words=cache['words']
        if not words: raise ValueError(f'No speech detected in scene {shot["id"]}. Listen to the original.')
        start=max(0,float(words[0]['s'])-.12);end=min(probe(folder/'raw'/shot['source'])['duration'],float(words[-1]['e'])+.18)
        text=' '.join(w['w'] for w in words)
        if shot.get('analysis_signature')!=cache['signature']:
            changed=True
            shot.update(clip=[start,end],say=text,words=[{'text':w['w'],'start':max(0,w['s']-start),'end':w['e']-start} for w in words],
                        caption_pages=rw.pages(text),text_confirmed=False,analysis_signature=cache['signature'])
        for w in words:
            if w.get('probability') is not None and w['probability']<.5: uncertain.append({'scene':shot['id'],'start':w['s'],'end':w['e'],'text':w['w']})
        frame=out/f'{shot["id"]}.jpg'
        if changed or not frame.exists(): run(['ffmpeg','-y','-v','error','-ss',str((start+end)/2),'-i',folder/'raw'/shot['source'],'-vf','scale=540:-2','-frames:v','1',frame])
        shot['source_frame']=frame.relative_to(folder).as_posix()
    if changed: plan['visual_selection']=None
    write_json(folder/'plan.json',plan);rw.make_html(folder,plan)
    return {'project':slug,'stage':'verify_transcript_and_choose_visuals','uncertain':uncertain,'details':str(out),
            'next':'Listen to uncertain segments. Never substitute the expected script for uncertain speech. Correct say, words and captions together; confirm text before previews.'}
