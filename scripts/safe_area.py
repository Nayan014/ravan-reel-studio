#!/usr/bin/env python3
"""Platform-specific and universal safe area definitions and validation for vertical reels and videos.

Defines safe zones, margins and restricted areas for Instagram Reels, TikTok,
YouTube Shorts and universal cross-platform deployment on 1080x1920 (portrait 9:16)
as well as resolution-scaled video formats (e.g. 2160x3840 4K).
"""

import argparse
import json
import math
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Base canvas reference for standard vertical short-form video
BASE_WIDTH = 1080
BASE_HEIGHT = 1920

# Platform-specific safe area margins on a 1080x1920 portrait canvas (in pixels)
# Restricted zones:
# - top: navigation, search, camera, tabs, audio tags
# - bottom: captions, account handle, audio ticker, scrub bar, native platform buttons
# - right: vertical engagement action rail (like, comment, share, remix, bookmark, vinyl disc)
# - left: standard comfort margin from screen edge
PLATFORM_SPECS: Dict[str, Dict[str, Any]] = {
    'universal': {
        'name': 'Universal Cross-Platform',
        'description': 'Intersection safe zone guaranteed to be clear of UI on Instagram Reels, TikTok, and YouTube Shorts.',
        'top': 290,
        'bottom': 440,
        'left': 70,
        'right': 160,
        'profile_grid_safe': True,  # Fits within Instagram 1:1 center crop (420px to 1500px)
        'caption_anchor': 'bottom',
        'caption_bottom_margin': 460,
        'caption_max_width_pct': 0.76,
        'headline_top_margin': 300,
    },
    'instagram': {
        'name': 'Instagram Reels',
        'description': 'Optimized for Instagram Reels UI (audio pill on top, profile + handle bottom, action rail right).',
        'top': 220,
        'bottom': 380,
        'left': 60,
        'right': 130,
        'profile_grid': {'top': 420, 'bottom': 420, 'height': 1080},
        'caption_anchor': 'bottom',
        'caption_bottom_margin': 400,
        'caption_max_width_pct': 0.80,
        'headline_top_margin': 240,
    },
    'tiktok': {
        'name': 'TikTok',
        'description': 'Optimized for TikTok UI (Following/For You top, heavy multi-line caption & sound bottom, wide right action stack).',
        'top': 240,
        'bottom': 440,
        'left': 60,
        'right': 150,
        'caption_anchor': 'bottom',
        'caption_bottom_margin': 460,
        'caption_max_width_pct': 0.78,
        'headline_top_margin': 260,
    },
    'youtube_shorts': {
        'name': 'YouTube Shorts',
        'description': 'Optimized for YouTube Shorts UI (search & camera top, subscribe button & sound pill bottom, action column right).',
        'top': 280,
        'bottom': 400,
        'left': 60,
        'right': 160,
        'caption_anchor': 'bottom',
        'caption_bottom_margin': 420,
        'caption_max_width_pct': 0.77,
        'headline_top_margin': 300,
    },
    # Also support landscape 16:9 for YouTube videos
    'youtube_landscape': {
        'name': 'YouTube Landscape (16:9)',
        'description': 'Safe area for standard 16:9 widescreen YouTube videos (avoiding player controls and end screens).',
        'top': 80,
        'bottom': 120,
        'left': 100,
        'right': 100,
        'caption_anchor': 'bottom',
        'caption_bottom_margin': 140,
        'caption_max_width_pct': 0.80,
        'headline_top_margin': 100,
    }
}


def normalize_platform_key(platform: Optional[str]) -> str:
    """Normalize user or config platform string to canonical key."""
    if not platform:
        return 'universal'
    p = str(platform).lower().strip().replace(' ', '_').replace('-', '_')
    if p in ('ig', 'instagram', 'reels', 'instagram_reels'):
        return 'instagram'
    if p in ('tt', 'tiktok'):
        return 'tiktok'
    if p in ('yt', 'shorts', 'youtube_shorts', 'youtube_short', 'yt_shorts'):
        return 'youtube_shorts'
    if p in ('youtube', 'landscape', 'youtube_landscape', 'widescreen'):
        return 'youtube_landscape'
    return 'universal'


