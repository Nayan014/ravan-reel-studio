"""Drafts, source attachment and cached speech analysis for new reel runs."""
import copy
import math
import os
import tempfile
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
    result=detect(sources,plan.get('project_type','reel'))
    plan['source_profiles']=sources
    plan['quality_choices']=result
    if plan.get('profile_choice')!='explicit': plan['output_profile']=result['output']
    return result


def upgrade(folder,plan,settings=None):
    plan.update(pipeline_version=2, renderer='hyperframes', caption_engine='hyperframes', phase='recorded',audio=defaults(settings))
    for shot in plan['shots']: shot['remotion']={'status':'none'}
    quality(folder,plan)


def draft(rw,slug,file,fresh=False):
    data=read_json(Path(file));folder=rw.project(slug)
    if folder.exists():
        if fresh:
            shutil.rmtree(folder)
        else:
            raise ValueError('Project already exists. Pass --fresh to start a clean new project, or resume or attach takes instead.')
    review_path = rw.STUDIO / 'outputs/.workflow/reviews' / rw.PROJECT_KIND / f'{slug}.json'
    if review_path.is_file():
        review_path.unlink()
    shots=data.get('shots',[])
    if not shots or not data.get('title'): raise ValueError('Draft needs a title and shots with expected_say.')
    plan={'version':1,'pipeline_version':2,'renderer':'hyperframes','caption_engine':'hyperframes','phase':'draft',
          'project_type':'video' if rw.PROJECT_KIND=='videos' else 'reel','target_duration':data.get('target_duration'),'sections':data.get('sections',[]),
          'slug':slug,'title':data['title'],'idea':data.get('idea',''),'channel':data.get('channel','Techno Ravan'),
          'language':data.get('language','en'),'style':'flat','palette':'clay','visual_selection':None,'audio':defaults(rw.load_settings()),'shots':[]}
    for i,item in enumerate(shots):
        if not isinstance(item.get('expected_say'),str) or not item['expected_say'].strip(): raise ValueError('Each scene needs the intended spoken script.')
        plan['shots'].append({'id':f'{i+1:02d}','expected_say':item['expected_say'],'say':'','words':[],
            'shooting_note':item.get('shooting_note',''),'estimated_duration':max(1,len(item['expected_say'].split())/2.5),
            'text_confirmed':False,'caption_pages':[],'layout':'full','focus':[.5,.4],
            'vibha':{'status':'pending','effects':[]},'remotion':{'status':'none'}})
    for name in ['raw','assets','working']: (folder/name).mkdir(parents=True,exist_ok=True)
    write_json(folder/'plan.json',plan);rw.make_html(folder,plan)
    return {'project':slug,'stage':'review_script','review':str(folder/'review.html')}


def mapped_scenes(items, files, shots, infos):
    if not isinstance(items,list) or len(items)!=len(shots) or any(not isinstance(item,dict) for item in items):
        raise ValueError('Map every scene to a recording and a [start,end] clip.')
    by_id={str(item.get('id')):item for item in items}
    if set(by_id)!={s['id'] for s in shots}:
        raise ValueError('Mapping IDs must match the scene IDs exactly.')
    result=[]
    for shot in shots:
        item=by_id[shot['id']];name=item.get('source');clip=item.get('clip')
        if name not in files or not isinstance(clip,list) or len(clip)!=2:
            raise ValueError('Choose a source filename and clip [start,end] for every scene.')
        if not all(isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n) for n in clip) or not 0<=clip[0]<clip[1]<=infos[name]['duration']:
            raise ValueError('Scene clip boundaries must be inside the source recording.')
        row=copy.deepcopy(shot)
        for key in ['analysis_signature','source_frame','narration','audition','voice_mode']:
            row.pop(key,None)
        row.update(source=name,source_sha256=digest(files[name]),source_span=clip,clip=clip,
                   say='',words=[],caption_pages=[],text_confirmed=False)
        result.append(row)
    return result


