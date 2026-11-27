#!/usr/bin/env python3
"""Connect this project to the shared AI Brain (skills, workflows, rules). Stdlib only, never blocks the host.

  python3 scripts/ai_brain.py            # find/clone brain, pull if due, mount skills
  python3 scripts/ai_brain.py --no-pull  # skip the git pull
  python3 scripts/ai_brain.py --pull     # pull now, ignoring the hourly throttle

Brain location, first match wins: $AI_BRAIN_HOME, ../ai-brain (side-by-side dev layout), ./.ai-brain (auto-cloned).
Config lives in .ai-brain.json: {"repo": "<git url>", "project": "<name>", "ref": "main", "pull_interval_minutes": 60}.
Env overrides: AI_BRAIN_REF (branch to use, handy for testing a brain branch), AI_BRAIN_OFFLINE=1 (never touch the network).
This file is generated from ai-brain/templates/ai_brain.py; edit it there.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".ai-brain.json"
STAMP = ROOT / ".ai-brain-last-pull"
DEFAULTS = {"repo": "https://github.com/Nayan014/ai-brain.git", "project": ROOT.name, "ref": "main", "pull_interval_minutes": 60}
QUIET = "--quiet" in sys.argv or "-q" in sys.argv


def say(msg):
    if not QUIET:
        print(f"[ai-brain] {msg}")


def warn(msg):
    print(f"[ai-brain] WARN {msg}", file=sys.stderr)


def git(args, cwd, timeout=30):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    return r.returncode, (r.stdout + r.stderr).strip()


def load_config():
    cfg = dict(DEFAULTS)
    if CONFIG.is_file():
        try:
            cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
        except ValueError:
            warn(f"{CONFIG.name} is not valid JSON; using defaults")
    if os.environ.get("AI_BRAIN_REF"):
        cfg["ref"] = os.environ["AI_BRAIN_REF"]
    return cfg


def find_brain():
    for cand in (os.environ.get("AI_BRAIN_HOME"), ROOT.parent / "ai-brain", ROOT / ".ai-brain"):
        if cand and (Path(cand) / "scripts" / "sync.py").is_file():
            return Path(cand).resolve()
    return None


def clone(cfg):
    dest = ROOT / ".ai-brain"
    say(f"cloning {cfg['repo']} ({cfg['ref']}) into .ai-brain/")
    code, out = git(["clone", "--quiet", "--branch", cfg["ref"], cfg["repo"], str(dest)], ROOT, timeout=180)
    if code != 0:
        warn(f"clone failed, skills not mounted: {out.splitlines()[-1] if out else code}")
        return None
    STAMP.write_text(str(time.time()))
    return dest


def pull_due(cfg, force):
    if force:
        return True
    try:
        return time.time() - float(STAMP.read_text()) > float(cfg["pull_interval_minutes"]) * 60
    except (OSError, ValueError):
        return True


def pull(brain, cfg):
    """Fast-forward only, and only when it cannot disturb anyone's work in the brain checkout."""
    code, branch = git(["branch", "--show-current"], brain)
    if code != 0:
        return
    explicit_ref = bool(os.environ.get("AI_BRAIN_REF"))
    if branch != cfg["ref"] and not explicit_ref:
        say(f"brain is on '{branch}', not '{cfg['ref']}'; not pulling")
        return
    if git(["status", "--porcelain", "--untracked-files=no"], brain)[1]:
        say("brain has local edits; not pulling")
        return
    code, out = git(["fetch", "--quiet", "origin", cfg["ref"]], brain, timeout=30)
    if code != 0:
        say("offline or fetch failed; using the local brain")
        return
    if branch != cfg["ref"]:
        code, out = git(["checkout", "--quiet", "-B", cfg["ref"], "FETCH_HEAD"], brain)
    else:
        code, out = git(["merge", "--ff-only", "--quiet", "FETCH_HEAD"], brain)
    if code != 0:
        warn(f"could not fast-forward the brain: {out.splitlines()[-1] if out else code}")
        return
    STAMP.write_text(str(time.time()))


def main():
    cfg = load_config()
    brain = find_brain()
    offline = os.environ.get("AI_BRAIN_OFFLINE") == "1" or "--no-pull" in sys.argv
    if brain is None:
        if offline:
            warn("no brain found and offline mode is on")
            return 0
        brain = clone(cfg)
        if brain is None:
            return 0
    elif not offline and pull_due(cfg, "--pull" in sys.argv):
        try:
            pull(brain, cfg)
        except (OSError, subprocess.TimeoutExpired) as e:
            say(f"pull skipped: {e}")
    cmd = [sys.executable, str(brain / "scripts" / "sync.py"), "--target", str(ROOT), "--project", cfg["project"], "--quiet"]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        warn(f"sync failed: {(r.stderr or r.stdout).strip().splitlines()[-1:]}")
        return 0
    report = ROOT / ".ai-brain-sync.json"
    try:
        info = json.loads(report.read_text(encoding="utf-8"))
        say(f"{len(info['skills'])} skills mounted from {brain} @ {info['brain_commit']}")
        for w in info.get("warnings", []):
            warn(w)
    except (OSError, ValueError):
        pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never break the host app because the brain is unavailable
        warn(f"unexpected error: {e}")
        sys.exit(0)
