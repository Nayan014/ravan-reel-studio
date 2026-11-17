#!/usr/bin/env python3
"""Numbered recordings -> HTML review -> combined Vibha/Remotion previews -> approved export."""
import argparse
import copy
import hashlib
import html
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from video_workflow import digest, probe, run, runtime, effects_root, read_json, write_json
from text_layers import validate_layers, render_layers
from studio_lighting import lighting_effect, validate_lighting

STUDIO = Path(__file__).resolve().parents[1]
ENGINE = STUDIO / 'tools/techno-reel'
VIDEO_TYPES = {'.mov', '.mp4', '.m4v', '.mkv', '.webm', '.avi'}
SCENES = {'Hook', 'Statement', 'Stamp', 'ChatPrompt', 'BigNumber', 'List', 'Compare', 'Meter', 'Swarm', 'Screenshot', 'CTA'}
PROJECT_KIND = 'reels'

CAMERAS = {'lean-in', 'locked-on', 'slow-push', 'over-the-shoulder-zoom'}


def load_settings():
    path = STUDIO / 'settings.json'
    if path.exists():
        try:
            return json.loads(path.read_text('utf-8'))
        except Exception:
            pass
    return {
        'channelName': 'Techno Ravan',
        'creatorName': 'Nayan',
        'niche': 'Developer Tutorials, AI Engineering, Full-Stack Architecture',
        'targetAudience': 'Developers, Software Engineers, AI Builders',
        'youtubeHandle': '@TechnoRavan',
        'instagramHandle': '@technoravan',
        'linkedinUrl': 'https://www.linkedin.com/in/nayanv',
        'bio': 'Bite-sized developer workflows, AI systems, and modern software engineering.',
        'primaryRatio': '9:16 (Portrait Reel)',
        'targetResolution': '4K UHD (2160x3840)',
        'targetFps': 60,
        'aesthetic': 'Developer Dark (Deep Slate, Clean Accents, Terminal Highlighting)',
        'preferredEffectCategory': 'Techno Ravan Effects',
        'tone': 'Direct, punchy, pragmatic, high developer empathy, zero fluff',
        'pacing': 'Fast hook in 0-3s, rapid transitions every 3-5s, code/terminal proof first',
        'noEmDashes': True,
        'callToAction': 'Follow @TechnoRavan for more developer systems',
        'defaultMusicMood': 'Tech Minimal / Coding Focus',
        'voiceDucking': '-18 dB during dialogue',
        'sfxStyle': 'Subtle mechanical clicks, terminal beeps, soft risers',
        'theme': 'system'
    }


def project(slug):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Use a lowercase project slug with letters, numbers and hyphens.')
    path=STUDIO/'outputs'/PROJECT_KIND/slug
    if any(p.is_symlink() for p in [STUDIO/'outputs',STUDIO/'outputs'/PROJECT_KIND,path]):raise ValueError('Project storage cannot use symlinks.')
    return path


def plan_at(slug):
    folder = project(slug)
    return folder, read_json(folder / 'plan.json')


def natural(path):
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', path.name)]


def inputs():
    root = STUDIO / 'inputs'
    items = []
    for f in root.iterdir():
        if f.is_file() and not f.is_symlink() and not f.name.startswith('.') and f.suffix.lower() in VIDEO_TYPES:
            items.append({'folder': f.relative_to(STUDIO).as_posix(), 'takes': 1, 'time': f.stat().st_ctime})
    for p in root.iterdir():
        if p.is_dir() and not p.is_symlink() and not p.name.startswith('.'):
            takes = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_TYPES]
            if takes:
                items.append({'folder': p.relative_to(STUDIO).as_posix(), 'takes': len(takes), 'time': max(f.stat().st_ctime for f in takes)})
    items.sort(key=lambda x: x['time'], reverse=True)
    return [{'folder': x['folder'], 'takes': x['takes']} for x in items[:5]]


class ScriptLines(HTMLParser):
    def __init__(self):
        super().__init__(); self.lines=[]; self.capture=False; self.text=''
    def handle_starttag(self, tag, attrs):
        if tag=='p' and 'spoken' in dict(attrs).get('class','').split():
            self.capture=True; self.text=''
    def handle_data(self, data):
        if self.capture: self.text+=data
    def handle_endtag(self, tag):
        if tag=='p' and self.capture:
            self.lines.append(self.text.strip()); self.capture=False


def input_folder(folder):
    path=Path(folder).expanduser()
    if not path.is_absolute():
        path=STUDIO/path if path.parts and path.parts[0]=='inputs' else STUDIO/'inputs'/path
    source=path.resolve()
    if not source.is_relative_to((STUDIO/'inputs').resolve()) or (not source.is_dir() and not source.is_file()):
        raise ValueError('Choose a recordings folder or video file inside inputs.')
    if any(parent.is_symlink() for parent in [path,*path.parents] if parent.is_relative_to(STUDIO)):
        raise ValueError('Recordings folders cannot use symlinks.')
    return source


