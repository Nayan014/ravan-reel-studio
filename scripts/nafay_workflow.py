#!/usr/bin/env python3
"""Studio projects, review and approval for Nafay 3D's standalone video editor."""
import argparse
from contextlib import contextmanager
import hashlib
import html
from importlib.metadata import version, PackageNotFoundError
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid

from video_workflow import STUDIO, digest, probe, read_json, write_json, run, runtime
from media_profile import detect, profile, rate, validate_export, inspect_source

VENDOR = STUDIO/'tools/nafay-video-editor'
CATALOGUE = STUDIO/'assets/styles/nafay.json'
VIDEO_TYPES = {'.mp4','.mov','.m4v','.mkv','.avi','.webm'}


def safe(path):
    path = Path(path)
    if not path.is_relative_to(STUDIO):
        raise ValueError('Project storage must stay inside the studio.')
    current = STUDIO
    for part in path.relative_to(STUDIO).parts:
        if part=='..':
            raise ValueError('Invalid project path.')
        current = current/part
        if current.is_symlink():
            raise ValueError('Nafay project and runtime paths cannot use symlinks.')
    return path


def project(slug):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):
        raise ValueError('Use a lowercase project slug with letters, numbers and hyphens.')
    return safe(STUDIO/'outputs/videos'/slug)


def load(slug):
    folder = project(slug)
    plan = read_json(safe(folder/'plan.json'))
    if plan.get('renderer')!='nafay':
        raise ValueError('This project belongs to another editor. Resume its original workflow.')
    for parent in [folder/'raw',folder/'working/nafay']:
        for path in parent.rglob('*'):
            safe(path)
    if digest(safe(folder/'raw'/plan['source']))!=plan['source_sha256']:
        raise ValueError('The imported original changed. Re-import and review it.')
    return folder,plan


@contextmanager
def operation(folder):
    """Serialize writes and release the lock automatically if a process exits."""
    stream = safe(folder/'.nafay.lock').open('a+b')
    locked = False
    try:
        if os.name=='nt':
            import msvcrt
            stream.seek(0);stream.write(b'0');stream.flush();stream.seek(0)
            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locked = True
        yield
    except BlockingIOError as error:
        raise ValueError('Another operation is active for this project. Wait for it to finish.') from error
    finally:
        if locked:
            if os.name=='nt':
                stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                fcntl.flock(stream,fcntl.LOCK_UN)
        stream.close()


def styles():
    return read_json(CATALOGUE)['entries']


def defaults():
    return {'style':'warm-canvas','language':'en','captions':False,'silence':True,
            'mistakes':True,'pause':.3,'min_gap':.6,'graphics':'light','sfx_gain':1.0}


def validate_options(value):
    allowed=set(defaults())|{'model','crop_approved'}
    if not isinstance(value,dict) or set(value)-allowed:
        raise ValueError('Unknown Nafay option. Use the documented options schema.')
    result={**defaults(),**value}
    result['style']=result['style'].removeprefix('nafay:')
    if result['style'] not in {item['upstream_id'] for item in styles()}:
        raise ValueError('Choose one of the seven catalogued Nafay styles.')
    if result['language'] not in ['en','hi','auto'] or result['graphics'] not in ['light','medium','none']:
        raise ValueError('Choose English, Hindi or auto language and light, medium or no graphics.')
    for name in ['captions','silence','mistakes','crop_approved']:
        if name in result and not isinstance(result[name],bool):
            raise ValueError(name+' must be true or false.')
    for name,low,high in [('pause',0,1),('min_gap',.1,5),('sfx_gain',0,1)]:
        number=result[name]
        if not isinstance(number,(int,float)) or isinstance(number,bool) or not math.isfinite(number) or not low<=number<=high:
            raise ValueError('Invalid '+name+'.')
    if result.get('model') is not None and (not isinstance(result['model'],str) or not result['model'].strip()):
        raise ValueError('Choose a speech model name.')
    return result


def work(folder):
    return safe(folder/'working/nafay')


