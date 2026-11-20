"""Version 2: approved Vibha footage -> editable Hyperframes -> checked delivery."""
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid
from video_workflow import STUDIO, run, runtime, effects_root, read_json, write_json, digest, probe
from media_profile import get_profile, frames_for, rate, validate_export
from audio_library import prepare_audio, validate_audio, audio_file, digest_key


def api():
    import reel_workflow
    return reel_workflow


def timeline(plan):
    output=get_profile(plan);fps=float(rate(output['fps']));cursor=0;rows=[]
    for shot in plan['shots']:
        frames=frames_for(shot['clip'][1]-shot['clip'][0],output)
        rows.append({'id':shot['id'],'from':cursor,'frames':frames,'start':cursor/fps,'duration':frames/fps})
        cursor+=frames
    return rows


def normalize(folder,shot,output):
    key=digest_key([shot['source_sha256'],shot['clip'],shot.get('focus',[.5,.4]),shot.get('framing','crop'),folder.parent.name,output,'normalize-v4'])
    target=folder/'working/normalized'/f'{shot["id"]}-{key}.mp4';target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        count=frames_for(shot['clip'][1]-shot['clip'][0],output);duration=count/float(rate(output['fps']))
        x,y=shot.get('focus',[.5,.4]);w,h=output['width'],output['height']
        if shot.get('framing','crop')=='fit':
            vf=f'scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={output["fps"]}'
        else:
            vf=f'scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}:(iw-ow)*{x}:(ih-oh)*{y},setsar=1,fps={output["fps"]}'
        pending=target.with_name(target.stem+'.pending.mp4')
        cmd = ['ffmpeg','-y','-v','error','-ss',str(shot['clip'][0]),'-i',folder/'raw'/shot['source']]
        audio_stream = '0:a:0'
        if not probe(folder/'raw'/shot['source'])['has_audio']:
            cmd += ['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
            audio_stream = '1:a:0'
        run(cmd + ['-map','0:v:0','-map',audio_stream,'-vf',vf,'-t',str(duration),
                   '-af',f'apad,atrim=duration={duration}','-c:v','libx264','-preset','fast','-crf','16',
                   '-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2','-movflags','+faststart',pending])
        validate_export(probe(pending),output,count);pending.replace(target)
    return target


def input_hash(folder,visual_only=False):
    plan=read_json(folder/'plan.json');value=dict(plan)
    if visual_only: value.pop('audio',None)
    values=[('plan',value)]
    for root in [folder/'raw',folder/'assets',effects_root()/'scripts',effects_root()/'fonts',effects_root()/'models']:
        if root.is_symlink():raise ValueError('Production inputs cannot use symlinks.')
        for path in sorted(root.rglob('*')):
            if path.is_symlink():raise ValueError('Production inputs cannot use symlinks.')
            if path.is_file() and '__pycache__' not in path.parts and not any(p.startswith('.') for p in path.relative_to(root).parts):
                values.append((str(path),digest(path)))
    for name in ['reel_workflow.py','reel_pipeline.py','media_profile.py','audio_library.py','narration.py']:
        path=Path(__file__).with_name(name);values.append((name,digest(path)))
    if (folder/'hyperframes').is_symlink():raise ValueError('Hyperframes inputs cannot use symlinks.')
    for path in sorted((folder/'hyperframes').rglob('*')):
        if path.is_symlink():raise ValueError('Hyperframes inputs cannot use symlinks.')
        if not path.is_file() or any(x.startswith('.') or x=='node_modules' for x in path.relative_to(folder/'hyperframes').parts): continue
        if path.suffix.lower() not in ['.html','.css','.js','.mjs','.json','.ttf','.svg']: continue
        content=path.read_bytes()
        if visual_only and path.name=='index.html': content=re.sub(b'<!-- STUDIO AUDIO START -->.*?<!-- STUDIO AUDIO END -->',b'',content,flags=re.S)
        values.append((str(path),hashlib.sha256(content).hexdigest()))
    lock=STUDIO/'tools/hyperframes/package-lock.json'
    if lock.exists(): values.append(('hyperframes-runtime',digest(lock)))
    if not visual_only:
        audio=validate_audio(plan)
        for ident in sorted(set(([audio['music']] if audio['music'] else [])+[c['sound'] for c in audio['sfx']])):
            values.append((ident,digest(audio_file(ident))))
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def copy_changed(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists() or digest(source)!=digest(target): shutil.copyfile(source,target)


def managed_write(folder,path,text,manifest):
    """Regenerate managed code; preserve independently authored Studio changes."""
    name=path.relative_to(folder).as_posix();old=manifest.get(name)
    if path.exists() and (old is None or digest(path)!=old): return
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text()!=text: path.write_text(text)
    manifest[name]=digest(path)


def caption_source(plan,placed,output):
    scale=min(output['width'],output['height'])/1080
    landscape=output['width']>output['height']
    font_size=(48 if landscape else 64)*scale
    groups=[];cues=[]
    for shot,row in zip(plan['shots'],placed):
        if not shot.get('captions_visible',True): continue
        cursor=0;pages=shot['caption_pages']
        for i,page in enumerate(pages):
            count=len(page.split());words=shot['words'][cursor:cursor+count];cursor+=count
            if page in shot.get('caption_omit_pages',[]): continue
            start=row['start']+(words[0]['start'] if words else 0)
            end=row['start']+(shot['words'][cursor]['start'] if cursor<len(shot['words']) else row['duration'])
            if shot.get('narration') and words:
                end=row['start'] + min(words[-1]['end'], row['duration'])
            ident=f'caption-{shot["id"]}-{i}'
            groups.append(f'<div id="{ident}" class="caption">{html.escape(page)}</div>')
            cues.append(f'tl.set("#{ident}",{{opacity:1}},{start:.12f}).set("#{ident}",{{opacity:0}},{end:.12f});')
    w,h=output['width'],output['height']
    return f'<template><style>@font-face{{font-family:StudioInter;src:url(assets/fonts/Inter.ttf);font-weight:100 900}}#root{{position:absolute;inset:0;width:{w}px;height:{h}px;pointer-events:none}}.caption{{position:absolute;top:{h*.76}px;left:{w*.08}px;width:{w*.84}px;font-family:StudioInter,sans-serif;font-size:{font_size}px;font-weight:800;line-height:1.15;color:white;text-align:center;text-wrap:balance;opacity:0;-webkit-text-stroke:{2*scale}px #101319;paint-order:stroke fill;text-shadow:0 {3*scale}px {6*scale}px #000}}</style><div id="root" data-composition-id="captions" data-width="{w}" data-height="{h}">{"".join(groups)}</div><script>const tl=gsap.timeline({{paused:true}});{"".join(cues)}window.__timelines=window.__timelines||{{}};window.__timelines.captions=tl;</script></template>'


def build(folder,plan,final_media=None):
    for name in ['raw','assets','working','hyperframes']:
        root=folder/name
        if root.is_symlink() or any(p.is_symlink() for p in root.rglob('*')):raise ValueError('Project media and working folders cannot contain symlinks.')
    for shot in plan['shots']:
        source=(folder/'raw'/shot['source']).resolve()
        if not re.fullmatch(r'[A-Za-z0-9_-]+',shot['id']) or not source.is_relative_to((folder/'raw').resolve()):raise ValueError('Invalid source path or scene ID.')
        if digest(source)!=shot['source_sha256']:raise ValueError('Source changed. Re-import and review it.')
    output=get_profile(plan);placed=timeline(plan);hf=folder/'hyperframes';hf.mkdir(exist_ok=True)
    manifest_file=folder/'working/hyperframes-managed.json';manifest=read_json(manifest_file) if manifest_file.exists() else {}
    for file in ['Inter.ttf']: copy_changed(effects_root()/'fonts'/file,hf/'assets/fonts'/file)
    vendor=STUDIO/'tools/hyperframes/node_modules/hyperframes/dist/vendor/npm/gsap@3.15.0/dist/gsap.min.js'
    if not vendor.exists(): raise ValueError('Install the bundled Hyperframes dependencies before previewing.')
    copy_changed(vendor,hf/'assets/vendor/gsap.min.js')
    refs=[];prepared=[];w,h=output['width'],output['height'];duration=sum(r['frames'] for r in placed)/float(rate(output['fps']))
    for shot,row in zip(plan['shots'],placed):
        ident=shot['id'];source=normalize(folder,shot,output);prepared.append(source)
        copy_changed((final_media or {}).get(ident,source),hf/f'assets/media/{ident}.mp4')
        extra=shot.get('hyperframes',{})
        headline=extra.get('headline','')
        # Initial scaffolds are deliberately small. Studio/agent-authored code stays editable.
        graphic=f'<div class="headline">{html.escape(str(headline))}</div>' if headline else ''
        text=f'<template><style>#root{{position:absolute;inset:0;width:{w}px;height:{h}px;overflow:hidden;background:#111}}.visual{{position:absolute;inset:0}}video,img{{position:absolute;inset:0;width:{w}px;height:{h}px;object-fit:cover}}.headline{{position:absolute;top:10%;left:8%;width:84%;color:white;font:800 {88*min(w,h)/1080}px/1.1 sans-serif;text-align:center}}</style><div id="root" data-composition-id="shot-{ident}" data-width="{w}" data-height="{h}"><div id="visual-{ident}" class="visual"><video id="media-{ident}" class="clip" data-start="0" data-duration="{row["duration"]:.12f}" data-track-index="0" src="assets/media/{ident}.mp4" muted playsinline></video>{graphic}</div></div><script>const tl=gsap.timeline({{paused:true}});window.__timelines=window.__timelines||{{}};window.__timelines["shot-{ident}"]=tl;</script></template>'
        managed_write(hf,hf/f'compositions/shot-{ident}.html',text,manifest)
        refs.append(f'<div id="shot-{ident}" class="clip" data-composition-id="shot-{ident}" data-composition-src="compositions/shot-{ident}.html" data-start="{row["start"]:.12f}" data-duration="{row["duration"]:.12f}" data-track-index="1" data-width="{w}" data-height="{h}" style="position:absolute;inset:0"></div>')
    managed_write(hf,hf/'compositions/captions.html',caption_source(plan,placed,output),manifest)
    refs.append(f'<div id="captions" class="clip" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{duration:.12f}" data-track-index="30" data-width="{w}" data-height="{h}" style="position:absolute;inset:0;z-index:30"></div>')
    source=f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(plan["title"])}</title><script src="assets/vendor/gsap.min.js"></script><style>*{{box-sizing:border-box}}html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden;background:#111}}#root{{position:relative;width:{w}px;height:{h}px}}</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="{duration:.12f}" data-fps="{float(rate(output["fps"])):.12f}" data-width="{w}" data-height="{h}">{"".join(refs)}<!-- STUDIO AUDIO START --><!-- STUDIO AUDIO END --></div><script>const tl=gsap.timeline({{paused:true}});window.__timelines=window.__timelines||{{}};window.__timelines.main=tl;</script></body></html>'
    managed_write(hf,hf/'index.html',source,manifest)
    audio=prepare_audio(folder,plan,output,placed)
    mix = audio['sample']
    audio_files = [mix]
    copy_changed(mix,hf/'assets/audio'/mix.name)
    audio_nodes = [f'<audio id="approved-mix" class="clip" src="assets/audio/{mix.name}" data-start="0" data-duration="{duration:.12f}" data-volume="1" data-track-index="40"></audio>']
    index=hf/'index.html';text=index.read_text()
    block='<!-- STUDIO AUDIO START -->'+''.join(audio_nodes)+'<!-- STUDIO AUDIO END -->'
    if not re.search(r'<!-- STUDIO AUDIO START -->.*?<!-- STUDIO AUDIO END -->',text,re.S): raise ValueError('The authored index no longer has its managed audio section. Restore it before building.')
    updated=re.sub(r'<!-- STUDIO AUDIO START -->.*?<!-- STUDIO AUDIO END -->',lambda _:block,text,flags=re.S)
    old=digest(index)
    if updated!=text: index.write_text(updated)
    if manifest.get('index.html')==old: manifest['index.html']=digest(index)
    write_json(manifest_file,manifest)
    return {'project':hf,'timeline':placed,'prepared':prepared,'audio':audio,'audio_files':audio_files,'frames':sum(r['frames'] for r in placed)}


def clip_effects(folder,shot,output,final=False,times=None):
    effects=api().effects_for(folder,shot);source=normalize(folder,shot,output)
    engine=[(str(p.relative_to(effects_root())),digest(p)) for name in ['scripts','fonts','models'] for p in sorted((effects_root()/name).rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    key=digest_key([folder.parent.name,digest(source),effects,output,engine])
    target=folder/'working/vibha'/key;target.mkdir(parents=True,exist_ok=True)
    if final:
        file=target/'effected.mp4'
        if not file.exists():
            if effects:
                config=target/'effects.json';write_json(config,{'effects':effects})
                run([runtime(),effects_root()/'scripts/fx.py','--plan',config,source,file,'--width',str(min(output['width'],output['height']))],target/'render.log')
            else: shutil.copyfile(source,file)
            validate_export(probe(file),output,frames_for(shot['clip'][1]-shot['clip'][0],output))
        return file
    times=times or [0];results=[]
    missing=[t for t in times if not (target/f'at-{t:.6f}.png').exists()]
    if missing and effects:
        config=target/'effects.json';write_json(config,{'effects':effects})
        run([runtime(),effects_root()/'scripts/fx.py','--plan',config,source,target/'frame.png','--still',','.join(str(t) for t in missing),'--warmup','--width',str(min(output['width'],output['height']))],target/'preview.log')
        for t in missing:
            found=target/'frame.png' if len(missing)==1 else target/f'frame_{t:.2f}.png'
            shutil.copyfile(found,target/f'at-{t:.6f}.png')
    elif missing:
        for t in missing: run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',source,'-frames:v','1',target/f'at-{t:.6f}.png'])
    for t in times: results.append(target/f'at-{t:.6f}.png')
    return results


def preview(slug):
    rw=api();folder,plan=rw.plan_at(slug);rw.validate(folder,plan);get_profile(plan)
    built=build(folder,plan);before=input_hash(folder);output=get_profile(plan);fps=float(rate(output['fps']))
    dest=folder/'previews'/uuid.uuid4().hex[:12];dest.mkdir(parents=True)
    scratch=folder/'working'/f'hf-preview-{dest.name}'
    shutil.copytree(built['project'],scratch,ignore=shutil.ignore_patterns('.hyperframes','renders','node_modules'),copy_function=shutil.copyfile)
    details=[];global_times=[]
    for shot,row in zip(plan['shots'],built['timeline']):
        sample_frames={min(row['frames']-1,round(.2*fps)),row['frames']//2,max(0,row['frames']-2)}
        for effect in rw.effects_for(folder,shot):
            sample_frames.update(min(row['frames']-1,max(0,round((effect['start']+(effect['end']-effect['start'])*f)*fps))) for f in [.2,.6,.9])
        times=[n/fps for n in sorted(sample_frames)];images=clip_effects(folder,shot,output,times=times)
        children=[];cuts=[0]+[(a+b)/2 for a,b in zip(times,times[1:])]+[row['duration']]
        for i,(t,image) in enumerate(zip(times,images)):
            rel=f'assets/previews/{shot["id"]}-{i}.png';copy_changed(image,scratch/rel)
            children.append(f'<img class="clip" data-start="{cuts[i]:.12f}" data-duration="{cuts[i+1]-cuts[i]:.12f}" data-track-index="0" src="{rel}">')
            when=row['start']+t;global_times.append(when)
            details.append({'id':f'{shot["id"]}@{t:.6f}','scene':shot['id'],'time':when,'local_time':t})
        path=scratch/f'compositions/shot-{shot["id"]}.html';source=path.read_text()
        pattern=r'<video\b([^>]*\bsrc=["\']assets/media/'+re.escape(shot['id'])+r'\.mp4["\'][^>]*)>\s*</video>'
        replacement='<div id="media-'+shot['id']+'" style="position:absolute;inset:0">'+''.join(children)+'</div>'
        source,count=re.subn(pattern,lambda _:replacement,source)
        if not count: raise ValueError(f'Cannot map authored scene {shot["id"]} to its preview source. Preserve the managed video source path.')
        path.write_text(source)
    captures=dest/'frames'
    wrapper=STUDIO/'tools/hyperframes/hyperframes.mjs'
    run(['node',wrapper,'snapshot',scratch,'--at',','.join(f'{t:.12f}' for t in global_times),'--no-end','--keep','--output',captures,'--json'],dest/'snapshot.log')
    available={float(re.search(r'at-([0-9.]+)s',p.name).group(1)):p for p in captures.glob('at-*s.png')}
    images={};files=[]
    for item in details:
        when=min(available,key=lambda t:abs(t-item['time']))
        if abs(when-item['time'])>.001: raise ValueError('Hyperframes did not capture the requested actual frame.')
        file=available[when];item['file']=str(file);files.append(str(file));images.setdefault(item['scene'],[]).append(file)
    if input_hash(folder)!=before: raise ValueError('Inputs changed during preview. Generate fresh frames.')
    review=rw.make_html(folder,plan,dest/'review.html',images)
    record={'pipeline_version':2,'inputs':before,'visual_inputs':input_hash(folder,True),'files':files+[str(review)],
            'review_plan_sha256':digest(folder/'plan.json'),'mix_version':2,'scene_audio_times':{row['id']:[row['start'],row['start']+row['duration']] for row in built['timeline']},
            'frame_details':details,'media_files':[str(p) for p in built['prepared']],
            'audio_files':[str(p) for p in built['audio_files']],'mix_sample':str(built['audio']['sample']),
            'review':str(review),'output_profile':output}
    record['id']=rw.preview_digest(record);write_json(folder/'preview.json',record);rw.make_html(folder,plan,images=images)
    return {'project':slug,'stage':'review_actual_frames_and_audio','preview_id':record['id'],'frames':len(details),'review':str(review),'output_profile':output}


def choose_music(slug,track):
    rw=api();folder,plan=rw.plan_at(slug)
    if plan.get('pipeline_version')!=2: raise ValueError('Audio selection is available for the version 2 reel pipeline.')
    if track is not None:
        from audio_library import require_verified
        require_verified(track);audio_file(track,'music')
    old=read_json(folder/'preview.json') if (folder/'preview.json').exists() else None
    current=bool(old and old['inputs']==input_hash(folder) and rw.preview_digest(old)==old['id'])
    visual_before=input_hash(folder,True)
    if plan.get('audio',{}).get('music') != track:
        rw.invalidate_approval(folder)
    plan.setdefault('audio',{})['music']=track;write_json(folder/'plan.json',plan)
    sample=None
    refreshed=False
    if plan.get('output_profile') and all(s.get('source') and s.get('text_confirmed') for s in plan['shots']):
        built=build(folder,plan);sample=str(built['audio']['sample'])
        if current and visual_before==input_hash(folder,True):
            old.update(inputs=input_hash(folder),review_plan_sha256=digest(folder/'plan.json'),audio_files=[str(p) for p in built['audio_files']],mix_sample=sample)
            old['id']=rw.preview_digest(old);write_json(folder/'preview.json',old)
            refreshed=True
    rw.make_html(folder,plan)
    return {'project':slug,'music':track,'mix_sample':sample,'preview_id':old['id'] if refreshed else None}


def render(slug):
    rw=api();folder,plan=rw.plan_at(slug);rw.validate(folder,plan);record=rw.approval_check(folder)
    output=get_profile(plan);media={}
    for shot in plan['shots']:
        media[shot['id']]=clip_effects(folder,shot,output,final=True);rw.approval_check(folder)
    built=build(folder,plan,media);rw.approval_check(folder)
    pending=folder/'working/hyperframes.pending.mp4'
    run(['node',STUDIO/'tools/hyperframes/hyperframes.mjs','render',built['project'],'--quality','delivery','--fps',output['fps'],'--workers','1','--experimental-fast-capture=false','--output',pending],folder/'working/hyperframes-render.log')
    rw.approval_check(folder);validate_export(probe(pending),output,built['frames'])
    final=folder/'export'/f'{slug}-{record["id"][:12]}.mp4';final.parent.mkdir(exist_ok=True)
    # Encode the WAV the creator heard. Hyperframes contributes only the approved picture.
    mix = Path(record['mix_sample'])
    if built['audio']['sample'] != mix:
        raise ValueError('The reviewed mix changed. Generate fresh previews.')
    staged = folder/'working/approved-mix.pending.mp4'
    run(['ffmpeg','-y','-v','error','-i',pending,'-i',mix,'-map','0:v:0','-map','1:a:0','-c:v','copy',
         '-c:a','aac','-b:a','192k','-movflags','+faststart',staged])
    info=probe(staged);validate_export(info,output,built['frames'])
    run(['ffmpeg','-v','error','-i',staged,'-f','null','-'],folder/'working/decode.log')
    rw.approval_check(folder)
    staged.replace(final)
    cover=final.parent/'cover.png';run(['ffmpeg','-y','-v','error','-i',final,'-frames:v','1',cover])
    caption=final.parent/'caption.txt'
    # Platform copy is authored by the agent before the export; never invent a ready-to-post caption.
    write_json(folder/'export.json',{'project_type':plan.get('project_type','reel'),'file':str(final),'renderer':'hyperframes','project':str(built['project']),
               'preview_id':record['id'],'approved_mix_sha256':digest(mix),'output_profile':output,'width':info['width'],'height':info['height'],
               'fps':info['fps'],'frames':info['frame_count'],'duration':info['duration'],'cover':{'png':'export/cover.png'},
               'caption_ready':caption.is_file(),'decode_check':'passed'})
    return {'project':slug,'stage':'exported' if caption.is_file() else 'video_ready_posting_copy_pending','file':str(final),'output_profile':output}