def init(slug, folder, title, script_html=None):
    source=input_folder(folder)
    if not source.is_relative_to((STUDIO/'inputs').resolve()) or (not source.is_dir() and not source.is_file()):
        raise ValueError('Choose a reel folder or video file inside this studio inputs folder.')
    dest=project(slug)
    if dest.exists(): raise ValueError('Project already exists. Use status to resume it.')
    if source.is_file():
        if source.suffix.lower() not in VIDEO_TYPES:
            raise ValueError('Recording file must be a supported video type.')
        files=[source]
    else:
        files=sorted([p for p in source.iterdir() if p.is_file() and not p.is_symlink() and p.suffix.lower() in VIDEO_TYPES], key=natural)
    if not files: raise ValueError('No recorded takes found.')
    expected=[]
    if script_html:
        parser=ScriptLines(); parser.feed(Path(script_html).read_text()); expected=parser.lines
        if len(expected)!=len(files): raise ValueError('Script scene count does not match the take count; map the takes manually first.')
    ids=[]
    for f in files:
        match=re.search(r'(\d+)$',f.stem)
        if not match and len(files)!=1: raise ValueError('Use numbered take filenames, such as 1.MOV or take-01.mp4.')
        ids.append(f'{int(match[1]):02d}' if match else '01')
    if len(set(ids))!=len(ids): raise ValueError('Two recordings have the same take number; clarify the preferred take first.')
    infos=[probe(f) for f in files]
    if not all(i['has_audio'] for i in infos): raise ValueError('Every recorded take needs its source audio.')
    (dest/'raw').mkdir(parents=True); (dest/'assets').mkdir(); (dest/'working').mkdir()
    shots=[]
    for idx,(f,ident,info) in enumerate(zip(files,ids,infos)):
        shutil.copy2(f,dest/'raw'/f.name)
        shots.append({'id':ident,'source':f.name,'source_sha256':digest(f),'clip':[0,info['duration']],
                      'expected_say':expected[idx] if expected else '', 'say':'','words':[],
                      'text_confirmed':False,'caption_pages':[], 'layout':'full','focus':[0.5,0.4],
                      'vibha':{'status':'pending','effects':[]},'remotion':{'status':'pending'}})
    settings = load_settings()
    plan={'version':1,'project_type':'video' if PROJECT_KIND=='videos' else 'reel','slug':slug,'title':title,
          'channel': settings.get('channelName', 'Techno Ravan'),
          'creator': settings.get('creatorName', 'Nayan'),
          'handle': settings.get('youtubeHandle', '@TechnoRavan'),
          'niche': settings.get('niche', 'Developer Tutorials, AI Engineering, Full-Stack Architecture'),
          'tone': settings.get('tone', 'Direct, punchy, pragmatic, high developer empathy, zero fluff'),
          'language':'en','style':'flat','palette':'clay',
          'visual_selection':None,'shots':shots}
    from reel_commands import upgrade
    upgrade(dest,plan)
    write_json(dest/'plan.json',plan); make_html(dest,plan)
    return {'project':slug,'stage':'verify_speech','takes':len(shots),'plan':str(dest/'plan.json'),'review':str(dest/'review.html')}


def analyze(slug):
    folder,plan=plan_at(slug)
    if plan.get('pipeline_version')==2:
        import reel_commands
        return reel_commands.analyze(sys.modules[__name__],slug)
    folder,plan=plan_at(slug); out=folder/'working/analysis'; out.mkdir(exist_ok=True)
    for shot in plan['shots']:
        src=folder/'raw'/shot['source']
        wav=out/f'{shot["id"]}.wav'
        run(['ffmpeg','-y','-v','error','-i',src,'-vn','-ac','1','-ar','16000',wav])
        run([runtime(),effects_root()/'scripts/words.py',wav,'--language',plan.get('language','en')],out/f'{shot["id"]}.log')
        words=read_json(wav.with_suffix('.words.json'))
        if not words: raise ValueError(f'No speech found in take {shot["id"]}; review its audio.')
        start=max(0,float(words[0]['s'])-0.12)
        end=min(probe(src)['duration'],float(words[-1]['e'])+0.18)
        shot.update(clip=[start,end],say=' '.join(w['w'] for w in words),
                    words=[{'text':w['w'],'start':max(0,w['s']-start),'end':w['e']-start} for w in words],
                    text_confirmed=False,caption_pages=[])
        shot['caption_pages']=pages(shot['say'])
        frame=out/f'{shot["id"]}.jpg'
        run(['ffmpeg','-y','-v','error','-ss',str((start+end)/2),'-i',src,
             '-vf','scale=540:-2','-frames:v','1',frame])
        shot['source_frame']=frame.relative_to(folder).as_posix()
    plan['visual_selection']=None
    write_json(folder/'plan.json',plan); make_html(folder,plan)
    return {'project':slug,'stage':'verify_transcript_and_choose_visuals','review':str(folder/'review.html'),
            'source_frames':[str(folder/s['source_frame']) for s in plan['shots']],
            'next':'Compare each transcript with its audio and expected script. Correct say, words and caption_pages together; confirm text. Ask the user to choose visuals.'}


def pages(say):
    tokens=say.split()
    return [' '.join(tokens[i:i+3]) for i in range(0,len(tokens),3)]


