import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from package_release import package


class PublicationTests(unittest.TestCase):
 def fixture(self,base):
  root=base/'source';root.mkdir()
  def put(name,value='safe'):
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value);return p
  put('README.md');put('LICENSE');put('skills/wf/SKILL.md');put('scripts/tool.py')
  for name in ['inputs/private.mp4','outputs/reels/private/plan.json','skills/effects/.venv/private','skills/effects/.cache/model','tools/hyperframes/node_modules/private','docs/local/private.md','docs/intro-reel-plan.html','docs/Intro_Reel_Shoot_Plan.pdf','tools/kit/.env','tools/kit/.env.local','assets/credentials.json','assets/server.pem','.claude/settings.local.json','.gemini/settings.json','.agents/session.json','assets/accidental.MOV','examples/real-recording.mp4','docs/interview.wav']:
   put(name,'PRIVATE_FIXTURE')
  put('tools/kit/.env.example','TOKEN=');put('tools/techno-reel/public/sfx/click-1.wav','licensed media fixture');put('tools/kit/src/scenes/local/README.md');put('examples/demo/export/demo.mp4','synthetic fixture')
  (root/'.agents/skills').mkdir(parents=True);(root/'.agents/skills/wf').symlink_to('../../skills/wf')
  return root,put
 def test_private_files_stay_local_and_relative_skills_survive(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);root,put=self.fixture(base);dest=base/'public';result=package(dest,root)
   self.assertGreater(result['files'],0)
   self.assertEqual(list((dest/'inputs').iterdir()),[dest/'inputs/.gitkeep'])
   self.assertEqual(list((dest/'outputs').iterdir()),[dest/'outputs/.gitkeep'])
   self.assertTrue((dest/'.agents/skills/wf/SKILL.md').is_file())
   self.assertTrue((dest/'tools/kit/.env.example').is_file());self.assertTrue((dest/'tools/techno-reel/public/sfx/click-1.wav').is_file());self.assertTrue((dest/'examples/demo/export/demo.mp4').is_file())
   self.assertTrue((dest/'tools/kit/src/scenes/local/README.md').is_file())
   manifest=json.loads((dest/'PUBLICATION_MANIFEST.json').read_text());self.assertFalse(any('PRIVATE_FIXTURE' in p.read_text() for p in dest.rglob('*') if p.is_file()))
   self.assertTrue((root/'inputs/private.mp4').is_file());self.assertTrue(manifest['files'])
 def test_existing_destinations_and_escaping_links_are_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);root,put=self.fixture(base);dest=base/'public';dest.mkdir()
   with self.assertRaisesRegex(ValueError,'already exists'):package(dest,root)
   (root/'docs').mkdir(exist_ok=True);(root/'docs/leak').symlink_to(base)
   with self.assertRaisesRegex(ValueError,'symlink'):package(base/'other',root)
   self.assertFalse((base/'other').exists())
 def test_public_source_cannot_be_its_own_destination(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);root,_=self.fixture(base)
   with self.assertRaisesRegex(ValueError,'separate'):package(root/'docs/public',root)
   with self.assertRaisesRegex(ValueError,'separate'):package(root/'.git',root)
 def test_git_ignores_real_media_and_allows_only_explicit_examples(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);subprocess.run(['git','init','-q',str(root)],check=True)
   studio=Path(__file__).resolve().parents[1];(root/'.gitignore').write_bytes((studio/'.gitignore').read_bytes())
   hidden=['inputs/take.MOV','outputs/reels/a/export/final.mp4','outputs/releases/ravan-reel-studio/README.md','accidental.MOV','assets/interview.Mp4','examples/my-real-video.webm','voice.wav','.env.local']
   public=['examples/demo/export/demo.mp4','examples/demo/export/cover.png','tools/techno-reel/public/music/lofi.mp3','tools/techno-reel/public/sfx/click-1.wav','tools/techno-reel/examples/example/audio/01-9e732c03.wav','inputs/.gitkeep','outputs/.gitkeep']
   result=subprocess.run(['git','-C',str(root),'check-ignore','--no-index','--stdin'],input='\n'.join(hidden+public)+'\n',capture_output=True,text=True)
   self.assertEqual(result.returncode,0);self.assertEqual(set(result.stdout.splitlines()),set(hidden))


if __name__=='__main__':unittest.main()