def save_plan(folder,plan):
    write_json(folder/'plan.json',plan)
    write_review(folder,plan)


def write_review(folder,plan):
    esc=html.escape
    template=(STUDIO/'skills/wf-reel-plan/assets/review-template.html').read_text()
    template=template.replace('Remotion graphic','Nafay graphics').replace('Vibha effect','Editor').replace('Remotion:</b>','Nafay:</b>')
    takes=[];rows=[]
    for shot in plan.get('shots',[]):
        say=esc(shot['say'])
        takes.append(f'<article class="take"><h3>Scene {esc(shot["id"])}</h3><p>{say}</p></article>')
        cells=[esc(shot['id']),say,esc(shot.get('shooting_note','')),
               esc(' / '.join(shot.get('caption_pages',[]))) if plan['nafay']['captions'] else 'Off',
               'Nafay 3D',esc(shot.get('hyperframes_note','Plain footage'))]
        labels=['Scene','What I say','Picture / source','Captions','Editor','Nafay graphics']
        rows.append('<tr>'+''.join(f'<td data-label="{label}">{value}</td>' for label,value in zip(labels,cells))+'</tr>')
    cut=safe(work(folder)/'cut_plan.json')
    if cut.is_file():
        data=read_json(cut)
        takes.append('<aside><h3>Proposed cuts</h3><p>'+esc(json.dumps(data['summary'],ensure_ascii=False))+'</p><ul>'+''.join(
            f'<li>{a:.2f}–{b:.2f}s · {esc(str(reason))} · {esc(str(words))}</li>' for a,b,reason,words in data['removed'])+'</ul></aside>')
    out=plan.get('output_profile')
    summary=f'Nafay 3D · {plan["phase"]} · source quality pending'
    if out:
        summary=f'Nafay 3D · {plan["phase"]} · Landscape {out["width"]}×{out["height"]} · {out["fps"]} FPS'
    for name,value in {'TITLE':esc(plan['title']),'CHANNEL':esc(plan.get('channel','Techno Ravan')),
                       'SUMMARY':esc(summary),'TAKES':''.join(takes),'ROWS':''.join(rows),'GALLERY':''}.items():
        template=template.replace('{{'+name+'}}',value)
    port=os.environ.get('DASHBOARD_PORT','4173')
    if not port.isdigit():port='4173'
    template=template.replace('</main>',f'<p><a href="http://127.0.0.1:{port}/review/videos/{folder.name}">Open feedback and approval review</a></p></main>')
    (folder/'review.html').write_text(template)


def initialize(slug,source,title):
    destination=project(slug)
    if destination.exists():
        raise ValueError('Project exists. Resume it or choose another name.')
    source=Path(source).expanduser()
    if not source.parts:raise ValueError('Choose a local video file.')
    if not source.is_absolute():
        source=(STUDIO/source) if source.parts[0]=='inputs' else STUDIO/'inputs'/source
    if source.is_symlink() or not source.is_file() or source.suffix.lower() not in VIDEO_TYPES:
        raise ValueError('Choose one existing local video file.')
    info=inspect_source(source)
    if not info['has_audio']:
        raise ValueError('Nafay editing requires the recording’s source audio.')
    quality=detect([info],'video')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent,prefix='.nafay-import-') as temporary:
        staging=Path(temporary)/'project'
        for name in ['raw','working/nafay','assets','previews','export']:
            (staging/name).mkdir(parents=True,exist_ok=True)
        copied=staging/'raw'/source.name;shutil.copy2(source,copied)
        sha=digest(copied)
        if sha!=digest(source):raise ValueError('Source changed during import.')
        plan={'version':1,'project_type':'video','renderer':'nafay','slug':slug,'title':title,
              'channel':'Techno Ravan','phase':'imported','source':source.name,'source_sha256':sha,
              'source_profiles':[info],'quality_choices':quality,'output_profile':quality['output'],
              'needs_crop':abs(info['width']/info['height']-16/9)>.002,
              'nafay':defaults(),'shots':[]}
        write_json(staging/'plan.json',plan)
        write_json(staging/'working/nafay/edit.json',{'source':str(destination/'raw'/source.name),
                   'studio_output_profile':plan['output_profile']})
        if destination.exists():raise ValueError('Project was created by another operation. Choose another name.')
        staging.rename(destination)
    write_review(destination,plan)
    return {'project':slug,'phase':plan['phase'],'quality':quality,'needs_crop':plan['needs_crop']}