def catalogue():
    items = {str(x['id']).lower(): {**x, 'category': x.get('category', 'Vibha Effects'), 'author': x.get('author', 'Vibha')} for x in read_json(effects_root()/'references/catalogue.json')}
    custom_path = effects_root() / 'references/custom-catalogue.json'
    if custom_path.is_file():
        for x in read_json(custom_path):
            items[str(x['id']).lower()] = {**x, 'category': x.get('category', 'Techno Ravan Effects'), 'author': x.get('author', 'Techno Ravan')}
    return items


def asset(folder, value):
    path=(folder/value).resolve()
    if not path.is_relative_to((folder/'assets').resolve()) or not path.is_file():
        raise ValueError('Graphics assets must be existing files inside this project assets folder.')
    return path


def effects_for(folder, shot, project_plan=None):
    selected=[]; entries=catalogue(); duration=shot['clip'][1]-shot['clip'][0]
    for effect in shot['vibha'].get('effects',[]):
        item=entries.get(str(effect.get('id')).lower())
        if not item: raise ValueError('Unknown Vibha catalogue number.')
        options=copy.deepcopy(effect.get('options',{}))
        if any(k in options for k in ['fx','look','start','end','id']):
            raise ValueError('Effect identity and timing cannot be overridden in options.')
        start=float(effect['start']); end=float(effect['end'])
        if not all(math.isfinite(x) for x in [start,end]) or not 0<=start<end<=duration+1e-6:
            raise ValueError('Vibha timings must be inside the trimmed shot, relative to its start.')
        row={'fx':item['config']['fx'],'start':start,'end':end,**options}
        if 'look' in item['config']: row['look']=item['config']['look']
        if 'images' in options:
            directory=(folder/options['images']).resolve()
            if not directory.is_relative_to((folder/'assets').resolve()) or not directory.is_dir():
                raise ValueError('Effect image folders must be inside project assets.')
            row['images']=str(directory)
        selected.append(row)
    # Keep camera operations before graphic overlays.
    selected = sorted(selected,key=lambda r: r['fx'] not in CAMERAS)
    if project_plan is None:
        project_plan = read_json(folder/'plan.json') if (folder/'plan.json').is_file() else {}
    config = shot['lighting'] if 'lighting' in shot else project_plan.get('lighting')
    lighting = lighting_effect(config, duration)
    return ([lighting] if lighting else []) + selected


def validate(folder,plan):
    validate_lighting(plan.get('lighting'))
    if plan.get('pipeline_version')==2:
        from media_profile import get_profile
        from audio_library import validate_audio
        get_profile(plan);validate_audio(plan)
        if plan.get('phase')=='draft': raise ValueError('Attach recordings before previewing.')
    if plan.get('style') not in ['flat','print'] or plan.get('palette') not in ['clay','cobalt','forest','mono']:
        raise ValueError('Unsupported graphic style or palette.')
    if not isinstance(plan.get('visual_selection'),str) or not plan['visual_selection'].strip():
        raise ValueError('Visual choices are pending. Record the user selection message in visual_selection before previewing.')
    ids=[]
    for shot in plan['shots']:
        ident=shot['id']; ids.append(ident)
        validate_layers(shot.get('text_layers',[]))
        if not re.fullmatch(r'[A-Za-z0-9_-]+',ident): raise ValueError('Invalid shot identifier.')
        src=(folder/'raw'/shot['source']).resolve()
        if not src.is_relative_to((folder/'raw').resolve()) or not src.is_file(): raise ValueError('Missing or invalid raw source.')
        if digest(src)!=shot['source_sha256']: raise ValueError('A recorded source changed. Re-import and review it.')
        info=probe(src); start,end=shot['clip']
        if not all(isinstance(v,(float,int)) and math.isfinite(v) for v in [start,end]) or not 0<=start<end<=info['duration']+1e-6:
            raise ValueError('Clip boundaries must be inside the source take.')
        duration=end-start
        if not shot.get('text_confirmed') or not shot['say'].strip() or not shot['words']:
            raise ValueError('Verify the actual transcript and word timings before previewing.')
        if shot['say'].split()!=[w['text'] for w in shot['words']]:
            raise ValueError('say and timed words must match exactly.')
        if shot['say'].split()!=' '.join(shot['caption_pages']).split():
            raise ValueError('Caption pages must contain exactly the spoken words.')
        previous=0
        for word in shot['words']:
            a,b=word['start'],word['end']
            if not all(isinstance(v,(float,int)) and math.isfinite(v) for v in [a,b]) or not 0<=a<=b<=duration+0.04 or a<previous:
                raise ValueError('Invalid or unordered word timings.')
            previous=a
        if shot.get('framing','crop') not in ['crop','fit']:
            raise ValueError('Choose crop or fit framing for each scene.')
        focus=shot.get('focus',[0.5,0.4])
        if len(focus)!=2 or not all(isinstance(x,(float,int)) and math.isfinite(x) and 0<=x<=1 for x in focus): raise ValueError('Focus must be two numbers from zero to one.')
        for key in ['vibha','remotion']:
            if shot[key]['status'] not in ['selected','none']: raise ValueError(f'{key} choices are pending in shot {ident}.')
        fx=effects_for(folder,shot,plan)
        graphics_fx=[effect for effect in fx if effect['fx']!='studio-light']
        if shot['vibha']['status']=='none' and graphics_fx: raise ValueError('None cannot include Vibha effects.')
        if shot['vibha']['status']=='selected' and not graphics_fx: raise ValueError('Selected Vibha effects are empty.')
        graphic=shot['remotion']; scene=graphic.get('scene')
        if not isinstance(shot.get('join_note',''),str): raise ValueError('Join notes must be text.')
        if graphic['status']=='selected' and scene not in SCENES: raise ValueError('Choose a bundled Remotion scene.')
        if graphic['status']=='none' and scene: raise ValueError('None cannot include a Remotion scene.')
        if shot['layout'] not in ['full','punch','split','graphic']: raise ValueError('Unsupported shot layout.')
        if shot['layout'] in ['graphic','split'] and graphic['status']!='selected': raise ValueError('Graphic and split layouts need a selected scene.')
        if shot['layout']=='graphic' and graphics_fx: raise ValueError('Vibha effects would be hidden by a full-screen graphic.')
        if shot['layout']=='punch' and any(x['fx'] in CAMERAS for x in fx): raise ValueError('Choose either a crop punch or a Vibha camera effect, avoiding double zoom.')
        for key in ['src','icon']:
            value=graphic.get('props',{}).get(key)
            if value: asset(folder,value)
        if scene=='Screenshot' and not graphic.get('props',{}).get('src'): raise ValueError('Screenshot needs an actual asset.')
    if not ids or len(set(ids))!=len(ids): raise ValueError('Use distinct, nonempty shot identifiers.')


