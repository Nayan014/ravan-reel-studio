#!/usr/bin/env python3
"""Composite topic visual with brand typography and optional creator badge."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

STUDIO = Path(__file__).resolve().parents[3]
FONTS = STUDIO / 'skills/effects/fonts'

def load_font(name, size, scale=2):
    font_file = FONTS / name
    if not font_file.is_file(): font_file = FONTS / 'Inter.ttf'
    return ImageFont.truetype(str(font_file), round(size * scale))

def create_topic_cover(visual_path, creator_path, output_path, include_creator=True):
    w, h = 1080, 1920
    scale = 2
    sw, sh = w * scale, h * scale

    with Image.open(visual_path) as vimg:
        vimg = ImageOps.exif_transpose(vimg).convert('RGB')
        # Scale to 1080x1920
        c_ratio = sw / sh
        i_ratio = vimg.width / vimg.height
        if i_ratio > c_ratio:
            nh = sh
            nw = round(nh * i_ratio)
        else:
            nw = sw
            nh = round(nw / i_ratio)
        resized = vimg.resize((nw, nh), Image.Resampling.LANCZOS)
        cx = (nw - sw) // 2
        cy = (nh - sh) // 2
        canvas = resized.crop((cx, cy, cx + sw, cy + sh))

    # Top gradient scrim for brand & headline readability
    top_scrim = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(top_scrim)
    scrim_end = round(sh * 0.38)
    for y in range(scrim_end):
        t = 1.0 - (y / scrim_end)
        alpha = int(220 * (t ** 1.3))
        sdraw.line((0, y, sw, y), fill=(8, 10, 16, alpha))

    canvas = Image.alpha_composite(canvas.convert('RGBA'), top_scrim).convert('RGB')
    draw = ImageDraw.Draw(canvas)

    # Brand Header
    bx = round(sw * 0.08)
    by = round(sh * 0.07)
    bf = load_font('SpaceMono-Bold.ttf', 32, scale)
    t_len = draw.textlength('TECHNO', font=bf)
    gap = round(32 * 0.25 * scale)
    draw.text((bx, by), 'TECHNO', font=bf, fill='#FF9933')
    draw.text((bx + t_len + gap, by), 'RAVAN', font=bf, fill='#EF3340')

    # Category Badge
    b_font = load_font('SpaceMono-Bold.ttf', 14, scale)
    badge_text = "MOBILE ARCHITECTURE"
    bw = draw.textlength(badge_text, font=b_font) + 20 * scale
    bh = 30 * scale
    rx = sw - round(sw * 0.08) - bw
    ry = by + 2 * scale
    draw.rounded_rectangle((rx, ry, rx + bw, ry + bh), radius=6 * scale, fill=(0, 0, 0, 180), outline='#F59E0B', width=scale)
    draw.text((rx + 10 * scale, ry + 6 * scale), badge_text, font=b_font, fill='#F59E0B')

    # Headline
    lines = ["10 YEARS", "BUILDING MOBILE APPS"]
    max_w = round(sw * 0.84)
    size = 72
    while size >= 30:
        hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
        if all(draw.textlength(l, font=hfont) <= max_w for l in lines): break
        size -= 2
    hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)

    ty = by + 58 * scale
    for i, line in enumerate(lines):
        color = '#F59E0B' if i == 1 else '#FFFFFF'
        # Drop shadow
        draw.text((bx + 2 * scale, ty + 2 * scale), line, font=hfont, fill=(0, 0, 0, 220))
        draw.text((bx, ty), line, font=hfont, fill=color)
        ty += round(size * 1.15 * scale)

    # Subtitle
    sub_font = load_font('Inter.ttf', 22, scale)
    sub_text = "Lessons, Architecture & Engineering Reality"
    draw.text((bx + scale, ty + 6 * scale + scale), sub_text, font=sub_font, fill=(0, 0, 0, 200))
    draw.text((bx, ty + 6 * scale), sub_text, font=sub_font, fill='#CBD5E1')

    # Optional Creator Inset Badge at bottom corner
    if include_creator and creator_path and Path(creator_path).is_file():
        with Image.open(creator_path) as cimg:
            cimg = ImageOps.exif_transpose(cimg).convert('RGBA')
            card_sz = round(130 * scale)
            c_resized = cimg.resize((card_sz, card_sz), Image.Resampling.LANCZOS)

            # Circular mask
            mask = Image.new('L', (card_sz, card_sz), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse((0, 0, card_sz, card_sz), fill=255)

            pos_x = round(sw * 0.08)
            pos_y = sh - round(sh * 0.11)

            # Outer ring shadow & border
            draw.ellipse((pos_x - 3 * scale, pos_y - 3 * scale, pos_x + card_sz + 3 * scale, pos_y + card_sz + 3 * scale), fill=(15, 23, 42), outline='#F59E0B', width=2 * scale)
            canvas.paste(c_resized, (pos_x, pos_y), mask=mask)

            # Label beside circular avatar
            lbl_font_bold = load_font('Inter.ttf', 16, scale)
            lbl_font_muted = load_font('Inter.ttf', 13, scale)
            tx_c = pos_x + card_sz + 14 * scale
            ty_c = pos_y + 30 * scale

            # Subtle pill behind label
            lbl_w = round(210 * scale)
            lbl_h = round(56 * scale)
            draw.rounded_rectangle((tx_c - 6 * scale, ty_c - 6 * scale, tx_c + lbl_w, ty_c + lbl_h), radius=8 * scale, fill=(15, 23, 42, 220), outline=(51, 65, 85), width=scale)
            draw.text((tx_c, ty_c), "NAYAN V.", font=lbl_font_bold, fill='#FFFFFF')
            draw.text((tx_c, ty_c + 22 * scale), "10+ Years Mobile Dev", font=lbl_font_muted, fill='#94A3B8')

    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((w, h), Image.Resampling.LANCZOS).save(out, quality=95)
    print(f"Rendered: {out}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--visual', required=True)
    parser.add_argument('--creator', default=None)
    parser.add_argument('--output', required=True)
    parser.add_argument('--no-creator', action='store_true')
    args = parser.parse_args()
    create_topic_cover(args.visual, args.creator, args.output, include_creator=not args.no_creator)
