"""Scene voice selection and optional real Kokoro + Hyperframes export checks."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audio_library
import narration
import reel_commands
import reel_workflow as rw


class NarrationTests(unittest.TestCase):
    def test_project_music_and_voice_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            script = base / "script.json"
            rw.write_json(script, {"title": "Demo", "shots": [{"expected_say": "Try this."}]})
            source = base / "inputs" / "1.mp4"
            source.parent.mkdir()
            source.write_bytes(b"fixture")
            with patch.object(rw, "STUDIO", base), patch.object(rw, "make_html"):
                rw.write_json(base / "settings.json", {"defaultMusicTrack": "music-bubbles", "defaultNarrationVoice": "af_bella"})
                with patch.object(rw, "project", return_value=base / "reel"):
                    reel_commands.draft(rw, "reel", script)
                rw.write_json(base / "settings.json", {"defaultMusicTrack": "none", "defaultNarrationVoice": "am_michael"})
                with patch.object(rw, "PROJECT_KIND", "videos"), patch.object(rw, "project", return_value=base / "video"), \
                        patch.object(rw, "input_folder", return_value=source), patch.object(rw, "probe", return_value={"duration": 4}), \
                        patch.object(reel_commands, "quality"):
                    rw.init("video", source, "Demo")
            for project, music, voice in [("reel", "music-bubbles", "af_bella"), ("video", None, "am_michael")]:
                audio = rw.read_json(base / project / "plan.json")["audio"]
                self.assertEqual(audio["music"], music)
                self.assertEqual(audio["recommended_music"], music)
                self.assertEqual(audio["narration_voice"], voice)
                takes = narration.delivery_for("Try this.", {}, audio["narration_voice"])
                self.assertEqual([row["voice"] for row in takes.values()], [voice, voice])
            self.assertEqual(narration.delivery_for("Try this.", {})["A"]["voice"], "af_heart")

    def test_directions_preserve_caption_text_and_distinct_readings(self):
        line = "Open the API."
        rows = narration.delivery_for(line, {"B":{"phrases":[{"text":line,"pronounce":{"API.":"A P I."}}]}})
        self.assertNotEqual(rows["A"]["speed"], rows["B"]["speed"])
        with self.assertRaisesRegex(ValueError, "approved words"):
            narration.delivery_for(line, {"A":{"phrases":[{"text":"Different script."}]}})
        with self.assertRaisesRegex(ValueError, "Kokoro preset"):
            narration.delivery_for(line, {"A":{"voice":"say"}})

    def test_only_verified_recordings_for_new_selections(self):
        for ident in ("music-bubbles", "sfx-pop-1"):
            audio_library.require_verified(ident)
        with self.assertRaisesRegex(ValueError,"CC0 recording"):
            audio_library.require_verified("sfx-click-1")  # Publisher reports pack downloads.
        legacy = {"shots":[{"id":"01","clip":[0,1]}],"audio":{"sfx":[{"scene":"01","at":0,"sound":"sfx-click-1"}]}}
        audio_library.validate_audio(legacy)
        legacy["audio"]["selection_policy"]="verified-recording"
        with self.assertRaisesRegex(ValueError,"CC0"):
            audio_library.validate_audio(legacy)


@unittest.skipUnless(os.getenv("NARRATION_INTEGRATION")=="1","Requires cached local Kokoro and Chromium")
class NarrationExports(unittest.TestCase):
    def exercise(self, kind):
        import numpy as np
        from media_profile import validate_export
        from speech_batch import transcribe_jobs

        retain = os.getenv("AUDIO_TEST_OUTPUT")
        work = Path(tempfile.mkdtemp(prefix="audio-v2-",dir=retain)) if retain else Path(self.enterContext(tempfile.TemporaryDirectory()))
        folder = work / kind / "audio-test"
        footage = work / "inputs"
        footage.mkdir()
        portrait = kind=="reels"
        size = "180x320" if portrait else "320x180"
        lines = ["Watch the build finish.", "The new screen is ready."]
        if portrait:
            lines[0] = "Recorded opener"
        for i,length in enumerate([5,6]):
            cmd = ["ffmpeg","-v","error","-f","lavfi","-i",f"testsrc2=s={size}:r=12:d={length}"]
            if portrait and i==0:
                src = os.getenv("AUDIO_TEST_RECORDING") or rw.ENGINE/"examples/example/audio/01-9e732c03.wav"
                cmd += ["-i",src,"-map","0:v","-map","1:a","-af","apad","-c:a","aac"]
            rw.run(cmd+["-t",str(length),"-c:v","libx264","-pix_fmt","yuv420p",footage/f"{i+1}.mp4"])
        manifest = work / "script.json"
        rw.write_json(manifest, {"title":"Audio workflow check","shots":[{"expected_say":s} for s in lines]})
        with patch.object(rw,"PROJECT_KIND",kind), patch.object(rw,"project",return_value=folder), patch.object(rw,"input_folder",return_value=footage):
            with patch.object(rw, "load_settings", return_value={"defaultMusicTrack": "music-bubbles", "defaultNarrationVoice": "am_michael"}):
                reel_commands.draft(rw,"audio-test",manifest)
            rw.write_json(folder/"script-approval.json",{"script":lines,"message":"Automated fixture only"})
            reel_commands.attach(rw,"audio-test",footage)
            rw.analyze("audio-test")
            plan = rw.read_json(folder/"plan.json")
            if portrait:
                with self.assertRaisesRegex(ValueError,"already has recorded speech"):
                    narration.audition(rw,"audio-test","01",confirmed_silent=True)
                self.assertTrue(plan["shots"][0]["words"])
                # Preserve the five-second picture for an identifiable late cue.
                shot=plan["shots"][0]
                offset=shot["clip"][0]
                for word in shot["words"]:
                    word["start"]+=offset
                    word["end"]+=offset
                shot.update(clip=[0,5],text_confirmed=True)
                rw.write_json(folder/"plan.json",plan)
            for scene in (["02"] if portrait else ["01","02"]):
                result = narration.audition(rw,"audio-test",scene)
                self.assertNotEqual(rw.digest(Path(result["takes"]["A"])),rw.digest(Path(result["takes"]["B"])))
                with self.assertRaisesRegex(ValueError,"current scene audition"):
                    narration.select(rw,"audio-test",scene,"B","outdated")
                narration.select(rw,"audio-test",scene,"B",result["audition"])
            plan=rw.read_json(folder/"plan.json")
            for shot in plan["shots"]:
                shot["vibha"]={"status":"none","effects":[]}
                if shot.get("narration"):
                    self.assertEqual(shot["narration"]["voice"], "am_michael")
                    self.assertEqual(shot["say"], " ".join(w["text"] for w in shot["words"]))
                    self.assertLessEqual(shot["words"][-1]["end"],shot["narration"]["duration"])
            plan["visual_selection"]="Automated test footage only"
            self.assertEqual(plan["audio"]["music"], "music-bubbles")
            plan["audio"].update(sfx=[{"scene":"02","sound":"sfx-pop-1","at":4.5,"gain":.23}])
            rw.write_json(folder/"plan.json",plan)
            rw.preview("audio-test")
            record=rw.read_json(folder/"preview.json")
            self.assertEqual(record["scene_audio_times"]["02"],[5,11])
            self.assertEqual(record["mix_version"],2)
            rw.approve("audio-test",record["id"],"Automated fixture only")
            exported=Path(rw.render("audio-test")["file"])
            validate_export(rw.probe(exported),plan["output_profile"],132)
            def pcm(file):
                data=subprocess.check_output(["ffmpeg","-v","error","-i",str(file),"-vn","-ar","48000","-ac","1","-f","f32le","-"])
                return np.frombuffer(data,dtype="<f4")
            mix_file=Path(record["mix_sample"])
            reference,encoded=pcm(mix_file),pcm(exported)
            self.assertEqual(len(reference),11*48000)
            for start,end in [(0,5),(5,11),(9.48,9.80)]:
                sl=slice(round(start*48000),round(end*48000))
                correlation=np.corrcoef(reference[sl],encoded[sl])[0,1]
                self.assertGreater(correlation,.98,f"Changed audio at {start}s: {correlation}")
            # Verify intelligibility on the delivered, music-backed audio using independent ASR.
            spoken=work/"delivered.wav"
            rw.run(["ffmpeg","-v","error","-ss","5","-i",exported,"-t","4","-ac","1","-ar","16000",spoken])
            rows=transcribe_jobs([{"wav":str(spoken),"cache":str(work/"heard.json"),"source":"delivered scene","source_sha256":rw.digest(spoken)}])
            heard=" ".join(w["w"].lower() for w in rows[0]["words"])
            self.assertIn("screen",heard)
            self.assertIn("ready",heard)
            timings={w["text"].strip(".").lower():w["start"] for w in plan["shots"][1]["words"]}
            for word in rows[0]["words"]:
                token=word["w"].strip(".").lower()
                if token in ("screen","ready"):
                    self.assertAlmostEqual(word["s"],timings[token],delta=.18)
            captions=(folder/"hyperframes/compositions/captions.html").read_text()
            caption_end=5+plan["shots"][1]["words"][-1]["end"]
            self.assertIn(f'{{opacity:0}},{caption_end:.12f}',captions)
            plan["audio"]["sfx"][0]["gain"]=.04
            rw.write_json(folder/"plan.json",plan)
            with self.assertRaisesRegex(ValueError,"No approval"):
                rw.approval_check(folder)
            print(f"{kind}: verified 11s, late cue at 9.5s; heard {heard!r}; {exported}",flush=True)

    def test_mixed_reel(self):
        self.exercise("reels")

    def test_fully_narrated_youtube(self):
        self.exercise("videos")