def input_hash(folder):
    if read_json(folder/'plan.json').get('pipeline_version')==2:
        from reel_pipeline import input_hash as current_hash
        return current_hash(folder)
    files=[folder/'plan.json',Path(__file__),ENGINE/'package-lock.json']
    for root in [folder/'raw',folder/'assets',ENGINE/'src',ENGINE/'studio',ENGINE/'public',effects_root()/'scripts',effects_root()/'fonts',effects_root()/'models']:
        files += sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    values=[(str(p.relative_to(STUDIO)),digest(p)) for p in files]
    return hashlib.sha256(json.dumps(values).encode()).hexdigest()


def normalized(folder,shot):
    key=hashlib.sha256(json.dumps([shot['source_sha256'],shot['clip'],shot['focus'],'1080x1920-30-v1']).encode()).hexdigest()[:20]
    target=folder/'working'/f'{shot["id"]}-{key}.mp4'
    if not target.is_file():
        frames=max(1,round((shot['clip'][1]-shot['clip'][0])*30))
        x,y=shot['focus']
        filt=f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-ow)*{x}:(ih-oh)*{y},setsar=1,fps=30'
        run(['ffmpeg','-y','-v','error','-ss',str(shot['clip'][0]),'-i',folder/'raw'/shot['source'],
             '-t',str(frames/30),'-vf',filt,'-frames:v',str(frames),'-c:v','libx264','-preset','fast','-crf','18',
             '-c:a','aac','-ar','48000','-ac','2','-movflags','+faststart',target])
    return target


def copy_public(folder):
    public=folder/'working/public'
    for name in ['fonts','sfx','music']:
        if (ENGINE/'public'/name).is_dir(): shutil.copytree(ENGINE/'public'/name,public/name,dirs_exist_ok=True)
    if (folder/'assets').is_dir(): shutil.copytree(folder/'assets',public/'reels/studio/assets',dirs_exist_ok=True)
    return public


def assemble(folder,plan,final=False):
    public=copy_public(folder); rows=[]; cursor=0; media={}
    for shot in plan['shots']:
        source=normalized(folder,shot); media[shot['id']]=source
        source_rel=f'reels/studio/media/{source.name}'
        target=public/source_rel; target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists(): shutil.copy2(source,target)
        actual=source_rel
        fx=effects_for(folder,shot)
        if final and fx:
            fxplan=folder/'working'/f'{shot["id"]}-effects.json'; write_json(fxplan,{'effects':fx})
            out=public/f'reels/studio/media/{shot["id"]}-effected.mp4'
            run([runtime(),effects_root()/'scripts/fx.py','--plan',fxplan,source,out,'--width','1080'],folder/'working'/f'{shot["id"]}-effects.log')
            actual=out.relative_to(public).as_posix()
        frames=max(1,round((shot['clip'][1]-shot['clip'][0])*30))
        row={'id':shot['id'],'say':shot['say'],'words':shot['words'],'from':cursor,'frames':frames,
             'end':frames/30,'audio':source_rel,'offset':0,'studioMedia':actual,'layout':shot['layout'],
             'captionPages':shot['caption_pages'], 'captions':shot.get('captions_visible',True)}
        if shot.get('text_layers'):
            layer_file=public/f'reels/studio/text-layers/{shot["id"]}.png'
            layer_file.parent.mkdir(parents=True,exist_ok=True)
            render_layers(shot['text_layers']).save(layer_file)
            row['studioTextImage']=layer_file.relative_to(public).as_posix()
        if shot['remotion']['status']=='selected':
            row['scene']=shot['remotion']['scene']; row['props']=copy.deepcopy(shot['remotion'].get('props',{}))
            for k in ['src','icon']:
                if row['props'].get(k): row['props'][k]='reels/studio/'+row['props'][k]
        rows.append(row); cursor+=frames
    return public,{'title':plan['title'],'style':plan['style'],'palette':plan['palette'],
                   'handle':plan.get('handle',''),'host':False,'take':'studio-recordings',
                   'focus':[0.5,0.5],'shots':rows,'durationInFrames':cursor},media