def get_safe_area(platform: str = 'universal', width: int = BASE_WIDTH, height: int = BASE_HEIGHT) -> Dict[str, Any]:
    """Calculate absolute pixel bounds and normalized ratios for the target platform and canvas dimensions."""
    key = normalize_platform_key(platform)
    spec = PLATFORM_SPECS.get(key, PLATFORM_SPECS['universal'])

    # Determine scaling factors relative to base canvas
    landscape = width > height
    if landscape and key != 'youtube_landscape':
        spec = PLATFORM_SPECS['youtube_landscape']
        base_w, base_h = 1920, 1080
    else:
        base_w, base_h = BASE_WIDTH, BASE_HEIGHT

    scale_x = width / base_w
    scale_y = height / base_h

    top_px = round(spec['top'] * scale_y)
    bottom_px = round(spec['bottom'] * scale_y)
    left_px = round(spec['left'] * scale_x)
    right_px = round(spec['right'] * scale_x)

    safe_x = left_px
    safe_y = top_px
    safe_width = max(1, width - left_px - right_px)
    safe_height = max(1, height - top_px - bottom_px)
    safe_x_max = width - right_px
    safe_y_max = height - bottom_px

    return {
        'platform': key,
        'platform_name': spec['name'],
        'description': spec['description'],
        'width': width,
        'height': height,
        'landscape': landscape,
        # Pixel margins
        'top_margin': top_px,
        'bottom_margin': bottom_px,
        'left_margin': left_px,
        'right_margin': right_px,
        # Usable bounding box
        'safe_x': safe_x,
        'safe_y': safe_y,
        'safe_width': safe_width,
        'safe_height': safe_height,
        'safe_x_max': safe_x_max,
        'safe_y_max': safe_y_max,
        # Normalized ratios (0.0 to 1.0)
        'normalized': {
            'x_min': round(safe_x / width, 4),
            'y_min': round(safe_y / height, 4),
            'x_max': round(safe_x_max / width, 4),
            'y_max': round(safe_y_max / height, 4),
            'width': round(safe_width / width, 4),
            'height': round(safe_height / height, 4),
            'top': round(top_px / height, 4),
            'bottom': round(bottom_px / height, 4),
            'left': round(left_px / width, 4),
            'right': round(right_px / width, 4),
        },
        # Profile grid safe zone for Instagram (center 1:1)
        'profile_grid': {
            'y_min': round(420 * scale_y),
            'y_max': round(1500 * scale_y),
            'height': round(1080 * scale_y),
        } if not landscape else None
    }


def caption_bounds(platform: str = 'universal', width: int = BASE_WIDTH, height: int = BASE_HEIGHT) -> Dict[str, Any]:
    """Calculate safe container positioning and typography bounds for spoken captions.

    Captions are anchored to the bottom of the safe area so multi-line text expands
    upwards away from the bottom UI instead of overlapping native platform captions.
    Horizontal width is restricted to clear the right engagement rail.
    """
    key = normalize_platform_key(platform)
    spec = PLATFORM_SPECS.get(key, PLATFORM_SPECS['universal'])
    scale_x = width / BASE_WIDTH
    scale_y = height / BASE_HEIGHT
    scale_font = min(width, height) / 1080

    landscape = width > height
    if landscape:
        font_size = round(48 * scale_font)
        left = round(width * 0.10)
        max_w = round(width * 0.80)
        bottom = round(140 * (height / 1080))
    else:
        font_size = round(64 * scale_font)
        # Left margin + comfort buffer
        left = round(spec['left'] * scale_x + 10 * scale_x)
        # Clear the right rail (like, comments, share buttons)
        right_rail_clearance = round(spec['right'] * scale_x + 15 * scale_x)
        max_w = round(width - left - right_rail_clearance)
        # Distance from bottom of canvas to caption baseline/bottom
        bottom = round(spec['caption_bottom_margin'] * scale_y)

    return {
        'platform': key,
        'font_size': font_size,
        'bottom': bottom,
        'left': left,
        'width': max_w,
        'right_margin': width - left - max_w,
        'line_height': 1.15,
        'max_lines': 3,
        'stroke_width': max(2, round(2 * scale_font)),
        'shadow_blur': round(6 * scale_font),
        'css': (
            f"position:absolute;bottom:{bottom}px;left:{left}px;width:{max_w}px;"
            f"font-size:{font_size}px;font-weight:800;line-height:1.15;"
            f"text-align:center;text-wrap:balance;"
        )
    }


