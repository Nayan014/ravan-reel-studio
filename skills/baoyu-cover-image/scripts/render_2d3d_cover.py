#!/usr/bin/env python3
"""
render_2d3d_cover.py
Production cover generator for Techno Ravan.

Features:
1. Full-bleed topic-driven visual (relevant 3D graphic, illustration, or scene).
2. 2D-3D Pop-Out Avatar at the bottom:
   - Creator photo cleanly segmented with local selfie segmenter.
   - Head and hair realistically break out over the top rim into 3D space.
   - Shoulders and torso stay inside the circular frame.
   - Preserves 100% natural aspect ratio with zero facial distortion.
3. Smooth ambient gradient at top (zero black strap).
4. Large, bold, high-contrast headline text (zero small text).
"""

import os
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

CANVAS_W = 1080
CANVAS_H = 1920

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
EFFECTS_DIR = os.path.join(ROOT_DIR, 'skills/effects')
FONTS_DIR = os.path.join(EFFECTS_DIR, 'fonts')
MODEL_PATH = os.path.join(EFFECTS_DIR, 'models/selfie_segmenter.tflite')
FONT_HEAD = os.path.join(FONTS_DIR, 'ArchivoBlack-Regular.ttf')

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_text_with_shadow(draw, pos, text, font, fill=(255, 255, 255)):
    x, y = pos
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-4, 4), (4, 4), (0, 8), (0, 12)]:
        draw.text((x + ox, y + oy), text, font=font, fill=(0, 0, 0, 215))
    draw.text((x, y), text, font=font, fill=fill)

def render_top_header(canvas, line1, line2, brand="TECHNO RAVAN"):
    """
    Renders top headline with smooth ambient gradient and zero small text.
    """
    grad = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad)
    grad_h = 680
    for y in range(grad_h):
        t = y / float(grad_h)
        alpha = int(195 * ((1.0 - t) ** 2.2))
        g_draw.line([(0, y), (CANVAS_W, y)], fill=(8, 12, 20, alpha))
    canvas.alpha_composite(grad)
    
    draw = ImageDraw.Draw(canvas, 'RGBA')
    brand_font = get_font(FONT_HEAD, 38)
    
    parts = brand.split(' ', 1)
    b1 = parts[0]
    b2 = parts[1] if len(parts) > 1 else ""
    
    draw_text_with_shadow(draw, (72, 90), b1, brand_font, fill=(255, 255, 255))
    advance = draw.textlength(b1, font=brand_font)
    if b2:
        draw_text_with_shadow(draw, (72 + int(advance) + 14, 90), b2, brand_font, fill=(255, 82, 82))
        
    font_l1 = get_font(FONT_HEAD, 108)
    draw_text_with_shadow(draw, (72, 165), line1, font_l1, fill=(255, 255, 255))
    
    if line2:
        font_l2 = get_font(FONT_HEAD, 72)
        draw_text_with_shadow(draw, (72, 295), line2, font_l2, fill=(255, 184, 0))

def extract_person_mask(creator_img):
    """
    Runs local selfie segmenter on creator image to get clean alpha mask.
    """
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
    
    options = vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE,
        output_confidence_masks=True
    )
    segmenter = vision.ImageSegmenter.create_from_options(options)
    
    rgb_np = np.array(creator_img)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_np)
    res = segmenter.segment(mp_img)
    mask_np = res.confidence_masks[0].numpy_view().squeeze()
    mask_smooth = np.clip((mask_np - 0.20) / 0.60, 0, 1)
    mask_img = Image.fromarray((mask_smooth * 255).astype(np.uint8), mode='L')
    return mask_img