def call_bridge(folder,payload):
    path=folder/'working/render-input.json'; write_json(path,payload)
    run(['node',ENGINE/'studio/bridge.mjs',path],folder/'working/remotion.log')


def preview_digest(record):
    tracked=record['files']+record.get('media_files',[])+record.get('audio_files',[])
    return hashlib.sha256(json.dumps([record['inputs'],[(str(p),digest(Path(p))) for p in tracked]],sort_keys=True).encode()).hexdigest()


def preview(slug):
    folder,plan=plan_at(slug)
    if plan.get('pipeline_version')==2:
        from reel_pipeline import preview as current_preview
        return current_preview(slug)
    if plan.get('renderer','remotion')!='remotion':
        raise ValueError('This reel uses Hyperframes. Preview its local Hyperframes composition; do not add Remotion captions.')
    validate(folder,plan); before=input_hash(folder)
    dest=folder/'previews'/uuid.uuid4().hex[:12]; dest.mkdir(parents=True)
    public,reel,media=assemble(folder,plan); jobs=[]; images={}
    for shot,placed in zip(plan['shots'],reel['shots']):
        duration=placed['frames']/30
        times={min(max(0,duration*0.5),max(0,duration-1/30))}
        fx=effects_for(folder,shot)
        for item in fx:
            for fraction in [0.2,0.6,0.9]: times.add(item['start']+(item['end']-item['start'])*fraction)
        # Opening, midpoint and end also expose animation entrances and exits.
        times.update([min(0.2,max(0,duration-1/30)),max(0,duration-0.1)])
        effects_plan=folder/'working'/f'{shot["id"]}-effects.json'; write_json(effects_plan,{'effects':fx})
        local_frames=sorted({min(placed['frames']-1,max(0,round(t*30))) for t in times})
        still_base=public/f'reels/studio/previews/{dest.name}-{shot["id"]}.png'
        if fx:
            still_base.parent.mkdir(parents=True,exist_ok=True)
            run([runtime(),effects_root()/'scripts/fx.py','--plan',effects_plan,media[shot['id']],still_base,
                 '--still',','.join(str(f/30) for f in local_frames),'--warmup','--width','1080'],
                folder/'working'/f'{shot["id"]}-still.log')
        for i,local_frame in enumerate(local_frames):
            t=local_frame/30
            output=dest/f'{shot["id"]}-{i}.png'; image=None
            if fx:
                still=still_base if len(local_frames)==1 else still_base.with_name(f'{still_base.stem}_{t:.2f}.png')
                image=still.relative_to(public).as_posix()
            jobs.append({'shot':shot['id'],'frame':placed['from']+local_frame,'output':str(output),'image':image})
            images.setdefault(shot['id'],[]).append(output)
    call_bridge(folder,{'mode':'preview','publicDir':str(public),'reel':reel,'jobs':jobs})
    if input_hash(folder)!=before: raise ValueError('Inputs changed during preview. Create a fresh preview.')
    review=dest/'review.html'; make_html(folder,plan,review,images)
    prepared=[str(p) for p in media.values()]
    staged=[str(public/s['studioMedia']) for s in reel['shots']]
    staged += [str(public/s['studioTextImage']) for s in reel['shots'] if s.get('studioTextImage')]
    record={'inputs':before,'files':[str(p) for paths in images.values() for p in paths]+[str(review)],
            'media_files':prepared+staged,'review':str(review)}
    record['id']=preview_digest(record)
    write_json(folder/'preview.json',record)
    make_html(folder,plan,images=images)
    return {'project':slug,'stage':'review_actual_frames','preview_id':record['id'],'review':str(review),'frames':len(jobs)}


def approve(slug,ident,message):
    folder,_=plan_at(slug); record=read_json(folder/'preview.json')
    pending_feedback(slug)
    if not message.strip(): raise ValueError('Record the actual user approval message.')
    if ident!=record['id'] or preview_digest(record)!=ident or input_hash(folder)!=record['inputs']:
        raise ValueError('Preview is stale or changed; review fresh frames before approval.')
    write_json(folder/'approval.json',{'preview_id':ident,'message':message})
    return {'project':slug,'stage':'approved','preview_id':ident}


def approval_check(folder):
    pending_feedback(folder.name)
    if not (folder/'preview.json').is_file() or not (folder/'approval.json').is_file():
        raise ValueError('No approval for the current plan and actual preview frames.')
    record=read_json(folder/'preview.json'); approval=read_json(folder/'approval.json')
    if approval.get('preview_id')!=record['id'] or preview_digest(record)!=record['id'] or input_hash(folder)!=record['inputs']:
        raise ValueError('No approval for the current plan, inputs and actual preview frames.')
    return record