def attach(rw,slug,source,mapping_file=None):
    folder,plan=rw.plan_at(slug)
    if plan.get('phase')!='draft':
        raise ValueError('Only an unrecorded draft can attach takes. Originals are never overwritten.')
    approval=read_json(folder/'script-approval.json') if (folder/'script-approval.json').exists() else {}
    if approval.get('script')!=[s['expected_say'] for s in plan['shots']]:
        raise ValueError('Approve the current script before attaching recordings.')
    source=rw.input_folder(source)
    if source.is_file():
        if source.suffix.lower() not in rw.VIDEO_TYPES:
            raise ValueError('Recording file must be a supported video type.')
        files={source.name: source}
    else:
        files={f.name:f for f in source.iterdir() if f.is_file() and not f.is_symlink() and f.suffix.lower() in rw.VIDEO_TYPES}
    infos={name:probe(path) for name,path in files.items()}
    if not files:
        raise ValueError('No supported footage found.')
    if mapping_file:
        items=read_json(Path(mapping_file))['scenes']
    else:
        numbered={}
        for name in files:
            match=re.search(r'(\d+)$',Path(name).stem)
            ident=f'{int(match[1]):02d}' if match else '01' if len(files)==1 else None
            if ident is None or ident in numbered:
                raise ValueError('Use unique numbered filenames or supply --mapping.')
            numbered[ident]=name
        if set(numbered)!={shot['id'] for shot in plan['shots']}:
            raise ValueError('Take numbers must match the approved scenes. Supply --mapping for continuous footage.')
        items=[{'id':ident,'source':name,'clip':[0,infos[name]['duration']]} for ident,name in numbered.items()]
    shots=mapped_scenes(items,files,plan['shots'],infos)
    used={s['source'] for s in shots}
    if any((folder/'raw'/name).exists() for name in used):
        raise ValueError('An original already exists. Attach aborted.')
    # Prepare copies and quality metadata before committing the recorded plan.
    updated=copy.deepcopy(plan);updated.update(shots=shots,phase='recorded')
    with tempfile.TemporaryDirectory(prefix='.attach-',dir=folder/'working') as tmp:
        staging=Path(tmp);(staging/'raw').mkdir();(staging/'working').mkdir()
        for name in used: shutil.copy2(files[name],staging/'raw'/name)
        quality(staging,updated)
        committed=[]
        try:
            for name in used:
                target=folder/'raw'/name
                os.link(staging/'raw'/name,target);committed.append(target)
            write_json(folder/'plan.json',updated)
        except Exception:
            for target in committed: target.unlink()
            raise
    rw.make_html(folder,updated)
    return {'project':slug,'stage':'analyze_speech','quality':updated['quality_choices']}


