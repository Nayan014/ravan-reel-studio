#!/usr/bin/env python3
"""Find when each word is said, so effects can land on the right word.

usage: python words.py input.mp4            -> prints "12.34  word" lines and saves input.words.json
Uses faster-whisper (installed into the skill's .venv on first run). On a Mac with mlx-whisper installed, that is used instead.
"""
import argparse, json, os, subprocess, sys

os.environ.setdefault('HF_HOME', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                          '.cache', 'huggingface'))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source')
parser.add_argument('--language', default=os.environ.get('WHISPER_LANGUAGE'),
                    help='Known speech language, e.g. en; omit for automatic detection')
args = parser.parse_args()
src = args.source
out = os.path.splitext(src)[0] + '.words.json'
words = []
try:
    import mlx_whisper
    r = mlx_whisper.transcribe(src, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', word_timestamps=True, language=args.language)
    words = [{'w': w['word'].strip(), 's': round(w['start'], 2), 'e': round(w['end'], 2)} for seg in r['segments'] for w in seg.get('words', [])]
except ImportError:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print('Installing the transcriber (one time, about 1 minute)...', flush=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'faster-whisper'], check=True)
        from faster_whisper import WhisperModel
    model = WhisperModel(os.environ.get('WHISPER_MODEL', 'base'), device='cpu', compute_type='int8')
    # Decode through the already-required ffmpeg. Passing PCM avoids PyAV
    # open() API differences across faster-whisper/PyAV package versions.
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vn', '-ac', '1', '-ar', '16000',
                          '-f', 'f32le', '-'], stdout=subprocess.PIPE, check=True).stdout
    audio = np.frombuffer(pcm, dtype='<f4').astype(np.float32, copy=True)
    segs, _ = model.transcribe(audio, word_timestamps=True, vad_filter=True, language=args.language)
    words = [{'w': w.word.strip(), 's': round(w.start, 2), 'e': round(w.end, 2)} for s in segs for w in (s.words or [])]

json.dump(words, open(out, 'w'), indent=0)
for w in words: print(f"{w['s']:7.2f}  {w['w']}")
print(f'\nSaved {len(words)} words to {out}')