def pending_feedback(slug):
    saved=STUDIO/'outputs/.workflow/reviews'/PROJECT_KIND/f'{slug}.json'
    if saved.is_file() and any(s.get('action')=='feedback' and s.get('status')=='pending' for s in read_json(saved).get('submissions',[])):
        raise ValueError('Resolve and acknowledge submitted feedback before approval or rendering.')


def render(slug):
    folder,plan=plan_at(slug)
    if plan.get('pipeline_version')==2:
        from reel_pipeline import render as current_render
        return current_render(slug)
    if plan.get('renderer','remotion')!='remotion':
        raise ValueError('This reel uses Hyperframes. Follow its recorded review authorization and Hyperframes export path.')
    validate(folder,plan); record=approval_check(folder)
    public,reel,_=assemble(folder,plan,final=True)
    approval_check(folder)
    temp=folder/'working/final.pending.mp4'
    call_bridge(folder,{'mode':'render','publicDir':str(public),'reel':reel,'output':str(temp)})
    approval_check(folder)
    info=probe(temp)
    if abs(info['duration']-reel['durationInFrames']/30)>0.15 or not info['has_audio']:
        raise ValueError('Export validation failed: timing or source audio is missing.')
    run(['ffmpeg','-v','error','-i',temp,'-f','null','-'],folder/'working/decode.log')
    output=folder/'export'/f'{slug}-{record["id"][:12]}.mp4'; output.parent.mkdir(exist_ok=True); temp.replace(output)
    write_json(folder/'export.json',{'file':str(output),'preview_id':record['id'],'duration':info['duration']})
    return {'project':slug,'stage':'exported','file':str(output),'duration':info['duration']}


def option_text(options):
    """Plain review copy; JSON configuration belongs in plan.json, not the user table."""
    def value_text(value):
        if isinstance(value,list): return ' / '.join(value_text(v) for v in value)
        if isinstance(value,dict): return ' · '.join(value_text(v) for v in value.values())
        return str(value)
    rows=[]
    for key,value in options.items():
        if key in ['x','y']: continue
        label={'src':'Image','icon':'Icon','at':'Action cue (seconds)','text':'Text','items':'Items','lines':'Headline'}.get(key,key.replace('_',' ').capitalize())
        rows.append(f'{label}: {value_text(value)}')
    if 'x' in options or 'y' in options:
        x=options.get('x',0.5); y=options.get('y',0.5)
        horizontal='left' if x<0.4 else 'right' if x>0.6 else 'center'
        vertical='upper frame' if y<0.35 else 'lower frame' if y>0.65 else 'middle of frame'
        rows.append(f'Placement: {horizontal}, {vertical}')
    return rows


