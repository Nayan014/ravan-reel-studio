"""Optional, local studio lighting for photographic footage before graphics.

Configuration helpers use only the standard library; rendering uses the
effects environment's existing NumPy/OpenCV and tracked person/face context.
"""
import math


def validate_lighting(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {'preset', 'screen_regions', 'look', 'accent_centers'}:
        raise ValueError('Lighting must contain preset and optional look or screen_regions.')
    if value.get('preset') not in ('natural-studio', 'adaptive-studio'):
        raise ValueError('Choose natural-studio or adaptive-studio, or null for no lighting.')
    result = {'preset': value['preset']}
    if 'look' in value:
        if result['preset'] != 'adaptive-studio' or value['look'] not in ('softbox', 'wall-accents'):
            raise ValueError('The softbox and wall-accents looks require the adaptive-studio preset.')
        result['look'] = value['look']
    if 'accent_centers' in value:
        centers = value['accent_centers']
        if (result.get('look') != 'wall-accents' or not isinstance(centers, dict)
                or set(centers) != {'blue', 'red'} or not all(
                    isinstance(point, (tuple, list)) and len(point) == 2 and all(
                        type(n) in (float, int) and math.isfinite(n) and 0 <= n <= 1 for n in point)
                    for point in centers.values())):
            raise ValueError('Wall accent centers need a normalized [x,y] for both blue and red.')
        result['accent_centers'] = {name: list(point) for name, point in centers.items()}
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


def shot_lighting(plan, shot):
    """Resolve a shot override and its camera-specific wall/screen geometry."""
    config = shot.get('lighting', plan.get('lighting'))
    if config is None:
        return None
    config = validate_lighting(config)
    calibration = dict(plan.get('lighting_calibration', {}))
    calibration.update({k: config[k] for k in ('screen_regions', 'accent_centers') if k in config})
    calibration.update(shot.get('lighting_calibration', {}))
    if 'screen_regions' in calibration:
        config['screen_regions'] = calibration['screen_regions']
    if config.get('look') == 'wall-accents' and 'accent_centers' in calibration:
        config['accent_centers'] = calibration['accent_centers']
    return validate_lighting(config)


def lighting_effect(value, end):
    config = validate_lighting(value)
    if config is None:
        return None
    if config['preset'] == 'natural-studio':
        del config['preset']  # The original direct effect defaults to this look.
    return {'fx': 'studio-light', 'start': 0, 'end': end, **config}


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


class AdaptiveAnalysis:
    """Pass-one measurements in tracking coordinates, independently indexed for stills."""
    def __init__(self, fps):
        self.exposure_alpha = 1 - math.exp(-1 / (fps * .40))
        self.position_alpha = 1 - math.exp(-1 / (fps * .065))
        self.previous_scene = None
        self.estimate = None
        self.position = None

    def start_frame(self, rgb):
        import cv2
        import numpy as np

        # Block averages avoid declaring a cut on sensor noise or small hand motion.
        scene = cv2.resize(rgb, (12, 8), interpolation=cv2.INTER_AREA).astype(np.float32)
        cut = self.previous_scene is None or np.mean(np.abs(scene - self.previous_scene)) > 32
        self.previous_scene = scene
        if cut:
            self.estimate = self.position = None
        return cut

    def measure(self, rgb, mask, detection):
        import numpy as np

        if detection is None:
            self.position = self.estimate = None
            return None
        x, y, width = detection
        # Sample central cheek patches. Ignore silhouette fallbacks, facial edges and room pixels.
        h, w = mask.shape
        left, right = max(0, int(x - .34 * width)), min(w, int(x + .34 * width))
        top, bottom = max(0, int(y)), min(h, int(y + .23 * width))
        patch = rgb[top:bottom, left:right]
        person = mask[top:bottom, left:right] > 210
        cols = np.arange(left, right) - x
        cheeks = []
        for side in (-1, 1):
            pixels = patch[person & (side * cols > .08 * width)]
            if len(pixels) < 8:
                self.position = self.estimate = None
                return None
            cheeks.append(float(np.median(pixels @ [.2126, .7152, .0722])) / 255)
        small = rgb[::8, ::8]
        room = small[mask[::8, ::8] < 32]
        face = sum(cheeks) / 2
        ambient = float(np.percentile(room @ [.2126, .7152, .0722], 70)) / 255 if len(room) >= 12 else face
        contrast = max(0, ambient - face - .12)
        key = np.clip((.40 - face) * 2.3 + contrast * .95, 0, .88)
        room_dim = np.clip(contrast * .72, 0, .32)
        difference = cheeks[1] - cheeks[0]
        fill = math.copysign(min(.48, max(0, abs(difference) - .035) * 2.2), difference)
        target = np.array([key, fill, room_dim])
        position = np.array(detection, dtype=float)
        if self.estimate is None:
            self.estimate, self.position = target, position
        else:
            self.estimate += self.exposure_alpha * (target - self.estimate)
            self.position += self.position_alpha * (position - self.position)
        return (*self.position, *self.estimate)


def render_adaptive(c, e, grid):
    import cv2
    import numpy as np

    if c.adaptive is None:
        return
    x, y, width, key, fill, room_dim = c.adaptive
    accents = e.o.get('look') == 'wall-accents'
    softbox = accents or e.o.get('look') == 'softbox'
    if not softbox and max(key, abs(fill), room_dim) < .005:
        return
    xx, yy = grid(c)
    dx, dy = (xx - x) / width, (yy - y) / width
    face = np.exp(-.5 * ((dx / .54) ** 2 + (dy / .76) ** 2))
    darker_side = np.clip(.5 - np.sign(fill) * dx * 1.8, 0, 1)
    # Feather uncertainty around moving hair and hands using the soft person mask.
    subject = np.clip((c.m - .12) / .76, 0, 1)
    subject *= subject * (3 - 2 * subject)
    if softbox:
        # An elevated, broad key on the existing lit cheek. Blend direction
        # continuously through ambiguous readings so the key never flips sides.
        direction = np.clip(fill / .12, -1, 1)
        key_shape = np.exp(-.5 * (((dx - .31 * direction) / .64) ** 2 + ((dy + .19) / .86) ** 2))
        subject_stops = (.98 + .85 * key) * key_shape + .23 * face - .10
        # Keep the pool of background light stationary, as a real fixture would be.
        if 'room_falloff' not in e.state:
            e.state['room_falloff'] = np.exp(-.5 * (((xx / c.W - .16) / .34) ** 2
                                                  + ((yy / c.H - .49) / .33) ** 2))
        pool = e.state['room_falloff']
        stops = subject_stops * subject - (1.70 + room_dim - .62 * pool) * (1 - subject)
    else:
        stops = face * subject * (key + abs(fill) * darker_side) - room_dim * (1 - subject)
    peak = c.img.max(axis=2)
    # Roll off the adjustment towards speculars and deep blacks. Apply one RGB
    # multiplier to retain channel ratios and texture in the recorded image.
    highlight_guard = np.clip((.94 - peak) / .22, 0, 1)
    if softbox:
        # Limit added light on skin and white clothing, while still bringing
        # bright walls down to the room exposure.
        highlight_guard = 1 - subject * (1 - highlight_guard)
    stops *= highlight_guard * np.clip(peak / .12, 0, 1)
    room_weight = 1 - subject
    if e.o.get('screen_regions'):
        if 'screen_mask' not in e.state:
            screen = np.zeros((c.H, c.W), np.float32)
            for polygon in e.o['screen_regions']:
                points = np.rint(np.array(polygon) * [c.W - 1, c.H - 1]).astype(np.int32)
                cv2.fillPoly(screen, [points], 1)
            e.state['screen_mask'] = cv2.GaussianBlur(screen, (0, 0), max(.6, c.W * .002))
        protection = e.state['screen_mask'] * (1 - subject)
        stops *= 1 - protection
        room_weight *= 1 - e.state['screen_mask']
    gain = np.minimum(np.exp2(stops / 2.2), 1 + .85 * (1 - peak))
    c.img *= gain[..., None]
    if accents:
        # Wall-mounted practicals stay in camera coordinates as the presenter moves.
        # Scale the radius in physical pixels so landscape and portrait pools stay soft.
        if 'accent_pools' not in e.state:
            centers = e.o.get('accent_centers', {'blue': [.17, .44], 'red': [.84, .35]})
            short = min(c.W, c.H)
            def wall_pool(center, height):
                x, y = center
                return np.exp(-.5 * (((xx - x*c.W) / (.34*short))**2
                                    + ((yy - y*c.H) / (height*short))**2))
            e.state['accent_pools'] = wall_pool(centers['blue'], .23), wall_pool(centers['red'], .18)
        blue, red = (p * room_weight for p in e.state['accent_pools'])
        # Modulate the recorded wall colour; displayed content, skin and clothing
        # receive no coloured light inside their protected masks.
        for channel, (b, r) in enumerate(((-.55, .86), (-.18, -.44), (.98, -.38))):
            pixels = c.img[..., channel]
            change = blue*b + red*r
            pixels += pixels * change * np.where(change > 0, 1 - pixels, 1)
    elif softbox:
        # A restrained cool bounce on the wall beside the neutral face key.
        c.img[..., 0] *= 1 - .19 * room_weight * pool
        c.img[..., 2] *= 1 + .21 * room_weight * pool
