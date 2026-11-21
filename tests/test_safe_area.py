import unittest
from scripts.safe_area import (
    get_safe_area,
    caption_bounds,
    headline_bounds,
    validate_box,
    clamp_box,
    validate_text_layers,
    PLATFORM_SPECS,
)


class TestSafeArea(unittest.TestCase):

    def test_universal_safe_area_dimensions(self):
        sa = get_safe_area('universal', 1080, 1920)
        self.assertEqual(sa['platform'], 'universal')
        self.assertEqual(sa['top_margin'], 290)
        self.assertEqual(sa['bottom_margin'], 440)
        self.assertEqual(sa['left_margin'], 70)
        self.assertEqual(sa['right_margin'], 160)
        self.assertEqual(sa['safe_width'], 850)
        self.assertEqual(sa['safe_height'], 1190)
        self.assertEqual(sa['safe_x_max'], 920)
        self.assertEqual(sa['safe_y_max'], 1480)

    def test_platform_presets(self):
        ig = get_safe_area('instagram', 1080, 1920)
        self.assertEqual(ig['top_margin'], 220)
        self.assertEqual(ig['bottom_margin'], 380)
        self.assertEqual(ig['right_margin'], 130)

        tt = get_safe_area('tiktok', 1080, 1920)
        self.assertEqual(tt['top_margin'], 240)
        self.assertEqual(tt['bottom_margin'], 440)
        self.assertEqual(tt['right_margin'], 150)

        yt = get_safe_area('youtube_shorts', 1080, 1920)
        self.assertEqual(yt['top_margin'], 280)
        self.assertEqual(yt['bottom_margin'], 400)
        self.assertEqual(yt['right_margin'], 160)

    def test_4k_resolution_scaling(self):
        sa4k = get_safe_area('universal', 2160, 3840)
        self.assertEqual(sa4k['top_margin'], 580)
        self.assertEqual(sa4k['bottom_margin'], 880)
        self.assertEqual(sa4k['left_margin'], 140)
        self.assertEqual(sa4k['right_margin'], 320)
        self.assertEqual(sa4k['safe_width'], 1700)
        self.assertEqual(sa4k['safe_height'], 2380)

    def test_caption_bounds_placement(self):
        cb = caption_bounds('universal', 1080, 1920)
        self.assertEqual(cb['platform'], 'universal')
        self.assertEqual(cb['font_size'], 64)
        self.assertEqual(cb['bottom'], 460)
        # Left margin + buffer
        self.assertEqual(cb['left'], 80)
        # Max width keeps clearance for right rail (160px + 15px = 175px)
        self.assertEqual(cb['right_margin'], 175)
        self.assertEqual(cb['width'], 1080 - 80 - 175)
        self.assertIn("bottom:460px", cb['css'])

    def test_headline_bounds_placement(self):
        hb = headline_bounds('universal', 1080, 1920)
        self.assertEqual(hb['platform'], 'universal')
        self.assertEqual(hb['font_size'], 84)
        self.assertEqual(hb['top'], 300)
        self.assertIn("top:300px", hb['css'])

    def test_box_validation_and_clamping(self):
        # Element violating top restricted zone
        top_box = {'x': 100, 'y': 150, 'width': 600, 'height': 100}
        res = validate_box(top_box, 'universal', 1080, 1920)
        self.assertFalse(res['valid'])
        self.assertTrue(any("Top overflow" in v for v in res['violations']))
        self.assertEqual(res['clamped']['y'], 290)

        # Element violating bottom restricted zone
        bottom_box = {'x': 100, 'y': 1500, 'width': 600, 'height': 100}
        res = validate_box(bottom_box, 'universal', 1080, 1920)
        self.assertFalse(res['valid'])
        self.assertTrue(any("Bottom overflow" in v for v in res['violations']))
        self.assertEqual(res['clamped']['y'], 1480 - 100)

        # Element violating right engagement rail
        right_box = {'x': 850, 'y': 600, 'width': 200, 'height': 100}
        res = validate_box(right_box, 'universal', 1080, 1920)
        self.assertFalse(res['valid'])
        self.assertTrue(any("Right overflow" in v for v in res['violations']))
        self.assertEqual(res['clamped']['x'], 920 - 200)

        # Valid box inside safe area
        valid_box = {'x': 100, 'y': 350, 'width': 600, 'height': 400}
        res = validate_box(valid_box, 'universal', 1080, 1920)
        self.assertTrue(res['valid'])
        self.assertEqual(len(res['violations']), 0)

    def test_text_layers_validation(self):
        layers = [
            {'id': 'layer-1', 'x': 0.1, 'y': 0.2, 'text': 'Safe hook title', 'fontSize': 64},
            {'id': 'layer-2', 'x': 0.85, 'y': 0.5, 'text': 'Overlapping text on right', 'fontSize': 64},
            {'id': 'layer-3', 'x': 0.1, 'y': 0.9, 'text': 'Too close to bottom', 'fontSize': 64},
        ]
        res = validate_text_layers(layers, 'universal', 1080, 1920)
        self.assertFalse(res['valid'])
        self.assertEqual(len(res['layers']), 3)
        self.assertTrue(res['layers'][0]['valid'])
        self.assertFalse(res['layers'][1]['valid'])
        self.assertFalse(res['layers'][2]['valid'])


if __name__ == '__main__':
    unittest.main()
