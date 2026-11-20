"""Portable lighting, ordering, geometry and non-presenter regression checks."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/effects/scripts'))
from studio_lighting import validate_lighting, expand_lighting, shot_lighting


class LightingConfiguration(unittest.TestCase):
    def test_disabled_plans_and_existing_effect_ids_are_preserved(self):
        plan = {'effects': [{'fx': 'orbit', 'start': 1, 'end': 2}]}
        self.assertEqual(expand_lighting(plan), plan)
        self.assertIsNone(validate_lighting(None))
        catalogue = json.loads((ROOT / 'skills/effects/references/catalogue.json').read_text())
        self.assertEqual([item['id'] for item in catalogue if isinstance(item['id'], int)], list(range(1, 52)))

    def test_light_is_compiled_before_existing_effects_without_mutation(self):
        plan = {'lighting': {'preset': 'natural-studio'}, 'effects': [{'fx': 'lean-in', 'start': 0, 'end': 2}]}
        compiled = expand_lighting(plan)
        self.assertEqual([e['fx'] for e in compiled['effects']], ['studio-light', 'lean-in'])
        self.assertEqual(len(plan['effects']), 1)
        self.assertEqual(expand_lighting(compiled), compiled)
        self.assertEqual(expand_lighting({'lighting': plan['lighting'], 'effects': []})['effects'][0]['fx'], 'studio-light')

    def test_rejects_bad_presets_and_screen_geometry(self):
        for value in [True, 'natural-studio', {}, {'preset': 'other'},
                      {'preset': 'natural-studio', 'screen_regions': 'not polygons'},
                      {'preset': 'natural-studio', 'screen_regions': [[[0, 0], [1, 1]]]},
                      *[{'preset': 'natural-studio', 'screen_regions': [[[0,0],[1,0],[v,1]]]} for v in [-.1, 1.1, float('nan'), float('inf'), True]]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_lighting(value)


class LightingPixels(unittest.TestCase):
    def context(self, w, h, person=True):
        import numpy as np
        rng = np.random.default_rng(7)
        image = np.clip(np.float32([.60, .48, .40]) + rng.normal(0,.025,(h,w,3)).astype(np.float32), 0, 1)
        mask = np.zeros((h,w), np.float32)
        if person: mask[h//3:, w//3:2*w//3] = 1
        return SimpleNamespace(W=w,H=h,img=image,m=mask,fx=w/2,fy=h*.45,fw=min(w,h)*.18)

    def test_no_person_leaves_footage_unchanged(self):
        import numpy as np
        from studio_lighting import render_studio_light
        from fx import grid, guided
        c=self.context(180,320,False);before=c.img.copy()
        render_studio_light(c,SimpleNamespace(o={},state={}),grid,guided)
        np.testing.assert_array_equal(c.img,before)

    def test_portrait_landscape_and_screen_mask_are_deterministic(self):
        import numpy as np
        from studio_lighting import render_studio_light
        from fx import grid, guided
        for w,h in [(180,320),(320,180)]:
            with self.subTest(size=(w,h)):
                c=self.context(w,h);before=c.img.copy()
                effect=SimpleNamespace(o={'screen_regions':[[[.05,.05],[.3,.05],[.3,.25],[.05,.25]]]},state={})
                render_studio_light(c,effect,grid,guided);first=c.img.copy()
                self.assertEqual(first.shape,before.shape)
                self.assertTrue(np.isfinite(first).all())
                self.assertGreaterEqual(float(first.min()),0)
                self.assertLessEqual(float(first.max()),1)
                self.assertLess(float(first[:h//4].mean()),float(before[:h//4].mean()))
                face=first[int(c.fy),int(c.fx)].mean();background=first[int(c.fy),w//8].mean()
                self.assertGreater(float(face),float(background))
                c.img=before.copy();render_studio_light(c,effect,grid,guided)
                np.testing.assert_array_equal(c.img,first)


class AdaptiveLighting(unittest.TestCase):
    def fixture(self, left, right, room):
        import numpy as np
        from studio_lighting import AdaptiveAnalysis
        rgb = np.full((120, 160, 3), room, np.uint8)
        mask = np.zeros(rgb.shape[:2], np.uint8)
        mask[30:, 45:115] = 255
        rgb[30:, 45:80] = left
        rgb[30:, 80:115] = right
        analysis = AdaptiveAnalysis(30)
        analysis.start_frame(rgb)
        sample = analysis.measure(rgb, mask, (80, 55, 60))
        c = SimpleNamespace(W=160, H=120, img=rgb.astype(np.float32)/255,
                            adaptive=sample, m=mask.astype(np.float32)/255)
        return c, analysis, rgb, mask

    def render(self, c, options=None):
        from fx import grid
        from studio_lighting import render_adaptive
        render_adaptive(c, SimpleNamespace(o=options or {}, state={}), grid)

    def test_backlight_balances_face_room_and_protects_screen_and_specular(self):
        import numpy as np
        c, _, _, _ = self.fixture(52, 52, 200)
        c.img[50, 80] = [1, .97, .8]
        c.img[60, 70] = [.35, .24, .18]
        before = c.img.copy()
        self.render(c, {'screen_regions': [[[.03,.05],[.18,.05],[.18,.23],[.03,.23]]]})
        self.assertGreater(c.img[60,70,0], before[60,70,0])
        np.testing.assert_allclose(c.img[60,70] / before[60,70], c.img[60,70,0] / before[60,70,0])
        self.assertLess(c.img[20,130,0], before[20,130,0])
        np.testing.assert_array_equal(c.img[50,80], before[50,80])
        np.testing.assert_array_equal(c.img[15,15], before[15,15])

    def test_softbox_shapes_face_and_room_while_protecting_displays(self):
        import numpy as np
        options = {'look':'softbox','screen_regions':[[[.02,.02],[.19,.02],[.19,.23],[.02,.23]]]}
        plan = expand_lighting({'lighting':{'preset':'adaptive-studio', **options},'effects':[]})
        self.assertEqual(plan['effects'][0]['look'], 'softbox')
        c = self.fixture(85, 105, 185)[0]
        original = c.img.copy()
        self.render(c, options)
        self.assertGreater(c.img[55,80].mean() - original[55,80].mean(), .07)
        self.assertLess(c.img[30,130].mean(), original[30,130].mean() * .8)
        np.testing.assert_array_equal(c.img[15,15], original[15,15])
        self.assertLessEqual(c.img.max(), 1)
        self.assertTrue(np.isfinite(c.img).all())

    def test_wall_lights_add_local_colour_and_keep_face_and_display_neutral(self):
        import numpy as np
        cfg = {'look':'wall-accents','preset':'adaptive-studio'}
        centers = {'blue':[.16,.30],'red':[.82,.30]}
        regions = [[[.76,.38],[.94,.38],[.94,.55],[.76,.55]]]
        project = {'lighting':cfg,'lighting_calibration':{'accent_centers':centers}}
        opts = shot_lighting(project, {'lighting_calibration':{'screen_regions':regions}})
        c = self.fixture(85,105,185)[0]
        original = c.img.copy()
        self.render(c, opts)
        self.assertGreater(c.img[36,26,2], c.img[36,26,0] + .12)
        self.assertGreater(c.img[36,131,0], c.img[36,131,2] + .12)
        np.testing.assert_array_equal(c.img[53,134], original[53,134])
        np.testing.assert_allclose(c.img[60,80], c.img[60,80,0])
        with self.assertRaises(ValueError):
            validate_lighting({**cfg, 'accent_centers':{'red':[-1,1]}})
        self.assertIsNone(shot_lighting({'lighting':None}, {}))

    def test_fills_either_darker_cheek_preserving_direction(self):
        for values in [(45, 145), (145, 45)]:
            c, _, _, _ = self.fixture(*values, 110)
            before = c.img.copy()
            self.render(c)
            dark, bright = (65, 95) if values[0] < values[1] else (95, 65)
            relative_gain = c.img / before.clip(.001)
            self.assertGreater(relative_gain[60,dark,0], relative_gain[60,bright,0])
            self.assertLess(c.img[60,dark,0], c.img[60,bright,0])

    def test_balanced_face_and_unconfirmed_detection(self):
        import numpy as np
        c, analysis, rgb, mask = self.fixture(135,135,145)
        before = c.img.copy()
        self.render(c)
        np.testing.assert_array_equal(c.img, before)
        self.assertIsNone(analysis.measure(rgb, mask, None))
        self.assertIsNone(analysis.measure(rgb, mask * 0, (80,55,60)))
        c.adaptive = None
        self.render(c)
        np.testing.assert_array_equal(c.img, before)

    def test_cut_resets_history_and_small_motion_is_smoothed(self):
        import numpy as np
        c, a, rgb, mask = self.fixture(40, 120, 180)
        initial = c.adaptive
        center = (80,55,60)
        changed = rgb.copy()
        changed[30:,45:80] += 20
        self.assertFalse(a.start_frame(changed))
        result = a.measure(changed, mask, center)
        fresh = self.fixture(60,120,180)[0].adaptive
        self.assertLess(abs(initial[4] - result[4]), abs(initial[4] - fresh[4]))
        cut = self.fixture(60,120,40)
        self.assertTrue(a.start_frame(cut[2]))
        np.testing.assert_allclose(a.measure(cut[2], mask, center), cut[0].adaptive)


if __name__ == '__main__': unittest.main()