def make_html(folder,plan,output=None,images=None):
    output=output or folder/'review.html'; images=images or {}; esc=html.escape
    def link(path): return esc(os.path.relpath(path,output.parent))
    takes=[]; rows=[]; cursor=0; human=0; previous=None
    if plan.get('sections'):
        headings=[section if isinstance(section,str) else section.get('title','') for section in plan['sections']]
        takes.append('<aside><h3>Video sections</h3><ol>'+''.join(f'<li>{esc(str(title))}</li>' for title in headings if title)+'</ol></aside>')
    for shot in plan['shots']:
        ident=shot['id']; duration=(shot['clip'][1]-shot['clip'][0]) if shot.get('clip') else shot.get('estimated_duration',4); start=cursor; cursor+=duration
        say=shot['say'] or shot.get('expected_say','') or '[Speech has not been transcribed yet]'
        takes.append(f'<article class="take"><h3>Take {esc(ident)}</h3><p>{esc(say)}</p></article>')
        timing=f'{start:.1f}–{cursor:.1f}s'
        frame={'graphic':'Full-screen Remotion graphic + your recorded voice',
               'split':'Your recording + Remotion split layout',
               'punch':'Your recording · closer crop',
               'full':'Your recording · full frame'}[shot['layout']]
        if shot['layout']!='graphic': human+=duration
        source=f'<b>{esc(frame)}</b><p>Take {esc(ident)}</p>'
        if shot.get('source'): source+=f'<a href="{link(folder/"raw"/shot["source"])}">{esc(shot["source"])}</a>'
        else: source+=f'<p>Record after script approval. {esc(shot.get("shooting_note",""))}</p>'
        if not images and shot.get('source_frame') and (folder/shot['source_frame']).is_file():
            source+=f'<p>Source frame · no effects yet</p><a href="{link(folder/shot["source_frame"])}"><img alt="Source frame before effects" src="{link(folder/shot["source_frame"])}"></a>'
        join=shot.get('join_note','')
        if previous and not join:
            if 'graphic' in [previous['layout'],shot['layout']]: join='Graphic transition covers the change between takes.'
            elif previous['layout']!=shot['layout']: join='Intentional framing change at this take boundary.'
            else: join='Take join to review: consider a crop change or a graphic cover.'
        if join: source+=f'<p><b>Edit join:</b> {esc(join)}</p>'
        for image in images.get(ident,[]): source+=f'<a href="{link(image)}"><img alt="Actual combined preview for scene {esc(ident)}" src="{link(image)}"></a>'
        cc=''.join(f'<span class="cc">{esc(page)}</span>' for page in shot.get('caption_pages',[]) if page not in shot.get('caption_omit_pages',[])) or 'Pending speech verification'
        if shot.get('caption_omit_pages'): cc='<p>No captions during the channel title.</p>'+cc
        if not shot.get('captions_visible', True): cc='None: the main headline carries this opening beat.'
        decision=shot['vibha']; fx='Pending your choice' if decision['status']=='pending' else 'None'
        if decision['status']=='pending':
            if decision.get('none_suggestion'): fx+=f'<p>{esc(decision["none_suggestion"])}</p>'
            for suggestion in decision.get('suggestions',[]):
                item=catalogue()[str(suggestion['id']).lower()]
                sample=effects_root()/item['preview']
                fx+=f'<p><b>{esc(suggestion.get("title","Alternative"))} · #{esc(str(item["id"]))} · {esc(item["name"])}</b></p><p>{esc(suggestion["reason"])}</p>'
                fx+=f'<a href="{link(sample)}"><img alt="Dummy reference sample for effect {esc(str(item["id"]))}; not your video" src="{link(sample)}"></a><small>Dummy reference · not applied</small>'
        if decision.get('effects'):
            fx='<br>'.join(f'<b>#{esc(str(e["id"]))} · {esc(catalogue()[str(e["id"]).lower()]["name"])}</b><p>{e["start"]:.2f}–{e["end"]:.2f}s within this shot</p>'
                          + ''.join(f'<p>{esc(line)}</p>' for line in option_text(e.get('options',{}))) for e in decision['effects'])
        lighting=shot['lighting'] if 'lighting' in shot else plan.get('lighting')
        if validate_lighting(lighting):
            fx='<p><b>Natural studio lighting</b> · soft face key and muted blue/red background, before graphics.</p>'+fx
        if shot.get('reference_note'):
            fx+=f'<p><b>Reference treatment:</b> {esc(str(shot["reference_note"]))}</p>'
        state='' if shot.get('text_confirmed') else '<small>Expected / unverified speech</small>'
        cells=[f'<b>{esc(ident)}</b><p>{timing}</p>',f'<p class="spoken">{esc(say)}</p>'+state,source,cc,fx]
        labels=['Scene / timing','What I say','Picture / source','CC on screen','Effects']
        rows.append('<tr>'+''.join(f'<td data-label="{label}">{value}</td>' for label,value in zip(labels,cells))+'</tr>')
        previous=shot
    template=(STUDIO/'skills/wf-reel-plan/assets/review-template.html').read_text()
    reference=plan.get('reference_style')
    if reference:
        takes.append('<aside><h3>Reference style · '+esc(str(reference['name']))+'</h3><p>'+esc(str(reference['summary']))+'</p><p>Style notes guide the proposed treatments below. Review their actual appearance in your preview frames.</p></aside>')
    result=template.replace('{{TITLE}}',esc(plan['title'])).replace('{{CHANNEL}}',esc(plan.get('channel','Techno Ravan')))
    result=result.replace('{{TAKES}}',''.join(takes)).replace('{{ROWS}}',''.join(rows))
    if not plan.get('visual_selection'):
        summary=f'{cursor:.1f}s timing draft · visual choices pending · source frames before effects'
        if plan.get('proposed_graphic_seconds') is not None and cursor:
            graphics=float(plan['proposed_graphic_seconds'])
            summary+=f' · proposed split: {100*(cursor-graphics)/cursor:.0f}% you / {100*graphics/cursor:.0f}% graphics'
    else:
        summary=f'{cursor:.1f}s planned · {human:.1f}s you / {cursor-human:.1f}s full-screen graphics · final render requires your approval'
    quality=plan.get('output_profile')
    if quality:
        orientation='Landscape' if quality['width']>quality['height'] else 'Portrait'
        summary+=f' · {orientation} {quality["width"]}×{quality["height"]} · {quality["fps"]} FPS · framing reviewed in actual frames'
    elif plan.get('pipeline_version')==2: summary+=' · output profile pending source inspection / explicit choice'
    result=result.replace('{{SUMMARY}}',summary)
    gallery=''
    if plan.get('show_effect_gallery'):
        gallery='<details style="margin-top:24px"><summary><b>Browse all Vibha dummy reference pictures</b></summary><p class="note">These are reference samples, not effects applied to your recordings. The opening looks A, B and C are alternatives; choose one.</p>'
        for i in range(1,7):
            sheet=STUDIO/f'docs/effect-gallery/effects-{i}.jpg'
            gallery+=f'<img style="width:100%;max-width:1050px;height:auto;display:block;margin:14px 0" alt="Vibha reference gallery sheet {i} of 6" src="{link(sheet)}">'
        gallery+='</details>'
    result=result.replace('{{GALLERY}}',gallery)
    port=os.environ.get('DASHBOARD_PORT','4173')
    if not port.isdigit(): port='4173'
    review_url=f'http://127.0.0.1:{port}/review/{folder.parent.name}/{folder.name}'
    result=result.replace('</main>',f'<p><a href="{html.escape(review_url)}">Open interactive review · script, scene and frame feedback and approval</a></p></main>')
    output.write_text(result)
    return output


