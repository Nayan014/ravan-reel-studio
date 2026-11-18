"""Audition and attach scene-local voiceovers to silent footage."""
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from video_workflow import STUDIO, digest, probe, read_json, run, runtime, write_json

WORKER = STUDIO / "skills/natural-narration/scripts/read_line.py"


def source_is_silent(path, clip):
    if not probe(path)["has_audio"]:
        return True
    # Check the selected span, including very quiet speech. Noise needs a listening decision.
    result = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-ss", str(clip[0]), "-t", str(clip[1]-clip[0]),
                             "-i", str(path), "-map", "0:a:0", "-af", "astats=reset=0", "-vn", "-f", "null", "-"], capture_output=True, text=True, check=True)
    peaks = re.findall(r"Peak level dB:\s*(\S+)", result.stderr)
    return bool(peaks) and all(peak == "-inf" for peak in peaks)


def scene_for_voice(folder, plan, scene, confirmed_silent=False):
    if plan.get("pipeline_version") != 2 or plan.get("phase") == "draft":
        raise ValueError("Attach the scene footage to a v2 Reel or YouTube project first.")
    shot = next((s for s in plan["shots"] if s["id"] == scene), None)
    if not shot or not re.fullmatch(r"[A-Za-z0-9_-]+", scene):
        raise ValueError("Choose an existing scene.")
    for directory in ("assets", "assets/narration", "working", "working/narration", "raw"):
        if (folder / directory).is_symlink():
            raise ValueError("Project narration folders cannot use symlinks.")
    raw = (folder / "raw" / shot["source"]).resolve()
    if not raw.is_relative_to((folder / "raw").resolve()) or digest(raw) != shot["source_sha256"]:
        raise ValueError("The scene source changed. Review its footage first.")
    if shot.get("say") and not shot.get("narration"):
        raise ValueError("This scene already has recorded speech.")
    prior = shot.get("audition", {})
    confirmed_silent = confirmed_silent or (prior.get("speech_free_confirmed")
                       and prior.get("clip") == shot["clip"] and prior.get("source_sha256") == shot["source_sha256"])
    if not confirmed_silent and not source_is_silent(raw, shot["clip"]):
        raise ValueError("Listen to the source. Only a confirmed speech-free scene can use narration.")
    return shot


def delivery_for(script, directions, voice="af_heart"):
    if not isinstance(script, str) or not script.strip():
        raise ValueError("Supply the English scene line with --line or expected_say.")
    if not isinstance(directions, dict) or set(directions) - {"A", "B"}:
        raise ValueError("Delivery settings use keys A and B.")
    readings = {}
    for key, pace in [("A", 1.0), ("B", .90)]:
        spec = {"speed": pace, "voice": voice, "phrases": [{"text": script}], **directions.get(key, {})}
        if not isinstance(spec["voice"], str) or not re.fullmatch(r"a[fm]_[a-z]+", spec["voice"]):
            raise ValueError("Choose an installed US English Kokoro preset.")
        phrases = spec["phrases"]
        if " ".join(" ".join(p["text"].split()) for p in phrases) != " ".join(script.split()):
            raise ValueError("Delivery phrases must preserve the approved words. Use pronounce for spoken aliases.")
        for p in phrases:
            speeds = [spec["speed"], p.get("speed", spec["speed"])]
            if any(not isinstance(n, (int,float)) or not .5 <= n <= 1.6 for n in speeds):
                raise ValueError("Use a speech speed between 0.5 and 1.6.")
            if not 0 <= p.get("pause_after", 0) <= 4 or not p["text"].strip():
                raise ValueError("Use a nonempty phrase and a pause of at most four seconds.")
            for word, alias in p.get("pronounce", {}).items():
                if word not in p["text"].split() or not isinstance(alias, str) or not alias.strip():
                    raise ValueError("Pronunciations must map an exact caption word to its spoken form.")
        readings[key] = spec
    if readings["A"] == readings["B"]:
        raise ValueError("Give the two readings different deliveries.")
    return readings


def audition(rw, slug, scene, line=None, delivery_file=None, confirmed_silent=False):
    folder, plan = rw.plan_at(slug)
    initial = digest(folder / "plan.json")
    shot = scene_for_voice(folder, plan, scene, confirmed_silent)
    if str(plan.get("language", "en")).split("-")[0] != "en":
        raise ValueError("These narration presets are for English scripts.")
    script = shot.get("expected_say") or line
    if line and script != line:
        raise ValueError("Use the scene's approved wording or revise the script first.")
    readings = delivery_for(script, read_json(Path(delivery_file)) if delivery_file else {},
                            plan.get("audio", {}).get("narration_voice", "af_heart"))
    # Use the same checkout discovery as the bundled installer, including its optional existing installation.
    located = subprocess.check_output(
        ["node","--input-type=module","-e","import {voiceStudio} from './scripts/lib.mjs'; console.log(voiceStudio.dir())"],
        cwd=STUDIO / "tools/techno-reel", text=True).strip()
    studio = STUDIO / "tools/techno-reel" / located
    python = studio / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        raise ValueError("Install the bundled VoiceStudio Kokoro runtime or set VOICESTUDIO_DIR to its checkout.")
    target = folder / "working/narration"
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target) as work:
        staging = Path(work)
        write_json(staging / "delivery.json", readings)
        run([python, WORKER, staging])
        timings = read_json(staging / "timings.json")
        ident = uuid.uuid4().hex
        takes = {key: {"file": f"working/narration/{ident}/{key}.wav", "voice": readings[key]["voice"], "sha256": digest(staging / f"{key}.wav"),
                       **timings[key]} for key in ("A", "B")}
        if digest(folder / "plan.json") != initial:
            raise ValueError("The plan changed during synthesis. Audition the current line.")
        dest = target / ident
        dest.mkdir()
        for key in takes:
            (staging / f"{key}.wav").replace(dest / f"{key}.wav")
        shot["audition"] = {"id": ident, "script": script, "takes": takes, "source_sha256": shot["source_sha256"],
                            "clip": shot["clip"], "speech_free_confirmed": confirmed_silent}
        if not shot.get("expected_say"):
            shot["expected_say"] = script
        rw.invalidate_approval(folder)
        write_json(folder / "plan.json", plan)
    rw.make_html(folder, plan)
    return {"stage":"review_readings", "scene":scene, "audition":ident,
            "takes":{key:str(folder / row["file"]) for key,row in takes.items()}}