def apply_2d3d_avatar(canvas, creator_path, cx=240, cy=1620, R=210, border_w=9):
    """
    Composites 2D-3D pop-out avatar at (cx, cy) with radius R.
    Head breaks out of the top rim into 3D space, shoulders stay inside.
    """
    creator = Image.open(creator_path).convert('RGB')
    cw, ch = creator.size
    
    # 1. Segment full creator
    mask_img = extract_person_mask(creator)
    
    # 2. Crop centered around head and chest
    # Default assumptions for talking head frames: face is horizontally centered
    crop_x0 = int(cw * 0.16)
    crop_y0 = int(ch * 0.25)
    crop_x1 = int(cw * 0.86)
    crop_y1 = int(ch * 0.72)
    
    person_crop = creator.crop((crop_x0, crop_y0, crop_x1, crop_y1))
    mask_crop = mask_img.crop((crop_x0, crop_y0, crop_x1, crop_y1))
    
    # 3. Scale person so head and shoulders fit circle naturally
    target_person_w = int(R * 2.38) # e.g. 500px for R=210
    target_person_h = int(target_person_w * (person_crop.size[1] / person_crop.size[0]))
    person_scaled = person_crop.resize((target_person_w, target_person_h), Image.Resampling.LANCZOS)
    mask_scaled = mask_crop.resize((target_person_w, target_person_h), Image.Resampling.LANCZOS)
    
    # Position: head pops 120px above top rim
    px = cx - target_person_w // 2
    py = (cy - R) - 120
    
    # 4. Canvas Shadow under circle
    shadow_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    s_draw.ellipse([cx - R - 20, cy - R - 5, cx + R + 20, cy + R + 35], fill=(0, 0, 0, 195))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(30))
    canvas.alpha_composite(shadow_layer)
    
    # 5. Disc Backdrop inside circle
    disc_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    d_draw = ImageDraw.Draw(disc_layer)
    d_draw.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(10, 16, 28, 255))
    d_draw.ellipse([cx - int(R*0.7), cy - int(R*0.7), cx + int(R*0.7), cy + int(R*0.7)], fill=(16, 28, 48, 255))
    disc_layer = disc_layer.filter(ImageFilter.GaussianBlur(8))
    disc_mask = Image.new('L', (CANVAS_W, CANVAS_H), 0)
    dm_draw = ImageDraw.Draw(disc_mask)
    dm_draw.ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    canvas.paste(disc_layer, (0, 0), disc_mask)
    
    # 6. Breakout Mask
    p_w, p_h = person_scaled.size
    mask_np_scaled = np.array(mask_scaled).astype(np.float32) / 255.0
    breakout_mask_np = np.zeros((p_h, p_w), dtype=np.float32)
    head_only_mask_np = np.zeros((p_h, p_w), dtype=np.float32)
    
    for ly in range(p_h):
        gy = py + ly
        dy = gy - cy
        for lx in range(p_w):
            gx = px + lx
            dx = gx - cx
            dist_sq = dx*dx + dy*dy
            in_circle = dist_sq <= (R - 2)**2
            is_upper_head = gy < (cy - int(R * 0.15))
            if in_circle or is_upper_head:
                breakout_mask_np[ly, lx] = mask_np_scaled[ly, lx]
            if is_upper_head and not in_circle:
                head_only_mask_np[ly, lx] = mask_np_scaled[ly, lx]
                
    breakout_mask = Image.fromarray((breakout_mask_np * 255).astype(np.uint8), mode='L')
    breakout_mask = breakout_mask.filter(ImageFilter.GaussianBlur(1))
    
    # 7. Ring Glow & Back Ring
    glow_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)
    g_draw.ellipse([cx - R - 8, cy - R - 8, cx + R + 8, cy + R + 8], outline=(255, 190, 0, 110), width=8)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(glow_layer)
    
    ring_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    r_draw = ImageDraw.Draw(ring_layer)
    for w in range(border_w):
        r_draw.ellipse([cx - R + w, cy - R + w, cx + R - w, cy + R - w], outline=(255, 184, 0, 255))
    canvas.alpha_composite(ring_layer)
    
    # 8. Head Shadow over top rim
    head_shadow = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    hs_mask = Image.fromarray((head_only_mask_np * 255).astype(np.uint8), mode='L').filter(ImageFilter.GaussianBlur(15))
    head_shadow.paste((0, 0, 0, 180), (px, py + 12), hs_mask)
    canvas.alpha_composite(head_shadow)
    
    # 9. Paste Person with Breakout Mask
    person_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    person_layer.paste(person_scaled, (px, py), breakout_mask)
    canvas.alpha_composite(person_layer)
    
    # 10. Front Ring Arc (bottom half over chest)
    front_ring = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    fr_draw = ImageDraw.Draw(front_ring)
    for w in range(border_w):
        fr_draw.arc([cx - R + w, cy - R + w, cx + R - w, cy + R - w], start=-15, end=195, fill=(255, 184, 0, 255))
    canvas.alpha_composite(front_ring)

def render_cover(visual_path, creator_path=None, line1="10 YEARS", line2="BUILDING MOBILE APPS", brand="TECHNO RAVAN", output_path="cover.png"):
    """
    Main entry point to render the complete 2D-3D cover.
    """
    vis = Image.open(visual_path).convert('RGBA')
    canvas = vis.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    
    if creator_path and os.path.exists(creator_path):
        apply_2d3d_avatar(canvas, creator_path, cx=240, cy=1620, R=210, border_w=9)
        
    render_top_header(canvas, line1, line2, brand=brand)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.convert('RGB').save(output_path, 'PNG', quality=95)
    print(f"Cover rendered successfully: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Render 2D-3D pop-out cover for Techno Ravan")
    parser.add_argument('--visual', required=True, help="Path to topic graphic / background")
    parser.add_argument('--creator', default=None, help="Path to creator photo or 4K frame")
    parser.add_argument('--line1', default="10 YEARS", help="Headline line 1")
    parser.add_argument('--line2', default="BUILDING MOBILE APPS", help="Headline line 2")
    parser.add_argument('--brand', default="TECHNO RAVAN", help="Brand text")
    parser.add_argument('--output', default="cover.png", help="Output path")
    args = parser.parse_args()
    
    render_cover(
        visual_path=args.visual,
        creator_path=args.creator,
        line1=args.line1,
        line2=args.line2,
        brand=args.brand,
        output_path=args.output
    )