def headline_bounds(platform: str = 'universal', width: int = BASE_WIDTH, height: int = BASE_HEIGHT) -> Dict[str, Any]:
    """Calculate safe container positioning for top hooks and scene headlines."""
    key = normalize_platform_key(platform)
    spec = PLATFORM_SPECS.get(key, PLATFORM_SPECS['universal'])
    scale_x = width / BASE_WIDTH
    scale_y = height / BASE_HEIGHT
    scale_font = min(width, height) / 1080

    landscape = width > height
    if landscape:
        font_size = round(72 * scale_font)
        top = round(100 * (height / 1080))
        left = round(width * 0.10)
        max_w = round(width * 0.80)
    else:
        font_size = round(84 * scale_font)
        top = round(spec['headline_top_margin'] * scale_y)
        left = round(spec['left'] * scale_x + 10 * scale_x)
        right_clearance = round(spec['right'] * scale_x + 15 * scale_x)
        max_w = round(width - left - right_clearance)

    return {
        'platform': key,
        'font_size': font_size,
        'top': top,
        'left': left,
        'width': max_w,
        'css': (
            f"position:absolute;top:{top}px;left:{left}px;width:{max_w}px;"
            f"font-size:{font_size}px;font-weight:800;line-height:1.1;"
            f"text-align:center;text-wrap:balance;"
        )
    }


def validate_box(
    box: Dict[str, Union[int, float]],
    platform: str = 'universal',
    width: int = BASE_WIDTH,
    height: int = BASE_HEIGHT,
    normalized: bool = False
) -> Dict[str, Any]:
    """Validate whether a rectangular bounding box lies completely within the safe area.

    box: dictionary containing 'x', 'y', 'width' (or 'w'), 'height' (or 'h').
    normalized: if True, box coordinates are in 0.0 to 1.0 range.
    """
    safe = get_safe_area(platform, width, height)

    bx = float(box.get('x', 0))
    by = float(box.get('y', 0))
    bw = float(box.get('width', box.get('w', 0)))
    bh = float(box.get('height', box.get('h', 0)))

    if normalized:
        bx *= width
        by *= height
        bw *= width
        bh *= height

    violations: List[str] = []
    overlap_area = 0.0
    total_area = max(1.0, bw * bh)

    # Check top boundary
    if by < safe['safe_y']:
        violations.append(f"Top overflow: {safe['safe_y'] - by:.1f}px into top header zone")
        clip_h = min(bh, safe['safe_y'] - by)
        overlap_area += bw * clip_h

    # Check bottom boundary
    if by + bh > safe['safe_y_max']:
        violations.append(f"Bottom overflow: {(by + bh) - safe['safe_y_max']:.1f}px into bottom UI/caption zone")
        clip_h = min(bh, (by + bh) - safe['safe_y_max'])
        overlap_area += bw * clip_h

    # Check left boundary
    if bx < safe['safe_x']:
        violations.append(f"Left overflow: {safe['safe_x'] - bx:.1f}px past left safe margin")
        clip_w = min(bw, safe['safe_x'] - bx)
        overlap_area += clip_w * bh

    # Check right boundary (action rail)
    if bx + bw > safe['safe_x_max']:
        violations.append(f"Right overflow: {(bx + bw) - safe['safe_x_max']:.1f}px into right engagement rail")
        clip_w = min(bw, (bx + bw) - safe['safe_x_max'])
        overlap_area += clip_w * bh

    # Clamped safe coordinates
    clamped_x = max(safe['safe_x'], min(bx, safe['safe_x_max'] - bw))
    clamped_y = max(safe['safe_y'], min(by, safe['safe_y_max'] - bh))
    clamped_w = min(bw, safe['safe_width'])
    clamped_h = min(bh, safe['safe_height'])

    return {
        'valid': len(violations) == 0,
        'platform': safe['platform'],
        'violations': violations,
        'overlap_pct': min(100.0, round((overlap_area / total_area) * 100, 1)),
        'clamped': {
            'x': round(clamped_x, 1),
            'y': round(clamped_y, 1),
            'width': round(clamped_w, 1),
            'height': round(clamped_h, 1),
        }
    }