def output_profile(plan):
    out=plan.get('output_profile')
    if not out:raise ValueError('Choose an explicit output profile before processing this footage.')
    if plan.get('needs_crop') and not plan['nafay'].get('crop_approved'):
        raise ValueError('Confirm the landscape centre crop before processing this recording.')
    return profile(out['width'],out['height'],out['fps'],'video')


def validate_video(info,plan,frames):
    out=output_profile(plan)
    validate_export(info,out,frames)
    if rate(info.get('fps_fraction',info['fps']))!=rate(out['fps']):
        raise ValueError('Encoded frame rate differs from the exact approved rate.')


def vendor(folder,plan,script,arguments):
    out=output_profile(plan)
    os.environ['RAVAN_NAFAY_PROFILE']=json.dumps(out)
    os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(safe(VENDOR/'.cache/browsers'))
    os.environ.setdefault('HF_HOME',str(safe(STUDIO/'skills/effects/.cache/huggingface')))
    log=work(folder)/(script+'.log')
    result=run([runtime(),VENDOR/'scripts'/script,*arguments],log)
    return json.loads(result[result.rfind('\n{')+1:])


def fingerprint(folder,plan):
    value={key:value for key,value in plan.items() if key!='phase'}
    entries=[('plan',value)]
    for dependency in ['playwright','faster-whisper']:
        try: installed=version(dependency)
        except PackageNotFoundError: installed='not installed'
        entries.append(('runtime:'+dependency,installed))
    files=[folder/'raw'/plan['source'],Path(__file__),CATALOGUE,STUDIO/'scripts/media_profile.py',
           STUDIO/'skills/effects/requirements-nafay.txt',STUDIO/'skills/effects/requirements-reel.txt']
    files.extend((folder/'assets').rglob('*'))
    files.extend((work(folder)/'assets').rglob('*'))
    files += [work(folder)/name for name in ['transcript.json','transcript_edited.json','edits.json','cut_plan.json','beats.json','story.js','cut.mp4','cut.wav']]
    for name in ['engine','scripts','assets/fonts','styles/'+plan['nafay']['style']]:
        files.extend(sorted((VENDOR/name).rglob('*')))
    for path in files:
        safe(path)
        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':
            entries.append((str(path.relative_to(STUDIO)),digest(path)))
    state_file=work(folder)/'edit.json'
    if state_file.is_file():
        state=read_json(state_file);state.pop('rendered',None)
        entries.append(('edit',state))
    return hashlib.sha256(json.dumps(entries,sort_keys=True).encode()).hexdigest()


def guard_review(folder,stage):
    state=json.loads(run(['node',STUDIO/'scripts/review.mjs','status','--kind','videos','--id',folder.name]))
    if state.get('stale') or state['request']['stage']!=stage:
        raise ValueError('Publish and review the current '+stage+' revision first.')
    if any(item.get('action')=='feedback' and item.get('status')=='pending' for item in state['submissions']):
        raise ValueError('Resolve and acknowledge feedback before approval.')
    return state


