import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reel_workflow as rw
from text_layers import render_layers,validate_layers
from sync_text_layers import sync

LAYER={'id':'headline','text':'BUILD WITH AI','color':'#ffcc00','fontSize':88,'x':.08,'y':.15}


class TextLayersTests(unittest.TestCase):
    def test_raster_is_transparent_outside_positioned_text_and_scales(self):
        import numpy as np
        full=render_layers([LAYER]);small=render_layers([LAYER],540,960)
        self.assertEqual(full.size,(1080,1920));self.assertEqual(small.size,(540,960))
        a=np.asarray(full);self.assertGreater(int(a[:,:,3].sum()),0)
        self.assertEqual(int(a[:280,:,3].sum()),0)
        self.assertEqual(int(a[500:,:,3].sum()),0)
        self.assertTrue(((a[:,:,0]==255)&(a[:,:,1]==204)&(a[:,:,3]>0)).any())
        self.assertEqual(full.tobytes(),render_layers([LAYER]).tobytes())
    def test_invalid_text_properties_and_duplicates_are_rejected(self):
        for change in [{'fontSize':float('nan')},{'x':2},{'y':-1},{'color':'red;display:none'},{'text':''}]:
            with self.assertRaises(ValueError):validate_layers([{**LAYER,**change}])
        with self.assertRaises(ValueError):validate_layers([LAYER,LAYER])
    def test_effects_cli_renders_saved_text_layers_in_an_actual_still(self):
        from video_workflow import run,runtime,effects_root
        import numpy as np
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.mp4';plan=root/'plan.json';still=root/'still.png'
            run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=black:s=180x320:r=12:d=1','-c:v','libx264','-pix_fmt','yuv420p',source])
            plan.write_text(json.dumps({'effects':[{'fx':'lean-in','start':0,'end':1}],'text_layers':[LAYER]}))
            run([runtime(),effects_root()/'scripts/fx.py','--plan',plan,source,still,'--still','0.5','--width','180'])
            pixels=np.asarray(Image.open(still).convert('RGB'))
            self.assertGreater(int(((pixels[:,:,0]>200)&(pixels[:,:,1]>140)&(pixels[:,:,2]<60)).sum()),15)
    def test_remotion_assembly_stages_the_shared_raster(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);public=folder/'public';public.mkdir()
            source=folder/'source.mp4';source.write_bytes(b'source fixture')
            shot={'id':'01','say':'Real words','words':[],'clip':[0,1],'layout':'full',
                  'caption_pages':['Real words'],'remotion':{'status':'none'},'text_layers':[LAYER]}
            plan={'title':'Fixture','style':'flat','palette':'clay','shots':[shot]}
            with patch.object(rw,'copy_public',return_value=public),patch.object(rw,'normalized',return_value=source),patch.object(rw,'effects_for',return_value=[]):
                _,reel,_=rw.assemble(folder,plan)
            file=public/reel['shots'][0]['studioTextImage']
            from PIL import Image
            self.assertEqual(Image.open(file).tobytes(),render_layers([LAYER]).tobytes())
    def test_hyperframes_sync_uses_identical_raster_and_is_idempotent(self):
        root=rw.STUDIO/'outputs/reels';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            project=Path(tmp);composition=project/'hyperframes';composition.mkdir()
            plan={'shots':[{'id':'01','text_layers':[LAYER]}]}
            (project/'plan.json').write_text(json.dumps(plan))
            index=composition/'index.html';index.write_text('<html><body><div id="shot-01" data-start="0.5" data-duration="1.5"></div></body></html>')
            self.assertTrue(sync(composition)['changed'])
            self.assertIn('studio-visual-text',index.read_text())
            self.assertIn('opacity:1},0.5)',(composition/'compositions/studio-visual-text.html').read_text())
            from PIL import Image
            self.assertEqual(Image.open(composition/'assets/studio-text/01.png').tobytes(),render_layers([LAYER]).tobytes())
            before=index.stat().st_mtime_ns;self.assertFalse(sync(composition)['changed']);self.assertEqual(index.stat().st_mtime_ns,before)
            plan['shots'][0]['text_layers']=[];(project/'plan.json').write_text(json.dumps(plan))
            sync(composition);self.assertNotIn('STUDIO TEXT START',index.read_text())

if __name__=='__main__':unittest.main()
