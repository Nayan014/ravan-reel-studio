#!/usr/bin/env python3
"""Second-opinion transcription with context across short takes. Does not edit the plan."""
import argparse
import json
import os
from pathlib import Path
import wave
from reel_workflow import STUDIO, plan_at

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project',required=True)
args=p.parse_args()
folder,plan=plan_at(args.project)
os.environ.setdefault('HF_HOME',str(STUDIO/'skills/effects/.cache/huggingface'))
import numpy as np
from faster_whisper import WhisperModel
chunks=[]; boundaries=[]; offset=0
# A split scene can reference the same source more than once: transcribe each original take once.
seen=set()
for shot in plan['shots']:
    if shot['source'] in seen: continue
    seen.add(shot['source'])
    wav=folder/'working/analysis'/f'{shot["id"]}.wav'
    with wave.open(str(wav),'rb') as w:
        if w.getframerate()!=16000 or w.getnchannels()!=1 or w.getsampwidth()!=2:
            raise ValueError('Run analyze first to prepare mono 16 kHz speech audio.')
        pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768
    chunks.append(pcm)
    boundaries.append({'take':shot['id'],'source':shot['source'],'start':offset,'end':offset+len(pcm)/16000})
    offset+=len(pcm)/16000
language=plan.get('language','en')
model=WhisperModel(plan.get('speech_model','small.en' if language=='en' else 'small'),device='cpu',compute_type='int8')
vocabulary=plan.get('vocabulary',[plan.get('channel',''),plan['title']])
segments,_=model.transcribe(np.concatenate(chunks),language=language,word_timestamps=True,vad_filter=True,
                           initial_prompt='. '.join(vocabulary),beam_size=5)
words=[{'w':w.word.strip(),'s':w.start,'e':w.end} for seg in segments for w in (seg.words or [])]
result=[]
for boundary in boundaries:
    selected=[{'w':w['w'],'s':round(max(0,w['s']-boundary['start']),3),
               'e':round(min(boundary['end'],w['e'])-boundary['start'],3)}
              for w in words if boundary['start']<=(w['s']+w['e'])/2<boundary['end']]
    result.append({**boundary,'words':selected,'text':' '.join(w['w'] for w in selected)})
output=folder/'working/analysis/context-transcript.json'
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'transcript':str(output),'takes':result,'note':'Candidate transcription only. Compare with each take; preserve uncertain wording for user confirmation.'},indent=2))