def clamp_box(
    box: Dict[str, Union[int, float]],
    platform: str = 'universal',
    width: int = BASE_WIDTH,
    height: int = BASE_HEIGHT,
    normalized: bool = False
) -> Dict[str, float]:
    """Clamp a box so it strictly fits inside the safe area."""
    res = validate_box(box, platform, width, height, normalized)
    clamped = res['clamped']
    if normalized:
        return {
            'x': round(clamped['x'] / width, 4),
            'y': round(clamped['y'] / height, 4),
            'width': round(clamped['width'] / width, 4),
            'height': round(clamped['height'] / height, 4),
        }
    return clamped


def validate_text_layers(
    layers: List[Dict[str, Any]],
    platform: str = 'universal',
    width: int = BASE_WIDTH,
    height: int = BASE_HEIGHT
) -> Dict[str, Any]:
    """Validate all text layers against platform safe zones."""
    results = []
    all_valid = True
    safe = get_safe_area(platform, width, height)

    for layer in layers:
        font_size = layer.get('fontSize', 60)
        # Normalized x and y
        nx = float(layer.get('x', 0.1))
        ny = float(layer.get('y', 0.1))
        text = str(layer.get('text', ''))
        lines = text.split('\n')
        # Approximate bounding box
        line_count = len(lines)
        longest_line = max(len(l) for l in lines) if lines else 0
        approx_w = min(width * (1.0 - nx), longest_line * (font_size * 0.55))
        approx_h = line_count * (font_size * 1.2)

        box = {
            'x': nx * width,
            'y': ny * height,
            'width': approx_w,
            'height': approx_h
        }
        val = validate_box(box, platform, width, height)
        if not val['valid']:
            all_valid = False
        results.append({
            'id': layer.get('id', 'unknown'),
            'valid': val['valid'],
            'violations': val['violations'],
            'clamped_x': round(val['clamped']['x'] / width, 4),
            'clamped_y': round(val['clamped']['y'] / height, 4),
        })

    return {
        'valid': all_valid,
        'platform': safe['platform'],
        'layers': results
    }


def main():
    parser = argparse.ArgumentParser(description="Query and validate safe areas for vertical reels.")
    parser.add_argument('--platform', choices=['universal', 'instagram', 'tiktok', 'youtube_shorts', 'youtube_landscape'], default='universal')
    parser.add_argument('--width', type=int, default=BASE_WIDTH)
    parser.add_argument('--height', type=int, default=BASE_HEIGHT)
    parser.add_argument('--caption', action='store_true', help="Print safe caption configuration")
    parser.add_argument('--headline', action='store_true', help="Print safe headline configuration")
    parser.add_argument('--validate-box', type=str, help="Validate JSON box: '{\"x\":100,\"y\":100,\"w\":500,\"h\":200}'")
    args = parser.parse_args()

    if args.caption:
        print(json.dumps(caption_bounds(args.platform, args.width, args.height), indent=2))
        return

    if args.headline:
        print(json.dumps(headline_bounds(args.platform, args.width, args.height), indent=2))
        return

    if args.validate_box:
        box = json.loads(args.validate_box)
        print(json.dumps(validate_box(box, args.platform, args.width, args.height), indent=2))
        return

    print(json.dumps(get_safe_area(args.platform, args.width, args.height), indent=2))


if __name__ == '__main__':
    main()
