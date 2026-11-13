"""Regression: stateful still previews must replay the effect's earlier frames."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from video_workflow import run, runtime, effects_root


class StatefulPreviewParity(unittest.TestCase):
    def test_pause_point_freezes_same_moment_in_still_and_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'moving.mp4'; plan=root/'plan.json'
            run(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=s=180x320:r=30:d=1',
                 '-f','lavfi','-i','sine=frequency=440:duration=1','-c:v','libx264','-pix_fmt','yuv420p',
                 '-c:a','aac','-shortest',source])
            plan.write_text(json.dumps({'effects':[{'fx':'pause-point','start':0.1,'end':0.9,'text':'TEST'}]}))
            common=[runtime(),effects_root()/'scripts/fx.py','--plan',plan,source]
            run(common+[root/'still.png','--still','0.7','--warmup','--width','360'])
            run(common+[root/'render.mp4','--width','360'])
            run(['ffmpeg','-y','-v','error','-i',root/'render.mp4','-ss','0.7','-frames:v','1',root/'frame.png'])
            # Allow H.264 compression differences; the moving source makes a wrong frozen moment diverge strongly.
            import numpy as np
            from PIL import Image
            a=np.asarray(Image.open(root/'still.png').convert('RGB'),dtype=float)
            b=np.asarray(Image.open(root/'frame.png').convert('RGB'),dtype=float)
            self.assertEqual(a.shape,b.shape)
            self.assertLess(float(np.abs(a-b).mean()),4.0)

if __name__=='__main__': unittest.main()