def scenes(rw,slug,file):
    folder,plan=rw.plan_at(slug)
    if plan.get('pipeline_version')!=2 or plan.get('phase')=='draft':
        raise ValueError('Import recordings into a current pipeline project before splitting scenes.')
    manifest=read_json(Path(file));items=manifest.get('scenes')
    if not isinstance(items,list) or not items or any(not isinstance(item,dict) for item in items):
        raise ValueError('Provide scenes with id, source and clip [start,end].')
    ids=[item.get('id') for item in items]
    if any(not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',ident) for ident in ids) or len(set(ids))!=len(ids):
        raise ValueError('Scene IDs must be unique letters, numbers, hyphens or underscores.')
    files={f.name:f for f in (folder/'raw').iterdir() if f.is_file() and not f.is_symlink() and f.suffix.lower() in rw.VIDEO_TYPES}
    # Imported recordings are immutable, including when one source feeds many scenes.
    known={shot['source']:shot['source_sha256'] for shot in plan['shots']}
    if any(name not in files or digest(files[name])!=sha for name,sha in known.items()):
        raise ValueError('An imported original changed. Re-import before mapping scenes.')
    infos={name:probe(path) for name,path in files.items()}
    old={shot['id']:shot for shot in plan['shots']}
    proposed=[]
    for item in items:
        row={'id':item['id'],'expected_say':'','layout':'full','focus':[.5,.5],
             'vibha':{'status':'pending','effects':[]},'remotion':{'status':'none'}}
        previous=old.get(item['id'])
        if previous: row['expected_say']=previous.get('expected_say','')
        row['shooting_note']=item.get('shooting_note','')
        proposed.append(row)
    # Keep the approved script separately even when scene boundaries are reorganised.
    script_approval=folder/'script-approval.json'
    if script_approval.is_file():
        plan.setdefault('approved_script',read_json(script_approval)['script'])
    mapped=mapped_scenes(items,files,proposed,infos)
    unchanged=set()
    for index,row in enumerate(mapped):
        previous=old.get(row['id'])
        if previous and previous.get('source')==row['source'] and previous.get('source_span',previous.get('clip'))==row['source_span']:
            mapped[index]=copy.deepcopy(previous)
            unchanged.add(row['id'])
    plan['shots']=mapped
    plan['visual_selection']=None
    audio=plan.setdefault('audio',defaults())
    audio['sfx']=[cue for cue in audio.get('sfx',[]) if cue.get('scene') in unchanged]
    quality(folder,plan);write_json(folder/'plan.json',plan);rw.make_html(folder,plan)
    return {'project':slug,'stage':'analyze_speech','scenes':len(plan['shots'])}


def analyze(rw,slug):
    folder,plan=rw.plan_at(slug)
    if plan.get('phase')=='draft': raise ValueError('Attach the numbered recordings first.')
    out=folder/'working/analysis';out.mkdir(exist_ok=True);jobs=[]
    silent_ids=set()
    for shot in plan['shots']:
        src=folder/'raw'/shot['source'];sha=digest(src)
        if sha!=shot['source_sha256']: raise ValueError('Original footage changed; re-import it before analysis.')
        if shot.get('narration'):
            continue
        if not probe(src)['has_audio']:
            silent_ids.add(shot['id'])
            continue
        wav=out/f'{sha}.wav'
        if not wav.exists(): run(['ffmpeg','-y','-v','error','-i',src,'-vn','-ac','1','-ar','16000',wav])
        job={'wav':str(wav),'cache':str(out/f'{sha}.speech.json'),'source':str(src),'source_sha256':sha,'allow_empty':True}
        if job not in jobs: jobs.append(job)
    manifest=out/'batch.json';write_json(manifest,{'jobs':jobs,'language':plan.get('language','en'),'model':plan.get('speech_model')})
    if jobs: run([runtime(),Path(__file__).with_name('speech_batch.py'),manifest],out/'batch.log')
    uncertain=[];changed=False
    for shot in plan['shots']:
        span=shot.get('source_span',[0,probe(folder/'raw'/shot['source'])['duration']])
        start,end=shot['clip']
        shot_changed=False
        if not shot.get('narration'):
            cache = {} if shot['id'] in silent_ids else read_json(out/f'{shot["source_sha256"]}.speech.json')
            words=[dict(w,s=max(w['s'],span[0]),e=min(w['e'],span[1])) for w in cache.get('words',[]) if span[0]<=(w['s']+w['e'])/2<span[1]]
            if words:
                start=max(span[0],float(words[0]['s'])-.12);end=min(span[1],float(words[-1]['e'])+.18)
                text=' '.join(w['w'] for w in words)
                signature=[cache['signature'],span]
                shot_changed=shot.get('analysis_signature')!=signature
                if shot_changed:
                    shot.pop('voice_mode',None)
                    shot.update(clip=[start,end],say=text,words=[{'text':w['w'],'start':max(0,w['s']-start),'end':w['e']-start} for w in words],
                                caption_pages=[' '.join(text.split()[i:i+6]) for i in range(0,len(text.split()),6)] if plan.get('project_type')=='video' else rw.pages(text),text_confirmed=False,analysis_signature=signature)
                for w in words:
                    if w.get('probability') is not None and w['probability']<.5: uncertain.append({'scene':shot['id'],'start':w['s'],'end':w['e'],'text':w['w']})
            else:
                silent_ids.add(shot['id'])
                # An empty transcript alone cannot authorize muting audible source sound.
                if shot.get('voice_mode') != 'silent':
                    from narration import source_is_silent
                    if source_is_silent(folder/'raw'/shot['source'],span):
                        shot.update(voice_mode='silent',say='',words=[],caption_pages=[],text_confirmed=not shot.get('expected_say'))
                        shot_changed=True
            changed |= shot_changed
        frame=out/f'{shot["id"]}.jpg'
        if shot_changed or not frame.exists(): run(['ffmpeg','-y','-v','error','-ss',str((start+end)/2),'-i',folder/'raw'/shot['source'],'-vf','scale=540:-2','-frames:v','1',frame])
        shot['source_frame']=frame.relative_to(folder).as_posix()
    if changed: plan['visual_selection']=None
    write_json(folder/'plan.json',plan);rw.make_html(folder,plan)
    return {'project':slug,'stage':'verify_transcript_and_choose_visuals','uncertain':uncertain,'scenes_without_detected_speech':sorted(silent_ids),'details':str(out),
            'next':'Listen to uncertain segments. Never substitute the expected script for uncertain speech. Correct say, words and captions together; confirm text before previews.'}