def sync_scenes(folder,plan,edited_timeline=False):
    edited=work(folder)/'transcript_edited.json'
    file=edited if edited_timeline and edited.is_file() else work(folder)/'transcript.json'
    if not file.exists():return
    transcript=read_json(file);words=transcript['words'];duration=transcript['duration']
    beats_file=work(folder)/'beats.json'
    beats=read_json(beats_file)['beats'] if beats_file.exists() and edited_timeline else []
    segments=[];cursor=0
    for beat in beats:
        if beat['start']>cursor:segments.append((cursor,beat['start'],'Plain footage'))
        segments.append((beat['start'],beat['end'],beat['description']));cursor=beat['end']
    if cursor<duration:segments.append((cursor,duration,'Plain footage'))
    source_info=plan['source_profiles'][0]
    plan['shots']=[]
    for index,(start,end,description) in enumerate(segments):
        chosen=[word for word in words if start<=(word['s']+word['e'])/2<end]
        text=' '.join(word['w'] for word in chosen)
        plan['shots'].append({'id':str(index+1).zfill(2),'say':text,'expected_say':'','clip':[start,end],
             'source':plan['source'],'source_sha256':plan['source_sha256'],'shooting_note':'Nafay edited-timeline seconds; source audio continues under graphics.',
             'caption_pages':[' '.join(text.split()[i:i+5]) for i in range(0,len(text.split()),5)],
             'layout':'full','focus':[.5,.5],'text_confirmed':True,
             'vibha':{'status':'none','effects':[]},'remotion':{'status':'none'},
             'hyperframes_note':'Nafay · '+description})
    plan['source_profiles']=[source_info for _ in plan['shots']]


def transcribe(folder,plan):
    options=plan['nafay']
    model=options.get('model') or ('small.en' if options['language']=='en' else 'large-v3-turbo')
    key=[plan['source_sha256'],options['language'],model,'faster-whisper-1.2.1-nafay-v1']
    marker=work(folder)/'speech-cache.json'
    if not marker.is_file() or read_json(marker).get('key')!=key or not (work(folder)/'transcript.json').is_file():
        vendor(folder,plan,'transcribe.py',[folder/'raw'/plan['source'],'--work',work(folder),
               '--lang',options['language'],'--model',model,'--device','cpu'])
        write_json(marker,{'key':key})
    plan['phase']='transcribed';sync_scenes(folder,plan);save_plan(folder,plan)
    return {'phase':plan['phase'],'transcript':str(work(folder)/'transcript.txt'),'model':model}


def cut_arguments(folder,plan,dry=False):
    options=plan['nafay'];out=output_profile(plan)
    arguments=[work(folder),'--style',options['style'],'--captions','yes' if options['captions'] else 'no',
               '--height',str(out['height']),'--pause',str(options['pause']),'--min-gap',str(options['min_gap'])]
    if not options['silence']:arguments.append('--no-silence')
    if dry:arguments.append('--dry-run')
    return arguments


def plan_cuts(folder,plan):
    transcript=read_json(work(folder)/'transcript.json')
    edits_file=work(folder)/'edits.json'
    edits=read_json(edits_file) if edits_file.is_file() else {}
    if not plan['nafay']['mistakes'] and (edits.get('remove') or edits.get('remove_times')):
        raise ValueError('Mistake removal is off. Clear proposed removals or confirm enabling it.')
    for item in edits.get('remove',[]):
        start,end=item['from'],item['to']
        if not all(isinstance(i,int) and not isinstance(i,bool) for i in [start,end]) or not 0<=start<=end<len(transcript['words']):
            raise ValueError('Mistake word indices must lie inside the source transcript.')
    for interval in edits.get('remove_times',[]):
        if not isinstance(interval,list) or len(interval)!=2 or not all(isinstance(n,(int,float)) and math.isfinite(n) for n in interval) or not 0<=interval[0]<interval[1]<=transcript['duration']:
            raise ValueError('Manual removals must lie inside the source timeline.')
    summary=vendor(folder,plan,'cut.py',cut_arguments(folder,plan,True))
    plan['phase']='cut_review';sync_scenes(folder,plan);save_plan(folder,plan)
    return {'phase':plan['phase'],'summary':summary,'review':str(folder/'review.html')}


