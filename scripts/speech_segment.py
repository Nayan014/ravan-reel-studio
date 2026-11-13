"""Optional uncertain-segment pass. Saves candidates without changing approved speech."""
import argparse
from pathlib import Path
from video_workflow import read_json,write_json,run,runtime,digest
from reel_workflow import plan_at

def segment(slug,scene,start,end):
    folder,plan=plan_at(slug);shot=next((s for s in plan['shots'] if s['id']==scene),None)
    if not shot or not 0<=start<end:raise ValueError('Choose an uncertain source-time interval and valid scene.')
    # Only a flagged low-confidence span may trigger another model pass.
    cache=read_json(folder/'working/analysis'/f'{shot["source_sha256"]}.speech.json')
    if not any(w.get('probability') is not None and w['probability']<.5 and w['s']<end and w['e']>start for w in cache['words']):
        raise ValueError('This interval has no flagged uncertain speech. Listen and confirm rather than retranscribing the whole take.')
    from audio_library import digest_key
    dest=folder/'working/analysis'/digest_key([scene,start,end,'second-pass']);dest.mkdir(exist_ok=True)
    wav=dest/'segment.wav'
    if not wav.exists():run(['ffmpeg','-y','-v','error','-ss',str(start),'-t',str(end-start),'-i',folder/'raw'/shot['source'],'-vn','-ac','1','-ar','16000',wav])
    manifest=dest/'batch.json';output=dest/'candidate.json'
    write_json(manifest,{'language':plan.get('language','en'),'jobs':[{'wav':str(wav),'cache':str(output),'source':f'{scene}:{start}-{end}','source_sha256':digest(wav)}]})
    run([runtime(),Path(__file__).with_name('speech_batch.py'),manifest],dest/'batch.log')
    return {'candidate':str(output),'source_offset':start,'next':'Listen and compare candidate timings offset by source_offset. This does not modify the plan.'}

if __name__=='__main__':
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--scene',required=True);p.add_argument('--start',type=float,required=True);p.add_argument('--end',type=float,required=True)
    a=p.parse_args();print(json.dumps(segment(a.project,a.scene,a.start,a.end)))
