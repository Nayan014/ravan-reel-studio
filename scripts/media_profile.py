"""Source-derived portrait output profiles shared by preparation and finishing."""
from fractions import Fraction
import math


def rate(value):
    try:
        result=Fraction(str(value))
    except (ValueError,ZeroDivisionError,TypeError):
        raise ValueError('A valid frame rate is required.')
    if result<=0: raise ValueError('Frame rate must be positive.')
    return result


def profile(width,height,fps):
    fps=rate(fps)
    if isinstance(width,bool) or isinstance(height,bool) or not isinstance(width,int) or not isinstance(height,int):
        raise ValueError('Output dimensions must be whole pixels.')
    if width<144 or width>2160 or height>3840 or width%2 or height%2 or abs(height-width*16/9)>2:
        raise ValueError('Choose an even-sized portrait 9:16 profile, up to 2160×3840.')
    if not 1<=fps<=60: raise ValueError('This pipeline supports 1–60 FPS; choose an explicit supported output profile.')
    return {'width':width,'height':height,'fps':str(fps),'fps_value':float(fps)}


def from_source(info):
    width=min(info['width'],info['height'])
    return profile(width,round(width*16/9/2)*2,info.get('fps_fraction',info['fps']))


def detect(infos):
    choices=[];flags=[]
    for info in infos:
        try:
            item=from_source(info)
            if item not in choices: choices.append(item)
        except ValueError as error: flags.append(str(error))
        if info.get('variable_frame_rate'): flags.append('Variable frame rate detected; choose the output rate explicitly.')
    return {'output':choices[0] if len(choices)==1 and not flags else None,
            'choices':choices,'requires_choice':len(choices)!=1 or bool(flags),
            'reasons':list(dict.fromkeys(flags or (['Source resolutions or frame rates differ.'] if len(choices)>1 else [])))}


def get_profile(plan):
    value=plan.get('output_profile')
    if not value: raise ValueError('Output quality is pending. Inspect quality and choose a profile before previewing.')
    return profile(value['width'],value['height'],value['fps'])


def frames_for(seconds,output):
    if not math.isfinite(seconds) or seconds<=0: raise ValueError('A positive clip duration is required.')
    return max(1,round(Fraction(str(seconds))*rate(output['fps'])))


def validate_export(info,output,frames):
    expected=frames/float(rate(output['fps']))
    if (info['width'],info['height'])!=(output['width'],output['height']): raise ValueError('Encoded output dimensions do not match the approved profile.')
    if abs(float(rate(info.get('fps_fraction',info['fps'])))-float(rate(output['fps'])))>0.0001:
        raise ValueError('Encoded output frame rate does not match the approved profile.')
    if info.get('frame_count') is not None and info['frame_count']!=frames: raise ValueError(f'Encoded frame count {info["frame_count"]} does not match the approved timeline ({frames}).')
    if abs(info['duration']-expected)>max(.08,2/float(rate(output['fps']))): raise ValueError('Encoded output duration does not match the approved timeline.')
    if not info['has_audio']: raise ValueError('Encoded output has no source audio.')
    if info.get('audio_duration') and abs(info['audio_duration']-expected)>max(.08,2/float(rate(output['fps']))):
        raise ValueError('Encoded audio duration is out of sync with the approved timeline.')


def inspect_source(path):
    """Packet timing inspects VFR without decoding frames or sending media to a model."""
    from video_workflow import probe,run
    import json
    info=probe(path)
    data=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_packets','-show_entries','packet=pts_time','-of','json',path]))
    stamps=sorted(float(p['pts_time']) for p in data.get('packets',[]) if 'pts_time' in p)
    target=1/float(rate(info['fps_fraction']))
    intervals=[b-a for a,b in zip(stamps,stamps[1:])]
    info['variable_frame_rate']=info['variable_frame_rate'] or any(abs(n-target)>max(.0001,target*.01) for n in intervals)
    return info
