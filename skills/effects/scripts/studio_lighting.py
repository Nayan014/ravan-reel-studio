"""Optional, local studio lighting for photographic footage before graphics.

Configuration helpers use only the standard library; rendering uses the
effects environment's existing NumPy/OpenCV and tracked person/face context.
"""
import math


def validate_lighting(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {'preset', 'screen_regions'}:
        raise ValueError('Lighting must contain preset and optional screen_regions.')
    if value.get('preset') != 'natural-studio':
        raise ValueError('Choose the natural-studio lighting preset, or null for no lighting.')
    result = {'preset': 'natural-studio'}
    if 'screen_regions' in value:
        polygons = value['screen_regions']
        if not isinstance(polygons, list):
            raise ValueError('Lighting screen_regions must be a list of polygons.')
        regions = []
        for polygon in polygons:
            if not isinstance(polygon, list) or len(polygon) < 3:
                raise ValueError('Each lighting screen region needs at least three points.')
            points = []
            for point in polygon:
                if not isinstance(point, (list, tuple)) or len(point) != 2 or not all(
                    type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in point
                ):
                    raise ValueError('Lighting screen points must be normalized x/y values from zero to one.')
                points.append(list(point))
            regions.append(points)
        result['screen_regions'] = regions
    return result


def lighting_effect(value, end):
    config = validate_lighting(value)
    if config is None:
        return None
    return {'fx': 'studio-light', 'start': 0, 'end': end,
            **{key: value for key, value in config.items() if key != 'preset'}}


def expand_lighting(plan):
    """Compile optional plan lighting ahead of existing camera/graphic effects."""
    result = dict(plan)
    effect = lighting_effect(result.pop('lighting', None), 1e9)
    if effect:
        result['effects'] = [effect, *result.get('effects', [])]
    return result


def render_studio_light(c, e, grid, guided):
    import cv2
    import numpy as np

    # No confident person: leave non-presenter footage alone. A workflow may
    # also explicitly disable lighting for a cutaway with lighting: null.
    if np.count_nonzero(c.m > .60) < .01 * c.W * c.H:
        return

    def to_linear(rgb):
        return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)

    def to_srgb(rgb):
        rgb = np.maximum(rgb, 0)
        return np.where(rgb <= .0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - .055)

    radius = max(1, round(c.W * .0028))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    person = cv2.erode(c.m, kernel)
    person = guided(cv2.cvtColor(c.img, cv2.COLOR_RGB2GRAY), person, r=4, eps=.0003)
    person = np.clip((person - .10) / .90, 0, 1) ** 1.6
    xx, yy = grid(c)

    def pool(x, y, rx, ry, tilt=0):
        dx, dy = (xx - x) / rx, (yy - y) / ry
        return np.exp(-.5 * ((dx + tilt * dy) ** 2 + dy ** 2))

    blue = pool(c.W * .08, c.H * .44, c.W * .30, c.H * .22, -.22)
    red = pool(c.W * .96, c.H * .37, c.W * .34, c.H * .24, .30)
    linear = to_linear(c.img)
    room_gain = (np.float32([.065, .067, .075])
                 + blue[..., None] * np.float32([.035, .075, .29])
                 + red[..., None] * np.float32([.27, .032, .046]))
    background = linear * room_gain + .0012

    # No room-specific coordinates are assumed. Optional, inspected polygons
    # preserve emissive display colours and are part of the approved plan.
    regions = e.o.get('screen_regions', [])
    if regions:
        cache_key = ('studio-screens', c.W, c.H)
        if cache_key not in e.state:
            screens = np.zeros((c.H, c.W), np.float32)
            for points in regions:
                polygon = np.array([(round(x * c.W), round(y * c.H)) for x, y in points], np.int32)
                cv2.fillPoly(screens, [polygon], 1.0)
            e.state[cache_key] = cv2.GaussianBlur(screens, (0, 0), c.W * .005)[..., None]
        screens = e.state[cache_key]
        background = background * (1 - screens * .88) + (linear * .25 + .0012) * screens * .88

    key = pool(c.fx - c.fw * .22, c.fy - c.fw * .10, c.fw * .95, c.fw * 1.40)
    subject_gain = (.43 + .51 * key)[..., None]
    blue_spill = pool(c.fx - c.fw * 1.65, c.fy + c.fw * 1.25, c.fw * .62, c.fw * 1.65)
    red_spill = pool(c.fx + c.fw * 1.72, c.fy + c.fw * .75, c.fw * .62, c.fw * 1.55)
    subject_gain = (subject_gain
                    + blue_spill[..., None] * np.float32([.015, .04, .15])
                    + red_spill[..., None] * np.float32([.10, .015, .02]))
    m = person[..., None]
    c.img = to_srgb(linear * subject_gain * m + background * (1 - m))

    # Approved gentle, neutral face lift; retain source texture and shading.
    face = pool(c.fx - .08 * c.fw, c.fy + .08 * c.fw, .70 * c.fw, .88 * c.fw)
    foreground = np.clip((c.m - .60) / .40, 0, 1)
    linear = to_linear(c.img)
    highlight = np.clip((linear.max(axis=2) - .65) / .28, 0, 1)
    gain = 1 + .24 * face * foreground * (1 - highlight)
    c.img = to_srgb(linear * gain[..., None])
