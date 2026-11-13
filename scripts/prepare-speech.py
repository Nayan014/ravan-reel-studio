"""Cache and check the default English CPU model; never reads user recordings."""
import os
from pathlib import Path

root=Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HOME',str(root/'skills/effects/.cache/huggingface'))
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')

if __name__=='__main__':
    from faster_whisper import WhisperModel
    from faster_whisper.utils import download_model
    try:path=download_model('small.en',local_files_only=True)
    except Exception:path=download_model('small.en')
    model=WhisperModel(path,device='cpu',compute_type='int8')
    print('Default English speech model ready (CPU, cached).')