def doctor():
    checks={'node':shutil.which('node'),'ffmpeg':shutil.which('ffmpeg'),'ffprobe':shutil.which('ffprobe'),
            'effects_python':str(runtime()),'remotion_installed':(ENGINE/'node_modules/remotion/package.json').is_file()}
    if checks['node']:
        checks['node_version']=run(['node','--version']).strip()
        version=tuple(int(x) for x in checks['node_version'].lstrip('v').split('.')[:2])
        checks['node_supported']=version>=(22,18)
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='cmd',required=True)
    sub.add_parser('list'); sub.add_parser('doctor')
    p=sub.add_parser('init');p.add_argument('--project',required=True);p.add_argument('--folder',required=True);p.add_argument('--title',required=True);p.add_argument('--script-html')
    for name in ['draft','attach','quality','profile','audio','approve-script']:
        p=sub.add_parser(name);p.add_argument('--project',required=True)
        if name=='draft': p.add_argument('--file',required=True)
        if name=='attach': p.add_argument('--folder',required=True);p.add_argument('--mapping')
        if name=='audio': p.add_argument('--track',required=True)
        if name=='profile':
            p.add_argument('--width',type=int,required=True);p.add_argument('--height',type=int,required=True);p.add_argument('--fps',required=True)
        if name=='approve-script': p.add_argument('--message',required=True)
    for name in ['analyze','plan','status','preview','approve','render']:
        p=sub.add_parser(name);p.add_argument('--project',required=True)
        if name=='approve': p.add_argument('--preview-id',required=True);p.add_argument('--message',required=True)
    p=sub.add_parser('scenes');p.add_argument('--project',required=True);p.add_argument('--file',required=True)
    for command in sub.choices.values():
        command.add_argument('--kind',choices=['reels','videos'],default='reels')
    args=parser.parse_args()
    global PROJECT_KIND
    PROJECT_KIND=args.kind
    if args.cmd=='list': result={'folders':inputs()}
    elif args.cmd=='doctor': result=doctor()
    elif args.cmd=='init': result=init(args.project,args.folder,args.title,args.script_html)
    elif args.cmd=='analyze': result=analyze(args.project)
    elif args.cmd=='preview': result=preview(args.project)
    elif args.cmd=='approve': result=approve(args.project,args.preview_id,args.message)
    elif args.cmd=='render': result=render(args.project)
    elif args.cmd=='draft':
        import reel_commands
        result=reel_commands.draft(sys.modules[__name__],args.project,args.file)
    elif args.cmd=='attach':
        import reel_commands
        result=reel_commands.attach(sys.modules[__name__],args.project,args.folder,args.mapping)
    elif args.cmd=='scenes':
        import reel_commands
        result=reel_commands.scenes(sys.modules[__name__],args.project,args.file)
    elif args.cmd=='audio':
        from reel_pipeline import choose_music
        result=choose_music(args.project,None if args.track=='none' else args.track)
    elif args.cmd in ['profile','quality','approve-script']:
        import reel_commands
        from media_profile import profile
        folder,plan=plan_at(args.project)
        if args.cmd=='approve-script':
            pending_feedback(args.project)
            if plan.get('phase')!='draft' or not args.message.strip(): raise ValueError('Approve a draft script with the actual approval message.')
            write_json(folder/'script-approval.json',{'script':[s['expected_say'] for s in plan['shots']],'message':args.message})
            result={'stage':'script_approved','project':args.project}
        else:
            if args.cmd=='profile': plan['output_profile']=profile(args.width,args.height,args.fps,plan.get('project_type','reel'));plan['profile_choice']='explicit'
            result=reel_commands.quality(folder,plan);write_json(folder/'plan.json',plan);make_html(folder,plan)
            result['selected']=plan.get('output_profile')
    else:
        folder,plan=plan_at(args.project)
        if args.cmd=='plan': make_html(folder,plan)
        result={'project':args.project,'plan':str(folder/'plan.json'),'review':str(folder/'review.html'),
                'preview':read_json(folder/'preview.json') if (folder/'preview.json').exists() else None,
                'export':read_json(folder/'export.json') if (folder/'export.json').exists() else None}
        if plan.get('pipeline_version')==2:
            record=result['preview']
            result.update(stage=plan.get('phase'),output_profile=plan.get('output_profile'),quality_choice_required=not bool(plan.get('output_profile')),reference_selection=plan.get('reference_selection'),reference_style=plan.get('reference_style'))
            if record:result['preview']={k:record.get(k) for k in ['id','review','mix_sample','output_profile']};result['preview']['frames']=len(record.get('frame_details',[]))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    sys.modules['reel_workflow']=sys.modules[__name__]
    try: main()
    except (ValueError,KeyError,FileNotFoundError,TypeError) as e:
        print(json.dumps({'error':str(e)}),file=sys.stderr);sys.exit(1)
