#!/usr/bin/env python3
"""
build_cover_combinations.py
Generate cover design combinations requested by the user:
- Full-spread tech environment with creator in the foreground (face & body unobstructed).
- Smooth ambient gradient with zero black strap.
- Large, high-impact headline text only (zero small text).
"""

import os
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

CANVAS_W = 1080
CANVAS_H = 1920

FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../effects/fonts'))
FONT_HEAD = os.path.join(FONTS_DIR, 'ArchivoBlack-Regular.ttf')
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../effects/models/selfie_segmenter.tflite'))

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_text_with_shadow(draw, pos, text, font, fill=(255, 255, 255)):
    """Draw text with a multi-pass drop shadow for maximum legibility against any background."""
    x, y = pos
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-4, 4), (4, 4), (0, 8), (0, 12)]:
        draw.text((x + ox, y + oy), text, font=font, fill=(0, 0, 0, 215))
    draw.text((x, y), text, font=font, fill=fill)

def render_unified_header(canvas, title_line1="10 YEARS", title_line2="BUILDING MOBILE APPS"):
    """
    Renders large, bold, high-contrast title text at the top with zero small text.
    Uses an ultra-smooth, wide quadratic falloff gradient to avoid any black strap appearance.
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
    
    # Brand tag
    brand_font = get_font(FONT_HEAD, 38)
    draw_text_with_shadow(draw, (72, 90), "TECHNO", brand_font, fill=(255, 255, 255))
    techno_w = draw.textlength("TECHNO", font=brand_font)
    draw_text_with_shadow(draw, (72 + int(techno_w) + 14, 90), "RAVAN", brand_font, fill=(255, 82, 82))
    
    # Headline Line 1: 10 YEARS
    font_l1 = get_font(FONT_HEAD, 108)
    draw_text_with_shadow(draw, (72, 165), title_line1, font_l1, fill=(255, 255, 255))
    
    # Headline Line 2: BUILDING MOBILE APPS
    font_l2 = get_font(FONT_HEAD, 72)
    draw_text_with_shadow(draw, (72, 295), title_line2, font_l2, fill=(255, 184, 0))

def build_full_spread_cover(visual_path, creator_path, output_path):
    """
    Full-spread 3D tech environment spread over the entire image.
    The creator sits in the foreground with 0% occlusion of his face, head, or body.
    The 3D smartphone, UI dashboard, and architecture nodes remain clearly visible beside him.
    Zero small text.
    """
    vis = Image.open(visual_path).convert('RGBA')
    creator = Image.open(creator_path).convert('RGB')
    
    # 1. Seamless Background:
    vis_1080 = vis.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    
    bg = Image.new('RGBA', (CANVAS_W, CANVAS_H), (10, 16, 26, 255))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(CANVAS_H):
        t = y / float(CANVAS_H)
        r = int(7 + 8 * (1.0 - t))
        g = int(12 + 12 * (1.0 - t))
        b = int(22 + 16 * (1.0 - t))
        bg_draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b, 255))
    
    vis_shifted = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    vis_shifted.paste(vis_1080, (110, 0))
    
    # Smooth left-edge feathering to blend seamlessly
    feather_mask = Image.new('L', (CANVAS_W, CANVAS_H), 255)
    fm_draw = ImageDraw.Draw(feather_mask)
    for x in range(320):
        a = int(255 * (x / 320.0) ** 1.5)
        fm_draw.line([(x, 0), (x, CANVAS_H)], fill=a)
    bg.paste(vis_shifted, (0, 0), feather_mask)
    
    # Composite the glowing nodes on the left side
    left_nodes = vis_1080.crop((0, int(CANVAS_H * 0.25), 350, int(CANVAS_H * 0.75)))
    left_mask = Image.new('L', left_nodes.size, 180)
    lm_draw = ImageDraw.Draw(left_mask)
    for x in range(left_nodes.size[0]):
        a = int(180 * (1.0 - x / float(left_nodes.size[0])))
        lm_draw.line([(x, 0), (x, left_nodes.size[1])], fill=a)
    bg.paste(left_nodes, (0, int(CANVAS_H * 0.25)), left_mask)
    
    # 2. Extract Creator via Selfie Segmentation
    creator_1080 = creator.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    options = vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE,
        output_confidence_masks=True
    )
    segmenter = vision.ImageSegmenter.create_from_options(options)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(creator_1080))
    res = segmenter.segment(mp_img)
    mask_np = res.confidence_masks[0].numpy_view().squeeze()
    mask_smooth = np.clip((mask_np - 0.20) / 0.60, 0, 1)
    mask_img = Image.fromarray((mask_smooth * 255).astype(np.uint8), mode='L')
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
    
    # Position Nayan shifted slightly left so his head/face is completely clear of the 3D phone
    nayan_x = -110
    nayan_y = 50
    
    # Ambient Drop Shadow behind Nayan
    shadow = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    s_mask = mask_img.filter(ImageFilter.GaussianBlur(28))
    shadow.paste((0, 0, 0, 170), (nayan_x + 12, nayan_y + 16), s_mask)
    bg.alpha_composite(shadow)
    
    # Ambient Cyber Rim Glow (cyan on right, amber on left)
    rim = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    rim_mask = mask_img.filter(ImageFilter.GaussianBlur(35))
    rim.paste((0, 190, 245, 55), (nayan_x + 35, nayan_y), rim_mask)
    rim.paste((255, 175, 0, 40), (nayan_x - 15, nayan_y), rim_mask)
    bg.alpha_composite(rim)
    
    # Paste Nayan cleanly in foreground
    nayan_layer = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    nayan_layer.paste(creator_1080, (nayan_x, nayan_y), mask_img)
    bg.alpha_composite(nayan_layer)
    
    # 3. Render Header with Smooth Gradient (No black strap)
    render_unified_header(bg)
    
    bg.convert('RGB').save(output_path, 'PNG', quality=95)
    print(f"Generated Full-Spread Cover: {output_path}")

def build_graphic_only(visual_path, output_path):
    """
    Combination 3: Full-bleed 3D mobile architecture graphic with only the bold headline.
    No small text anywhere.
    """
    vis = Image.open(visual_path).convert('RGB')
    vis_resized = vis.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    
    canvas = Image.new('RGBA', (CANVAS_W, CANVAS_H))
    canvas.paste(vis_resized, (0, 0))
    
    render_unified_header(canvas)
    
    canvas.convert('RGB').save(output_path, 'PNG', quality=95)
    print(f"Generated Graphic-Only: {output_path}")

def build_split_half(visual_path, creator_path, output_path):
    """
    Combination 2: 50/50 Split.
    Left half: Creator in his real video.
    Right half: 3D mobile architecture graphic.
    Divider: Sleek subtle glowing vertical neon divider.
    Top: Unified massive bold headline.
    No small text anywhere.
    """
    creator = Image.open(creator_path).convert('RGB')
    cw, ch = creator.size
    
    target_ratio = 540.0 / 1920.0
    crop_w = int(ch * target_ratio)
    x0 = int((cw - crop_w) * 0.45)
    creator_cropped = creator.crop((x0, 0, x0 + crop_w, ch)).resize((540, CANVAS_H), Image.Resampling.LANCZOS)
    
    vis = Image.open(visual_path).convert('RGB')
    vw, vh = vis.size
    crop_vw = int(vh * target_ratio)
    vx0 = int((vw - crop_vw) * 0.52)
    vis_cropped = vis.crop((vx0, 0, vx0 + crop_vw, vh)).resize((540, CANVAS_H), Image.Resampling.LANCZOS)
    
    canvas = Image.new('RGBA', (CANVAS_W, CANVAS_H))
    canvas.paste(creator_cropped, (0, 0))
    canvas.paste(vis_cropped, (540, 0))
    
    divider = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    d_draw = ImageDraw.Draw(divider)
    for i in range(12, 0, -2):
        alpha = int(70 * (1.0 - i / 12.0))
        d_draw.line([(540 - i, 0), (540 - i, CANVAS_H)], fill=(0, 210, 255, alpha))
        d_draw.line([(540 + i, 0), (540 + i, CANVAS_H)], fill=(255, 184, 0, alpha))
    d_draw.line([(539, 0), (539, CANVAS_H)], fill=(0, 230, 255, 230))
    d_draw.line([(540, 0), (540, CANVAS_H)], fill=(255, 255, 255, 255))
    d_draw.line([(541, 0), (541, CANVAS_H)], fill=(255, 190, 0, 230))
    canvas.alpha_composite(divider)
    
    render_unified_header(canvas)
    
    canvas.convert('RGB').save(output_path, 'PNG', quality=95)
    print(f"Generated Split-Half: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--visual', required=True)
    parser.add_argument('--creator', required=True)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()
    
    os.makedirs(args.outdir, exist_ok=True)
    
    out_spread = os.path.join(args.outdir, 'style-combo-in-video.png')
    out_split = os.path.join(args.outdir, 'style-combo-split.png')
    out_graphic = os.path.join(args.outdir, 'style-combo-graphic-only.png')
    
    build_full_spread_cover(args.visual, args.creator, out_spread)
    build_split_half(args.visual, args.creator, out_split)
    build_graphic_only(args.visual, out_graphic)
    print("All combinations generated successfully.")
