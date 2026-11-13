#!/usr/bin/env bash
# One-time setup for the effects skill. Safe to run again: it prints READY when everything is in place.
set -euo pipefail
cd "$(dirname "$0")/.."
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$PWD/.cache/pip}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
REQUIREMENTS=requirements.txt
CHECK='import mediapipe, cv2, PIL, numpy'
REEL=0
if [ "$#" -gt 1 ]; then echo 'Usage: bash scripts/setup.sh [--reel]'; exit 2; fi
case "${1:-}" in
  '') ;;
  --reel) REQUIREMENTS=requirements-reel.txt; REEL=1 ;;
  *) echo 'Usage: bash scripts/setup.sh [--reel]'; exit 2 ;;
esac

# Rendering and transcription run in separate processes. Check them separately
# too, avoiding conflicting macOS FFmpeg dylibs loaded by OpenCV and PyAV.
check_environment() {
  .venv/bin/python -c "$CHECK" || return 1
  if [ "$REEL" -eq 1 ]; then
    .venv/bin/python -c 'import faster_whisper; from importlib.metadata import version; assert version("faster-whisper") == "1.2.1"'
  fi
}

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "NEED_FFMPEG: install ffmpeg first (Mac: brew install ffmpeg, Windows: winget install ffmpeg)"; exit 1
fi
if [ -x .venv/bin/python ] && check_environment 2>/dev/null; then echo READY; exit 0; fi

# Upgrade a working effects-only environment without replacing it.
if [ -x .venv/bin/python ]; then
  .venv/bin/python -m pip install -q -r "$REQUIREMENTS"
  check_environment
  echo READY
  exit 0
fi

PY=""
for v in python3.12 python3.11 python3.13 python3.10 python3; do
  if command -v "$v" >/dev/null 2>&1 && "$v" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>/dev/null; then PY="$v"; break; fi
done

if [ -n "$PY" ]; then
  "$PY" -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip
  .venv/bin/python -m pip install -q -r "$REQUIREMENTS"
elif command -v uv >/dev/null 2>&1; then
  uv venv -q -p 3.12 .venv
  uv pip install -q -p .venv/bin/python -r "$REQUIREMENTS"
else
  echo "NEED_PYTHON: install Python 3.10 or newer (python.org/downloads), then run this again"; exit 1
fi

check_environment
echo READY
