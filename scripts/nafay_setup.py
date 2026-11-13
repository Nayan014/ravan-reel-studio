#!/usr/bin/env python3
"""Prepare Nafay's optional renderer in the existing studio virtual environment."""
import argparse
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT/'skills/effects/.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
BROWSERS = ROOT/'tools/nafay-video-editor/.cache/browsers'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path in [ROOT/'skills/effects/.venv',ROOT/'skills/effects/.cache',ROOT/'tools/nafay-video-editor/.cache']:
        if path.is_symlink():
            raise ValueError('Runtime folders cannot use symlinks.')
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(BROWSERS),
               PIP_CACHE_DIR=str(ROOT/'skills/effects/.cache/pip'))
    env.setdefault('HF_HOME',str(ROOT/'skills/effects/.cache/huggingface'))
    if args.check:
        modules = False
        if PYTHON.is_file():
            modules = subprocess.run([str(PYTHON),'-c', 'import playwright, faster_whisper, numpy, PIL'],
                                     env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
        print(json.dumps({'python':str(PYTHON),'modules_installed':modules,
                          'browser_cache_present':BROWSERS.is_dir(),
                          'note':'Presence check only; no browser or renderer was launched.'}))
        return
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise ValueError('Run npm start first to prepare the base studio tools, then select Nafay again.')
    if not PYTHON.is_file():
        if not (3,10)<=sys.version_info[:2]<(3,14):
            raise ValueError('Use Python 3.10–3.13 to prepare the studio environment, or run npm start first.')
        subprocess.run([sys.executable,'-m','venv',str(PYTHON.parents[1])],check=True,env=env)
    subprocess.run([str(PYTHON),'-m','pip','install','-r',str(ROOT/'skills/effects/requirements-nafay.txt')],check=True,env=env)
    subprocess.run([str(PYTHON),'-m','playwright','install','chromium'],check=True,env=env)
    print(json.dumps({'status':'installed','python':str(PYTHON),'browser_cache':str(BROWSERS)}))


if __name__=='__main__':
    try:
        main()
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        print(json.dumps({'error':str(error)}),file=sys.stderr)
        sys.exit(1)