def recorded_timing(folder, wav, model):
    import wave
    with wave.open(str(wav)) as stream:
        duration = stream.getnframes() / stream.getframerate()
    with tempfile.TemporaryDirectory(dir=folder / "working") as work:
        root = Path(work)
        mono = root / "speech.wav"
        run(["ffmpeg","-v","error","-i",wav,"-ac","1","-ar","16000","-c:a","pcm_s16le",mono])
        manifest = root / "batch.json"
        write_json(manifest, {"language":"en", "model":model, "jobs":[{"source":"recorded narration",
                   "source_sha256":digest(mono),"wav":str(mono),"cache":str(root / "words.json")}]})
        run([runtime(), Path(__file__).with_name("speech_batch.py"), manifest])
        words = [{"text":w["w"],"start":w["s"],"end":w["e"]} for w in read_json(root / "words.json")["words"]]
    return {"duration":duration, "words":words}


def select(rw, slug, scene, take=None, audition_id=None, recording=None, confirmed_silent=False):
    folder, plan = rw.plan_at(slug)
    initial = digest(folder / "plan.json")
    candidate = next((s.get("audition", {}) for s in plan["shots"] if s["id"] == scene), {})
    shot = scene_for_voice(folder, plan, scene, confirmed_silent)
    dest = folder / "assets/narration"
    dest.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder / "working") as work:
        if recording:
            source = Path(recording).expanduser().resolve(strict=True)
            local = Path(work) / "recorded.wav"
            run(["ffmpeg","-v","error","-i",source,"-vn","-ac","1","-ar","48000","-c:a","pcm_s16le",local])
            data = recorded_timing(folder, local, plan.get("speech_model"))
            kind = "recorded"
        else:
            if (not candidate or audition_id != candidate["id"] or take not in ("A","B")
                    or candidate["script"] != shot.get("expected_say") or candidate["clip"] != shot["clip"]
                    or candidate["source_sha256"] != shot["source_sha256"]):
                raise ValueError("Choose A or B from the current scene audition.")
            data = candidate["takes"][take]
            local = (folder / data["file"]).resolve()
            if not local.is_relative_to((folder / "working/narration").resolve()) or digest(local) != data["sha256"]:
                raise ValueError("Audition audio changed. Generate fresh readings.")
            kind = "kokoro"
        clip_duration = shot["clip"][1] - shot["clip"][0]
        if data["duration"] > clip_duration + .00001:
            raise ValueError("The reading exceeds the picture. Extend the source clip or audition a shorter reading.")
        sha = digest(local)
        path = dest / (sha + ".wav")
        if digest(folder / "plan.json") != initial:
            raise ValueError("The plan changed. Review the current scene.")
        if not path.is_file() or digest(path) != sha:
            staged = Path(work) / "selected.wav"
            shutil.copyfile(local, staged)
            staged.replace(path)
        words = data["words"]
        text = " ".join(w["text"] for w in words)
        size = 6 if plan.get("project_type") == "video" else 3
        pages = [" ".join(text.split()[i:i+size]) for i in range(0,len(words),size)]
        shot.update(narration={"kind":kind,"file":path.relative_to(folder).as_posix(),"sha256":sha,
                               "duration":data["duration"], "take":take}, say=text, words=words,
                    caption_pages=pages, text_confirmed=(kind=="kokoro"))
        if kind == "kokoro" and data.get("voice"):
            shot["narration"]["voice"] = data["voice"]
        shot.pop("voice_mode", None)
        shot.pop("audition", None)
        rw.invalidate_approval(folder)
        write_json(folder / "plan.json", plan)
    rw.make_html(folder, plan)
    return {"scene":scene,"voice":kind,"stage":"review_plan_and_audio"}


def selected_file(folder, shot):
    take = shot["narration"]
    path = (folder / take["file"]).resolve()
    if (take.get("kind") not in ("kokoro","recorded") or not path.is_relative_to((folder / "assets/narration").resolve())
            or not path.is_file() or digest(path) != take["sha256"]):
        raise ValueError("Selected narration changed. Select and review a fresh take.")
    return path
