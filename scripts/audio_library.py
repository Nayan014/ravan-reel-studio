"""Local credited audio catalogue and reproducible voice/music/SFX review mixes."""
import hashlib
import json
from pathlib import Path
from video_workflow import STUDIO, digest, run, read_json
from media_profile import frames_for, rate


def catalogue():
    return {e['id']:e for e in read_json(STUDIO/'assets/audio/catalogue.json')['entries']}


def audio_file(ident,kind=None):
    item=catalogue().get(ident)
    if not item or (kind and item['kind']!=kind): raise ValueError('Choose an audio ID from the local catalogue.')
    base=(STUDIO/'tools/techno-reel/public').resolve();path=(STUDIO/item['file']).resolve()
    if not path.is_relative_to(base) or not path.is_file(): raise ValueError('Library audio file is missing.')
    return path


def defaults():
    return {'recommended_music':'music-lofi','music':'music-lofi','music_gain':.10,'sfx':[]}


def validate_audio(plan):
    audio={**defaults(),**plan.get('audio',{})}
    if audio['music'] is not None: audio_file(audio['music'],'music')
    if not isinstance(audio['music_gain'],(float,int)) or not 0<=audio['music_gain']<=.3: raise ValueError('Music gain must be between zero and 0.3.')
    shots={s['id']:s for s in plan['shots']}
    if not isinstance(audio['sfx'],list) or len(audio['sfx'])>100: raise ValueError('Invalid sound cue list.')
    for cue in audio['sfx']:
        audio_file(cue.get('sound'),'sfx')
        shot=shots.get(cue.get('scene'))
        if shot is None: raise ValueError('Sound cue scene is missing.')
        duration=shot['clip'][1]-shot['clip'][0]
        if not isinstance(cue.get('at'),(int,float)) or not 0<=cue['at']<duration: raise ValueError('Sound cues must be inside their scene.')
        if not isinstance(cue.get('gain',.1),(int,float)) or not 0<=cue.get('gain',.1)<=.5: raise ValueError('Sound cue gain is invalid.')
    return audio


def prepare_audio(folder,plan,output,timeline):
    audio=validate_audio(plan);target=folder/'working/audio';target.mkdir(parents=True,exist_ok=True)
    total=sum(s['frames'] for s in timeline)/float(rate(output['fps']))
    voice_key=digest_key([[s['source_sha256'],s['clip']] for s in plan['shots']]+[output['fps'],'voice-v1'])
    voice=target/f'voice-{voice_key}.wav'
    if not voice.exists():
        command=['ffmpeg','-y','-v','error'];filters=[]
        for i,(shot,placed) in enumerate(zip(plan['shots'],timeline)):
            duration=placed['frames']/float(rate(output['fps']))
            command+=['-ss',str(shot['clip'][0]),'-t',str(duration),'-i',folder/'raw'/shot['source']]
            filters.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,apad,atrim=duration={duration}[a{i}]')
        labels=''.join(f'[a{i}]' for i in range(len(timeline)))
        filters.append(f'{labels}concat=n={len(timeline)}:v=0:a=1,loudnorm=I=-16:TP=-2:LRA=11,aresample=48000[voice]')
        run(command+['-filter_complex',';'.join(filters),'-map','[voice]','-t',str(total),'-c:a','pcm_s16le',voice])
    bed=None
    if audio['music']:
        source=audio_file(audio['music'],'music')
        key=digest_key([voice_key,digest(source),audio['music_gain'],'duck-v1'])
        bed=target/f'bed-{key}.wav'
        if not bed.exists():
            run(['ffmpeg','-y','-v','error','-stream_loop','-1','-i',source,'-i',voice,
                 '-filter_complex',f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={audio["music_gain"]},afade=t=in:d=0.25,afade=t=out:st={max(0,total-.5)}:d=0.5[m];[m][1:a]sidechaincompress=threshold=0.02:ratio=6:attack=10:release=250[bed]',
                 '-map','[bed]','-t',str(total),'-c:a','pcm_s16le',bed])
    offsets={s['id']:s['start'] for s in timeline}
    cues=[{**cue,'file':audio_file(cue['sound'],'sfx'),'start':offsets[cue['scene']]+cue['at'],'duration':min(catalogue()[cue['sound']]['duration'],total-offsets[cue['scene']]-cue['at'])} for cue in audio['sfx']]
    key=digest_key([voice_key,str(bed),audio['sfx'],[[c['sound'],digest(c['file'])] for c in cues]])
    sample=target/f'mix-{key}.wav'
    if not sample.exists():
        command=['ffmpeg','-y','-v','error','-i',voice];filters=[];mix=['[0:a]'];index=1
        if bed: command+=['-i',bed];mix.append(f'[{index}:a]');index+=1
        for cue in cues:
            command+=['-i',cue['file']];delay=round(cue['start']*1000)
            filters.append(f'[{index}:a]atrim=duration={cue["duration"]},volume={cue.get("gain",.1)},adelay={delay}|{delay}[s{index}]');mix.append(f'[s{index}]');index+=1
        filters.append(''.join(mix)+f'amix=inputs={len(mix)}:normalize=0,alimiter=limit=0.95:level=false[out]')
        run(command+['-filter_complex',';'.join(filters),'-map','[out]','-t',str(min(8,total)),'-c:a','pcm_s16le',sample])
    return {'voice':voice,'bed':bed,'cues':cues,'sample':sample,'duration':total,'signature':key}


def digest_key(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()[:24]