def approve_stage(folder,plan,stage,message):
    if not message.strip():raise ValueError('Record the exact approval message.')
    expected='cut_review' if stage=='cuts' else 'graphics_review'
    if plan['phase']!=expected:raise ValueError('Prepare the current '+stage+' review first.')
    guard_review(folder,'plan')
    write_json(folder/(stage+'-approval.json'),{'inputs':fingerprint(folder,plan),'message':message})
    return {'phase':stage+'_approved','project':folder.name}


def cut(folder,plan):
    approval=read_json(folder/'cuts-approval.json')
    guard_review(folder,'plan')
    if approval['inputs']!=fingerprint(folder,plan):raise ValueError('Cut decisions changed. Review them again.')
    vendor(folder,plan,'cut.py',cut_arguments(folder,plan))
    state=read_json(work(folder)/'edit.json');frames=sum(end-start for start,end in read_json(work(folder)/'cut_plan.json')['keep_frames'])
    state['studio_frame_count']=frames;write_json(work(folder)/'edit.json',state)
    validate_video(probe(work(folder)/'cut.mp4'),plan,frames)
    write_json(work(folder)/'cut-cache.json',{'inputs':cut_key(folder,plan),'video':digest(work(folder)/'cut.mp4'),'audio':digest(work(folder)/'cut.wav')})
    plan['phase']='cut';sync_scenes(folder,plan,True);save_plan(folder,plan)
    return {'phase':plan['phase'],'frames':frames,'transcript':str(work(folder)/'transcript_edited.txt')}


def cut_key(folder,plan):
    options=plan['nafay']
    values=[plan['source_sha256'],output_profile(plan),
            {name:options[name] for name in ['silence','mistakes','pause','min_gap']},
            digest(work(folder)/'transcript.json'),digest(VENDOR/'scripts/cut.py'),digest(VENDOR/'scripts/common.py')]
    edits=work(folder)/'edits.json'
    values.append(digest(edits) if edits.is_file() else None)
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def require_cut(folder,plan):
    marker=work(folder)/'cut-cache.json'
    if not marker.is_file():raise ValueError('Approve and cut this recording first.')
    saved=read_json(marker)
    if saved['inputs']!=cut_key(folder,plan) or saved['video']!=digest(work(folder)/'cut.mp4') or saved['audio']!=digest(work(folder)/'cut.wav'):
        raise ValueError('Source, cuts or output quality changed. Review the cut again.')


def graphics_plan(folder,plan,file):
    require_cut(folder,plan)
    beats=read_json(Path(file))['beats']
    if not isinstance(beats,list):raise ValueError('Provide a chronological beats list.')
    if plan['nafay']['graphics']=='none' and beats:raise ValueError('Graphics are off. Use an empty beats list.')
    duration=read_json(work(folder)/'transcript_edited.json')['duration'];last=0
    for beat in beats:
        start,end=beat['start'],beat['end']
        if not all(isinstance(n,(int,float)) and math.isfinite(n) for n in [start,end]) or not last<=start<end<=duration:
            raise ValueError('Graphics beats must be ordered, non-overlapping and inside the edited timeline.')
        if not isinstance(beat.get('description'),str) or not beat['description'].strip():raise ValueError('Describe every graphics beat.')
        last=end
    if not (work(folder)/'story.js').is_file():raise ValueError('Author story.js before reviewing the graphics plan.')
    write_json(work(folder)/'beats.json',{'beats':beats});plan['phase']='graphics_review'
    sync_scenes(folder,plan,True);save_plan(folder,plan)
    return {'phase':plan['phase'],'review':str(folder/'review.html')}


def preview_id(record):
    files=[*record['files'],record['mix_sample']]
    return hashlib.sha256(json.dumps([record['inputs'],[(name,digest(safe(Path(name)))) for name in files]],sort_keys=True).encode()).hexdigest()


