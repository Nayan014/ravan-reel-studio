"""Portable lighting, ordering, geometry and non-presenter regression checks."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/effects/scripts'))
from studio_lighting import validate_lighting, expand_lighting


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


if __name__ == '__main__': unittest.main()
