"""Cached local word timings; one model load for every uncached take in a batch."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path


def transcribe_jobs(jobs,language='en',model=None,worker=None):
    backend='mlx' if importlib.util.find_spec('mlx_whisper') else 'faster-whisper'
    model=model or ('mlx-community/whisper-large-v3-turbo' if backend=='mlx' else 'small.en' if language=='en' else 'small')
    results=[];pending=[]
    for job in jobs:
        signature=hashlib.sha256(json.dumps([job['source_sha256'],backend,model,language,'word-times-v1']).encode()).hexdigest()
        cache=Path(job['cache'])
        old=json.loads(cache.read_text()) if cache.is_file() else {}
        if old.get('signature')==signature:
            results.append({**job,**old,'cached':True})
        else: pending.append((job,signature))
    if pending and worker is None:
        if backend=='mlx':
            import mlx_whisper
            def worker(path):
                data=mlx_whisper.transcribe(str(path),path_or_hf_repo=model,word_timestamps=True,language=language)
                return [{'w':w['word'].strip(),'s':w['start'],'e':w['end'],'probability':w.get('probability')} for seg in data['segments'] for w in seg.get('words',[])]
        else:
            from faster_whisper import WhisperModel
            loaded=WhisperModel(model,device='cpu',compute_type='int8')
            def worker(path):
                import wave,numpy as np
                with wave.open(str(path),'rb') as wav: audio=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768
                segments,_=loaded.transcribe(audio,word_timestamps=True,vad_filter=True,language=language)
                return [{'w':w.word.strip(),'s':w.start,'e':w.end,'probability':w.probability} for s in segments for w in (s.words or [])]
    for job,signature in pending:
        # Backends can return NumPy scalars. Keep the cache and CLI JSON portable.
        words=[{**w,'s':float(w['s']),'e':float(w['e']),
                'probability':None if w.get('probability') is None else float(w['probability'])}
               for w in worker(Path(job['wav']))]
        if not words and not job.get('allow_empty'): raise ValueError(f'No speech found in take {job["source"]}.')
        if any(not w['w'] or w['s']<0 or w['e']<w['s'] for w in words): raise ValueError('Invalid local speech timings; review the source.')
        value={'signature':signature,'backend':backend,'model':model,'language':language,'words':words}
        path=Path(job['cache']);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
        results.append({**job,**value,'cached':False})
    return results


if __name__=='__main__':
    import sys
    from video_workflow import STUDIO
    os.environ.setdefault('HF_HOME',str(STUDIO/'skills/effects/.cache/huggingface'))
    manifest=json.loads(Path(sys.argv[1]).read_text())
    rows=transcribe_jobs(manifest['jobs'],manifest.get('language','en'),manifest.get('model'))
    print(json.dumps({'takes':[{'source':r['source'],'cache':r['cache'],'cached':r['cached'],'words':len(r['words']),
                              'uncertain':sum(1 for w in r['words'] if w.get('probability') is not None and w['probability']<.5)} for r in rows]}))