def preview(folder,plan):
    require_cut(folder,plan)
    guard_review(folder,'plan')
    before=fingerprint(folder,plan)
    if read_json(folder/'graphics-approval.json')['inputs']!=before:raise ValueError('Graphics changed. Review the plan again.')
    report=vendor(folder,plan,'render.py',[work(folder),'--check'])
    out=output_profile(plan);fps=float(rate(out['fps']));duration=read_json(work(folder)/'edit.json')['studio_frame_count']/fps
    beats=read_json(work(folder)/'beats.json')['beats'];expected=[[beat['start'],beat['end']] for beat in beats]
    if abs(report['duration']-duration)>1/fps or len(report['spans'])!=len(expected) or any(abs(a-b)>1/fps for span,wanted in zip(report['spans'],expected) for a,b in zip(span,wanted)):
        raise ValueError('story.js duration and spans must match the reviewed graphics plan and cut frame count.')
    total=round(duration*fps)
    moments={min(total-1,round(.2*fps)),total//2,max(0,total-2)}
    for start,end in expected:
        moments.update(min(total-1,max(0,round((start+(end-start)*fraction)*fps))) for fraction in [.2,.55,.85])
    result=vendor(folder,plan,'render.py',[work(folder),'--stills',','.join(f'{moment/fps:.8f}' for moment in sorted(moments)),
                  '--sfx-gain',str(plan['nafay']['sfx_gain'])])
    if fingerprint(folder,plan)!=before:raise ValueError('Inputs changed during preview. Prepare fresh frames.')
    destination=folder/'previews'/uuid.uuid4().hex[:12];destination.mkdir(parents=True)
    files=[];details=[]
    if len(result['stills'])!=len(result['times']) or not result['stills']:
        raise ValueError('The renderer did not return the expected actual frames.')
    for index,(source,time) in enumerate(zip(result['stills'],result['times'])):
        from PIL import Image
        with Image.open(safe(Path(source))) as image:
            if image.size!=(out['width'],out['height']):raise ValueError('Preview dimensions do not match the approved profile.')
        path=destination/f'frame-{index:03d}.png';shutil.copy2(safe(Path(source)),path);files.append(str(path))
        scene=next((s['id'] for s in plan['shots'] if s['clip'][0]<=time<s['clip'][1]),plan['shots'][-1]['id'])
        details.append({'id':f'{scene}@{time:.6f}','scene':scene,'time':time,'file':str(path)})
    sample=destination/'voice-effects.wav';shutil.copy2(safe(Path(result['mix_sample'])),sample)
    record={'inputs':before,'files':files,'frame_details':details,'mix_sample':str(sample),
            'mix_start':result['mix_start'],'review':str(folder/'review.html'),'output_profile':out,'renderer':'nafay'}
    record['id']=preview_id(record);write_json(folder/'preview.json',record)
    return {'phase':'review_actual_frames_and_audio','preview_id':record['id'],'frames':len(files),'mix_sample':str(sample)}


def approval_check(folder,plan):
    require_cut(folder,plan)
    guard_review(folder,'frames')
    record=read_json(folder/'preview.json');approval=read_json(folder/'approval.json')
    if approval.get('preview_id')!=record['id'] or record['id']!=preview_id(record) or record['inputs']!=fingerprint(folder,plan):
        raise ValueError('The source, edit, style or previews changed. Review fresh frames before rendering.')
    return record


def render(folder,plan):
    record=approval_check(folder,plan)
    destination=folder/'export'/f'{folder.name}-{record["id"][:12]}.mp4'
    if not destination.is_file():
        vendor(folder,plan,'render.py',[work(folder),'--out','studio-final.pending.mp4','--sfx-gain',str(plan['nafay']['sfx_gain'])])
        approval_check(folder,plan)
        generated=work(folder)/'studio-final.pending.mp4'
        frames=read_json(work(folder)/'edit.json')['studio_frame_count']
        validate_video(probe(generated),plan,frames)
        run(['ffmpeg','-v','error','-i',generated,'-f','null','-'],work(folder)/'decode.log')
        generated.replace(destination)
    info=probe(destination);frames=read_json(work(folder)/'edit.json')['studio_frame_count']
    validate_video(info,plan,frames);approval_check(folder,plan)
    cover=folder/'export/cover.png';run(['ffmpeg','-y','-v','error','-i',destination,'-frames:v','1',cover])
    write_json(folder/'export.json',{'renderer':'nafay','creator':'Nafay 3D','file':str(destination),
               'project_type':'video','output_profile':plan['output_profile'],'frames':frames,
               'inputs':record['inputs'],'duration':info['duration'],'preview_id':record['id'],'cover':{'png':'export/cover.png'},
               'caption_ready':(folder/'export/caption.txt').is_file(),'decode_check':'passed'})
    return {'phase':'exported','file':str(destination),'output_profile':plan['output_profile']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('styles')
    for name in ['init','configure','profile','transcribe','cut-plan','approve-cuts','cut','plan','approve-plan','preview','approve','render','status']:
        command=sub.add_parser(name);command.add_argument('--project',required=True)
        if name=='init':command.add_argument('--source',required=True);command.add_argument('--title',required=True)
        if name in ['configure','plan']:command.add_argument('--file',required=True)
        if name=='profile':
            command.add_argument('--width',type=int,required=True);command.add_argument('--height',type=int,required=True);command.add_argument('--fps',required=True)
        if name.startswith('approve'):command.add_argument('--message',required=True)
        if name=='approve':command.add_argument('--preview-id',required=True)
    args=parser.parse_args()
    if args.command=='styles':result={'styles':styles()}
    elif args.command=='init':result=initialize(args.project,args.source,args.title)
    else:
        folder,plan=load(args.project)
        with operation(folder):
            folder,plan=load(args.project)
            if args.command=='configure':
                plan['nafay']=validate_options({**plan['nafay'],**read_json(Path(args.file))})
                state=read_json(work(folder)/'edit.json')
                state.update(style=plan['nafay']['style'],captions=plan['nafay']['captions'])
                write_json(work(folder)/'edit.json',state)
                save_plan(folder,plan);result={'options':plan['nafay']}
            elif args.command=='profile':
                plan['output_profile']=profile(args.width,args.height,args.fps,'video')
                if args.width!=int(round(args.height*16/9/2)*2):raise ValueError('Choose an exact 16:9 output width for Nafay graphics.')
                state=read_json(work(folder)/'edit.json');state['studio_output_profile']=plan['output_profile'];write_json(work(folder)/'edit.json',state)
                save_plan(folder,plan);result={'output_profile':plan['output_profile']}
            elif args.command=='transcribe':result=transcribe(folder,plan)
            elif args.command=='cut-plan':result=plan_cuts(folder,plan)
            elif args.command=='approve-cuts':result=approve_stage(folder,plan,'cuts',args.message)
            elif args.command=='cut':result=cut(folder,plan)
            elif args.command=='plan':result=graphics_plan(folder,plan,args.file)
            elif args.command=='approve-plan':result=approve_stage(folder,plan,'graphics',args.message)
            elif args.command=='preview':result=preview(folder,plan)
            elif args.command=='approve':
                guard_review(folder,'frames');record=read_json(folder/'preview.json')
                if not args.message.strip() or args.preview_id!=record['id'] or record['id']!=preview_id(record) or record['inputs']!=fingerprint(folder,plan):
                    raise ValueError('Approve the current actual frames/audio with the exact approval message.')
                write_json(folder/'approval.json',{'preview_id':record['id'],'message':args.message});result={'phase':'approved','preview_id':record['id']}
            elif args.command=='render':result=render(folder,plan)
            else:
                exported=read_json(folder/'export.json') if (folder/'export.json').is_file() else None
                current=exported and exported.get('inputs')==fingerprint(folder,plan)
                result={'project':args.project,'phase':'exported' if current else plan['phase'],
                        'options':plan['nafay'],'output_profile':plan['output_profile'],
                        'plan':str(folder/'plan.json'),'review':str(folder/'review.html'),
                        'export':exported if current else None}
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':
    try:
        main()
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(json.dumps({'error':str(error)},ensure_ascii=False),file=sys.stderr)
        sys.exit(1)
