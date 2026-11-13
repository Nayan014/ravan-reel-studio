import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from media_profile import profile, detect, frames_for,validate_export
from speech_batch import transcribe_jobs
import reel_workflow as rw
import reel_commands as commands
from audio_library import catalogue,defaults

class QualityTests(unittest.TestCase):
 def source(self,w,h,fps,**kw):return dict(width=w,height=h,fps=float(fps.split('/')[0])/float(fps.split('/')[1]) if '/' in fps else float(fps),fps_fraction=fps,**kw)
 def test_matching_profiles_and_mixed_choices(self):
  for w,h,fps in [(3840,2160,'60'),(2160,3840,'30'),(1920,1080,'60'),(1920,1080,'60000/1001')]:
   with self.subTest(fps=fps,w=w):
    result=detect([self.source(w,h,fps)]*2);self.assertFalse(result['requires_choice']);self.assertEqual(result['output']['width'],min(w,h));self.assertEqual(result['output']['fps'],fps)
  self.assertTrue(detect([self.source(1920,1080,'30'),self.source(3840,2160,'60')])['requires_choice'])
  self.assertTrue(detect([self.source(1080,1920,'60',variable_frame_rate=True)])['requires_choice'])
  self.assertTrue(detect([self.source(3840,2160,'120')])['requires_choice'])
 def test_exact_counts_and_encoded_checks(self):
  out=profile(1080,1920,'60000/1001');n=frames_for(1.001,out);self.assertEqual(n,60)
  good=dict(width=1080,height=1920,fps_fraction='60000/1001',fps=59.94,frame_count=n,duration=1.001,has_audio=True)
  validate_export(good,out,n)
  for key,value in [('width',2160),('fps_fraction','60'),('frame_count',59),('duration',2),('has_audio',False)]:
   with self.subTest(key=key),self.assertRaises(ValueError):validate_export({**good,key:value},out,n)
 def test_rotation_display_dimensions(self):
  import video_workflow as vw
  payload={'format':{'duration':'1'},'streams':[{'codec_type':'video','width':1920,'height':1080,'r_frame_rate':'60000/1001','avg_frame_rate':'60000/1001','nb_frames':'60','side_data_list':[{'rotation':90}]},{'codec_type':'audio','duration':'1'}]}
  with patch.object(vw,'run',return_value=json.dumps(payload)):
   info=vw.probe('unused');self.assertEqual((info['width'],info['height']),(1080,1920));self.assertEqual(info['fps_fraction'],'60000/1001')
 def test_cached_batch_transcription(self):
  with tempfile.TemporaryDirectory() as name:
   path=Path(name);calls=[];jobs=[{'source':str(i),'wav':str(path/f'{i}.wav'),'cache':str(path/f'{i}.json'),'source_sha256':str(i)} for i in range(2)]
   def worker(wav):calls.append(wav);return [{'w':'hello','s':0,'e':.2,'probability':.9}]
   first=transcribe_jobs(jobs,worker=worker);self.assertEqual(len(calls),2)
   second=transcribe_jobs(jobs,worker=lambda _:self.fail('cache miss'));self.assertTrue(all(r['cached'] for r in second))
   self.assertFalse(any(r['cached'] for r in first))
 def test_audio_catalogue_has_existing_credited_files(self):
  from audio_library import audio_file
  items=catalogue();self.assertEqual(sum(t['kind']=='music' for t in items.values()),4);self.assertEqual(sum(t['kind']=='sfx' for t in items.values()),23)
  for ident,item in items.items():self.assertTrue(audio_file(ident).exists());self.assertTrue(item['source']);self.assertTrue(item['license']);self.assertGreater(item['duration'],0)
 def test_speech_backend_numpy_values_produce_portable_cache_json(self):
  import numpy as np
  with tempfile.TemporaryDirectory() as name:
   cache=Path(name)/'speech.json'
   job={'source':'synthetic','wav':str(Path(name)/'speech.wav'),'cache':str(cache),'source_sha256':'fixture'}
   result=transcribe_jobs([job],worker=lambda _:[{'w':'hello','s':np.float32(.1),'e':np.float32(.3),'probability':np.float64(.4)}])[0]
   value=json.loads(cache.read_text());self.assertAlmostEqual(value['words'][0]['probability'],.4)
   self.assertIs(type(result['words'][0]['s']),float);self.assertIs(type(result['words'][0]['probability']),float)
 def test_draft_and_attach_preserve_approved_script(self):
  with tempfile.TemporaryDirectory(dir=rw.STUDIO/'outputs') as temp:
   base=Path(temp);folder=base/'draft';manifest=base/'draft.json';rw.write_json(manifest,{'title':'Test','shots':[{'expected_say':'Keep my words','shooting_note':'Look at camera'}]})
   source=base/'recordings';source.mkdir();(source/'1.mp4').write_bytes(b'test original')
   with patch.object(rw,'project',return_value=folder):
    commands.draft(rw,'draft',manifest);before=rw.read_json(folder/'plan.json');self.assertEqual(before['phase'],'draft')
    with self.assertRaisesRegex(ValueError,'Approve'):commands.attach(rw,'draft',source)
    rw.write_json(folder/'script-approval.json',{'script':['Keep my words']})
    # Test fixture uses a temporary input root; keep production's containment check in force.
    fakeStudio=base/'studio';(fakeStudio/'inputs').mkdir(parents=True);shutilSource=fakeStudio/'inputs/takes';source.rename(shutilSource)
    with patch.object(rw,'make_html'),patch.object(rw,'STUDIO',fakeStudio),patch.object(commands,'probe',return_value={'duration':2,'has_audio':True}),patch.object(commands,'inspect_source',return_value={'duration':2,'has_audio':True,'width':1920,'height':1080,'fps':60,'fps_fraction':'60'}):commands.attach(rw,'draft',shutilSource)
    after=rw.read_json(folder/'plan.json');self.assertEqual(after['shots'][0]['expected_say'],'Keep my words');self.assertEqual(after['phase'],'recorded');self.assertEqual(after['output_profile']['fps'],'60')
    with self.assertRaisesRegex(ValueError,'unrecorded'):commands.attach(rw,'draft',shutilSource)

if __name__=='__main__':unittest.main()
