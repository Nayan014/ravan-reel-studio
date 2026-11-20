"""Opt-in real ffmpeg + local Chromium/Hyperframes acceptance tests (no user media)."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reel_workflow as rw
import reel_pipeline as rp
from media_profile import profile,validate_export,inspect_source
from audio_library import catalogue,defaults

@unittest.skipUnless(os.environ.get('REEL_INTEGRATION')=='1','Set REEL_INTEGRATION=1 for real local-browser render tests')
class PipelineIntegration(unittest.TestCase):
 def exercise(self,width,height,fps,rotate=False,effect=False,lighting=False):
  with tempfile.TemporaryDirectory(dir=rw.STUDIO/'outputs') as temp:
   f=Path(temp)
   for n in ['raw','assets','working']:(f/n).mkdir()
   rate=rp.rate(fps);duration=12/float(rate);source=f/'raw/1.mp4'
   rw.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',f'testsrc2=s={width}x{height}:r={fps}:d={duration}','-f','lavfi','-i',f'sine=frequency=440:duration={duration}','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-shortest',source])
   if rotate:
    rotated=f/'raw/rotated.mp4';rw.run(['ffmpeg','-y','-v','error','-i',source,'-c','copy','-metadata:s:v:0','rotate=90',rotated]);rotated.replace(source)
   info=inspect_source(source);self.assertEqual(info['fps_fraction'],str(rate));self.assertFalse(info['variable_frame_rate'])
   out=profile(min(width,height),max(width,height),fps)
   shot={'id':'01','source':'1.mp4','source_sha256':rw.digest(source),'clip':[0,duration],'say':'Hello','words':[{'text':'Hello','start':0,'end':duration*.8}],'caption_pages':['Hello'],'text_confirmed':True,'layout':'full','focus':[.5,.4],'vibha':{'status':'selected' if effect else 'none','effects':[{'id':13,'start':0,'end':duration,'options':{'text':'LABEL'}}] if effect else []},'remotion':{'status':'none'}}
   plan={'pipeline_version':2,'renderer':'hyperframes','title':'Synthetic acceptance fixture','phase':'recorded','style':'flat','palette':'clay','output_profile':out,'audio':defaults(),'visual_selection':'Synthetic automated fixture only','shots':[shot]}
   if lighting:plan['lighting']={'preset':'natural-studio'}
   rw.write_json(f/'plan.json',plan)
   with patch.object(rw,'project',return_value=f):
    result=rp.preview('test');record=rw.read_json(f/'preview.json');self.assertEqual(result['output_profile'],out)
    from PIL import Image
    for frame in record['frame_details']:
     with Image.open(frame['file']) as image:self.assertEqual(image.size,(out['width'],out['height']))
    if width==180:
     # Native code is editable and its exact reviewed bytes are preserved during builds.
     authored=f/'hyperframes/compositions/shot-01.html';authored.write_text(authored.read_text().replace('background:#111','background:#221'))
     with self.assertRaisesRegex(ValueError,'stale'):rw.approve('test',record['id'],'stale fixture')
     rp.preview('test');record=rw.read_json(f/'preview.json')
     normalized=list((f/'working/normalized').glob('*.mp4'));times={str(p):p.stat().st_mtime_ns for p in normalized}
     old_files=record['files'];new_track=next(t['id'] for t in catalogue().values() if t['kind']=='music' and t['id']!='music-lofi')
     changed=rp.choose_music('test',new_track);self.assertNotEqual(changed['preview_id'],record['id']);record=rw.read_json(f/'preview.json');self.assertEqual(record['files'],old_files)
     self.assertEqual(times,{str(p):p.stat().st_mtime_ns for p in normalized})
     self.assertIn('background:#221',authored.read_text())
    rw.approve('test',record['id'],'Synthetic automated acceptance only')
    exported=rp.render('test');encoded=rw.probe(Path(exported['file']));validate_export(encoded,out,12)
    if lighting:
     configs=list((f/'working/vibha').glob('*/effects.json'));self.assertTrue(configs)
     self.assertTrue(all(rw.read_json(path)['effects'][0]['fx']=='studio-light' for path in configs))
    self.assertEqual(encoded['frame_count'],12)
    html=(f/'hyperframes/index.html').read_text();self.assertEqual(html.count('id="approved-mix"'),1);self.assertEqual(html.count('<div id="captions"'),1)
    self.assertNotIn('data-has-audio="true"',(f/'hyperframes/compositions/shot-01.html').read_text())
    rw.run(['ffmpeg','-y','-v','error','-i',exported['file'],'-frames:v','1',f'/tmp/reel-verified-{width}-{fps.replace("/","-")}.png'])
    if effect:
     clips=list((f/'working/vibha').glob('*/effected.mp4'));stamp={str(p):p.stat().st_mtime_ns for p in clips};self.assertTrue(clips)
     # Music-only revision reuses all approved visual stills AND full effected videos.
     rp.choose_music('test',None);record=rw.read_json(f/'preview.json');rw.approve('test',record['id'],'Synthetic music revision');rp.render('test')
     self.assertEqual(stamp,{str(p):p.stat().st_mtime_ns for p in clips})
     # Caption revision needs fresh frames but reuses caption-free full Vibha video.
     updated=rw.read_json(f/'plan.json');updated['shots'][0]['captions_visible']=False;rw.write_json(f/'plan.json',updated)
     rp.preview('test');record=rw.read_json(f/'preview.json');rw.approve('test',record['id'],'Synthetic caption revision');rp.render('test')
     self.assertEqual(stamp,{str(p):p.stat().st_mtime_ns for p in clips})
    # Changing profile or source after approval must fail before another full render.
    plan=rw.read_json(f/'plan.json');plan['output_profile']['fps']='24';rw.write_json(f/'plan.json',plan)
    with self.assertRaisesRegex(ValueError,'No approval'):rw.approval_check(f)
    print(json.dumps({'verified':f'{width}x{height}@{fps}','encoded':encoded,'rotation':rotate,'effect':effect}),flush=True)
 def test_4k60(self):self.exercise(2160,3840,'60')
 def test_4k30(self):self.exercise(2160,3840,'30')
 def test_1080p60(self):self.exercise(1080,1920,'60')
 def test_fractional_rate_rotated(self):self.exercise(320,180,'60000/1001',rotate=True)
 def test_landscape_crop(self):self.exercise(1920,1080,'60')
 def test_effects_music_and_cache(self):self.exercise(180,320,'60',effect=True)
 def test_studio_lighting_clean_take(self):self.exercise(360,640,'30',lighting=True)
 def test_source_voice_synchronization(self):
  import numpy as np
  import subprocess
  with tempfile.TemporaryDirectory(dir=rw.STUDIO/'outputs') as temp:
   f=Path(temp)
   for name in ['raw','assets','working']:(f/name).mkdir()
   shots=[]
   for i,frequency in enumerate([440,770],1):
    file=f/f'raw/{i}.mp4'
    rw.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c=black:s=180x320:r=60:d=1','-f','lavfi','-i',f'aevalsrc=sin(2*PI*{frequency}*t)*between(t\\,0.2\\,0.5):s=48000:d=1','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',file])
    shots.append({'id':f'{i:02d}','source':file.name,'source_sha256':rw.digest(file),'clip':[0,1],'say':'Tone','words':[{'text':'Tone','start':.2,'end':.5}],'caption_pages':['Tone'],'text_confirmed':True,'layout':'full','focus':[.5,.4],'vibha':{'status':'none','effects':[]},'remotion':{'status':'none'}})
   p={'pipeline_version':2,'renderer':'hyperframes','title':'Synthetic voice-sync test','style':'flat','palette':'clay','phase':'recorded','visual_selection':'Synthetic test','shots':shots,'output_profile':profile(180,320,'60'),'audio':{**defaults(),'music':None}}
   rw.write_json(f/'plan.json',p)
   with patch.object(rw,'project',return_value=f):
    rp.preview('test');r=rw.read_json(f/'preview.json');rw.approve('test',r['id'],'Synthetic synchronization test');result=rp.render('test')
   voice=next((f/'working/audio').glob('voice-*.wav'))
   def samples(path):
    b=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-vn','-ar','48000','-ac','1','-f','f32le','-'],capture_output=True,check=True).stdout
    return np.frombuffer(b,dtype='<f4')
   expected,encoded=samples(voice),samples(result['file']);length=min(len(expected),len(encoded))//48*48
   a=np.sqrt((expected[:length].reshape(-1,48)**2).mean(axis=1));b=np.sqrt((encoded[:length].reshape(-1,48)**2).mean(axis=1))
   lag=int(np.argmax(np.correlate(b,a,'full'))-(len(a)-1));self.assertLessEqual(abs(lag),25,'Voice shifted more than25ms during assembly')
   ratio=np.linalg.norm(b)/np.linalg.norm(a);self.assertGreater(ratio,.85);self.assertLess(ratio,1.15,'Voice should not be doubled')
   for start in [.2,1.2]:
    self.assertGreater(b[int((start+.05)*1000):int((start+.2)*1000)].mean(),b[int((start-.1)*1000):int((start-.03)*1000)].mean()*5)

if __name__=='__main__':unittest.main()
