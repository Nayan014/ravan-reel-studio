#!/usr/bin/env python3
"""
Baoyu Cover Image Renderer
Implements distinct, high-CTR cover styles:
  1. cinematic: Full-bleed creator photo with deep filmic scrim and documentary typography
  2. editorial: Restrained warm off-white Swiss magazine layout (Techno Ravan standard)
  3. minimal-dark: Matte slate developer aesthetic with monospace metadata (Vercel/Linear style)
  4. bold-type: Massive high-contrast headline taking primary canvas dominance
Zero external API calls required.
"""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

STUDIO = Path(__file__).resolve().parents[3]
FONTS = STUDIO / 'skills/effects/fonts'


def load_font(name, size, scale=2):
    font_file = FONTS / name
    if not font_file.is_file():
        font_file = FONTS / 'Inter.ttf'
    return ImageFont.truetype(str(font_file), round(size * scale))


def draw_brand_header(draw, x, y, scale=2, font_size=32, techno_color='#FF9933', ravan_color='#EF3340'):
    bf = load_font('SpaceMono-Bold.ttf', font_size, scale)
    gap = round(font_size * 0.25 * scale)
    t_len = draw.textlength('TECHNO', font=bf)
    draw.text((x, y), 'TECHNO', font=bf, fill=techno_color)
    draw.text((x + t_len + gap, y), 'RAVAN', font=bf, fill=ravan_color)
    return y + round(font_size * 1.3 * scale)


# --------------------------------------------------------------------------
# Style 1: Cinematic Full-Bleed
# Full-bleed creator portrait filling the entire 9:16 frame with deep dark
# bottom scrim and bold, crisp documentary typography overlaid.
# --------------------------------------------------------------------------
def render_cinematic(w, h, scale, lines, subtitle, badge, hero_path):
    sw, sh = w * scale, h * scale
    canvas = Image.new('RGB', (sw, sh), (10, 12, 16))

    if hero_path and Path(hero_path).is_file():
        with Image.open(hero_path) as himg:
            himg = ImageOps.exif_transpose(himg).convert('RGB')
            # Fit and cover entire canvas
            c_ratio = sw / sh
            i_ratio = himg.width / himg.height
            if i_ratio > c_ratio:
                nh = sh
                nw = round(nh * i_ratio)
            else:
                nw = sw
                nh = round(nw / i_ratio)
            resized = himg.resize((nw, nh), Image.Resampling.LANCZOS)
            cx = (nw - sw) // 2
            cy = (nh - sh) // 2
            cropped = resized.crop((cx, cy, cx + sw, cy + sh))
            canvas.paste(cropped, (0, 0))

    # Apply cinematic gradient scrim from middle to bottom for text contrast
    scrim = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(scrim)
    scrim_start = round(sh * 0.42)
    for y in range(scrim_start, sh):
        t = (y - scrim_start) / (sh - scrim_start)
        alpha = int(245 * (t ** 1.6))
        sdraw.line((0, y, sw, y), fill=(8, 10, 15, alpha))

    # Top scrim for brand legibility
    top_scrim_end = round(sh * 0.22)
    for y in range(0, top_scrim_end):
        t = 1.0 - (y / top_scrim_end)
        alpha = int(180 * (t ** 1.4))
        sdraw.line((0, y, sw, y), fill=(8, 10, 15, alpha))

    canvas = Image.alpha_composite(canvas.convert('RGBA'), scrim).convert('RGB')
    draw = ImageDraw.Draw(canvas)

    # Brand in upper left
    bx = round(sw * 0.08)
    by = round(sh * 0.07)
    draw_brand_header(draw, bx, by, scale, font_size=32)

    # Topic badge in upper right
    if badge:
        b_font = load_font('SpaceMono-Bold.ttf', 15, scale)
        b_text = str(badge).upper()
        bw = draw.textlength(b_text, font=b_font) + 22 * scale
        bh = 32 * scale
        rx = sw - round(sw * 0.08) - bw
        ry = by + 2 * scale
        draw.rounded_rectangle((rx, ry, rx + bw, ry + bh), radius=6 * scale, fill=(0, 0, 0, 180), outline='#FF9933', width=scale)
        draw.text((rx + 11 * scale, ry + 6 * scale), b_text, font=b_font, fill='#FF9933')

    # Typography at bottom
    max_w = round(sw * 0.84)
    tx = round(sw * 0.08)
    size = 80
    while size >= 32:
        hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
        if all(draw.textlength(l, font=hfont) <= max_w for l in lines):
            break
        size -= 2

    hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
    total_text_h = round(len(lines) * size * 1.15 * scale)
    y_start = sh - total_text_h - round(sh * 0.12)
    if subtitle:
        y_start -= round(44 * scale)

    # Accent color for punchline
    for i, line in enumerate(lines):
        color = '#F59E0B' if (i == len(lines) - 1 and len(lines) > 1) else '#FFFFFF'
        # Drop shadow for readability
        draw.text((tx + 2 * scale, y_start + 2 * scale), line, font=hfont, fill=(0, 0, 0, 200))
        draw.text((tx, y_start), line, font=hfont, fill=color)
        y_start += round(size * 1.15 * scale)

    if subtitle:
        sub_font = load_font('Inter.ttf', 24, scale)
        draw.text((tx + scale, y_start + 8 * scale + scale), str(subtitle), font=sub_font, fill=(0, 0, 0, 180))
        draw.text((tx, y_start + 8 * scale), str(subtitle), font=sub_font, fill='#E2E8F0')

    return canvas


# --------------------------------------------------------------------------
# Style 2: Understated Editorial
# The official Techno Ravan warm off-white magazine aesthetic (#F3EFE7 canvas,
# charcoal typography, clean photo framing, zero neon).
# --------------------------------------------------------------------------
def render_editorial(w, h, scale, lines, subtitle, badge, hero_path):
    sw, sh = w * scale, h * scale
    canvas = Image.new('RGB', (sw, sh), '#F3EFE7')
    draw = ImageDraw.Draw(canvas)

    # Brand
    bx = round(sw * 0.09)
    by = round(sh * 0.08)
    draw_brand_header(draw, bx, by, scale, font_size=32)

    # Subtle topic pill
    if badge:
        b_font = load_font('SpaceMono-Bold.ttf', 14, scale)
        b_text = str(badge).upper()
        bw = draw.textlength(b_text, font=b_font) + 20 * scale
        bh = 28 * scale
        rx = sw - round(sw * 0.09) - bw
        ry = by + 2 * scale
        draw.rounded_rectangle((rx, ry, rx + bw, ry + bh), radius=4 * scale, fill='#E5DFD3')
        draw.text((rx + 10 * scale, ry + 5 * scale), b_text, font=b_font, fill='#55574F')

    # Fine divider rule
    draw.line((bx, by + 48 * scale, sw - bx, by + 48 * scale), fill='#DDD7C9', width=scale)

    # Headline first
    max_w = round(sw * 0.82)
    tx = bx
    ty = by + 68 * scale
    size = 72
    while size >= 28:
        hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
        if all(draw.textlength(l, font=hfont) <= max_w for l in lines):
            break
        size -= 2

    hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
    y_cursor = ty
    for i, line in enumerate(lines):
        color = '#252525'
        draw.text((tx, y_cursor), line, font=hfont, fill=color)
        y_cursor += round(size * 1.16 * scale)

    if subtitle:
        sub_font = load_font('Inter.ttf', 22, scale)
        draw.text((tx, y_cursor + 8 * scale), str(subtitle), font=sub_font, fill='#55574F')
        y_cursor += round(38 * scale)

    # Hero visual in the lower half
    if hero_path and Path(hero_path).is_file():
        with Image.open(hero_path) as himg:
            himg = ImageOps.exif_transpose(himg).convert('RGB')
            card_w = round(sw * 0.82)
            card_y = y_cursor + 28 * scale
            card_h = sh - card_y - round(sh * 0.08)

            c_ratio = card_w / card_h
            i_ratio = himg.width / himg.height
            if i_ratio > c_ratio:
                nh = card_h
                nw = round(nh * i_ratio)
            else:
                nw = card_w
                nh = round(nw / i_ratio)
            resized = himg.resize((nw, nh), Image.Resampling.LANCZOS)
            cx = (nw - card_w) // 2
            cy = (nh - card_h) // 2
            cropped = resized.crop((cx, cy, cx + card_w, cy + card_h))

            # Restrained dark outline
            draw.rectangle(
                (tx - scale, card_y - scale, tx + card_w + scale, card_y + card_h + scale),
                outline='#55574F',
                width=round(1.5 * scale)
            )
            canvas.paste(cropped, (tx, card_y))

    return canvas


# --------------------------------------------------------------------------
# Style 3: Minimal Dark Developer
# Matte deep slate (#0B0F17) with monospace tech metadata and razor-sharp
# typography (Linear / Vercel developer aesthetic).
# --------------------------------------------------------------------------
def render_minimal_dark(w, h, scale, lines, subtitle, badge, hero_path):
    sw, sh = w * scale, h * scale
    canvas = Image.new('RGB', (sw, sh), (11, 15, 23))
    draw = ImageDraw.Draw(canvas)

    bx = round(sw * 0.08)
    by = round(sh * 0.07)
    draw_brand_header(draw, bx, by, scale, font_size=30)

    # Monospace system tag
    sys_font = load_font('SpaceMono-Bold.ttf', 13, scale)
    sys_text = f"SYS // {badge or 'DEV_JOURNEY'}"
    draw.text((sw - round(sw * 0.08) - draw.textlength(sys_text, font=sys_font), by + 8 * scale), sys_text, font=sys_font, fill='#94A3B8')

    # Top hairline
    draw.line((bx, by + 42 * scale, sw - bx, by + 42 * scale), fill=(30, 41, 59), width=scale)

    # Headline
    tx = bx
    ty = by + 64 * scale
    max_w = round(sw * 0.84)
    size = 76
    while size >= 30:
        hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
        if all(draw.textlength(l, font=hfont) <= max_w for l in lines):
            break
        size -= 2

    hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
    y_cursor = ty
    for i, line in enumerate(lines):
        color = '#38BDF8' if (i == len(lines) - 1 and len(lines) > 1) else '#F8FAFC'
        draw.text((tx, y_cursor), line, font=hfont, fill=color)
        y_cursor += round(size * 1.15 * scale)

    if subtitle:
        sub_font = load_font('Inter.ttf', 22, scale)
        draw.text((tx, y_cursor + 6 * scale), str(subtitle), font=sub_font, fill='#94A3B8')
        y_cursor += round(36 * scale)

    # Photo card with subtle cyan border
    if hero_path and Path(hero_path).is_file():
        with Image.open(hero_path) as himg:
            himg = ImageOps.exif_transpose(himg).convert('RGB')
            card_w = round(sw * 0.84)
            card_y = y_cursor + 24 * scale
            card_h = sh - card_y - round(sh * 0.07)

            c_ratio = card_w / card_h
            i_ratio = himg.width / himg.height
            if i_ratio > c_ratio:
                nh = card_h
                nw = round(nh * i_ratio)
            else:
                nw = card_w
                nh = round(nw / i_ratio)
            resized = himg.resize((nw, nh), Image.Resampling.LANCZOS)
            cx = (nw - card_w) // 2
            cy = (nh - card_h) // 2
            cropped = resized.crop((cx, cy, cx + card_w, cy + card_h))

            # Dark border with subtle accent
            draw.rectangle(
                (tx - scale, card_y - scale, tx + card_w + scale, card_y + card_h + scale),
                outline='#38BDF8',
                width=round(1.5 * scale)
            )
            canvas.paste(cropped, (tx, card_y))

    return canvas


# --------------------------------------------------------------------------
# Style 4: Bold Type Dominance
# Giant high-impact numbers and display typography taking center stage,
# with the creator photo smoothly integrated in the lower portion.
# --------------------------------------------------------------------------
def render_bold_type(w, h, scale, lines, subtitle, badge, hero_path):
    sw, sh = w * scale, h * scale
    canvas = Image.new('RGB', (sw, sh), (18, 18, 20))
    draw = ImageDraw.Draw(canvas)

    # Photo integrated into lower 55% with soft top fade
    if hero_path and Path(hero_path).is_file():
        with Image.open(hero_path) as himg:
            himg = ImageOps.exif_transpose(himg).convert('RGB')
            ph_h = round(sh * 0.58)
            ph_w = sw
            c_ratio = ph_w / ph_h
            i_ratio = himg.width / himg.height
            if i_ratio > c_ratio:
                nh = ph_h
                nw = round(nh * i_ratio)
            else:
                nw = ph_w
                nh = round(nw / i_ratio)
            resized = himg.resize((nw, nh), Image.Resampling.LANCZOS)
            cx = (nw - ph_w) // 2
            cy = (nh - ph_h) // 2
            cropped = resized.crop((cx, cy, cx + ph_w, cy + ph_h)).convert('RGBA')

            # Create alpha fade for top edge
            alpha_mask = Image.new('L', cropped.size, 255)
            mdraw = ImageDraw.Draw(alpha_mask)
            fade_h = round(ph_h * 0.35)
            for y in range(fade_h):
                mdraw.line((0, y, ph_w, y), fill=int(255 * (y / fade_h)))
            cropped.putalpha(alpha_mask)
            canvas.paste(cropped, (0, sh - ph_h), mask=cropped)

    draw = ImageDraw.Draw(canvas)

    # Brand
    bx = round(sw * 0.08)
    by = round(sh * 0.07)
    draw_brand_header(draw, bx, by, scale, font_size=32)

    # Huge bold headline
    tx = bx
    ty = by + 60 * scale
    max_w = round(sw * 0.84)
    size = 84
    while size >= 32:
        hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
        if all(draw.textlength(l, font=hfont) <= max_w for l in lines):
            break
        size -= 2

    hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
    y_cursor = ty
    for i, line in enumerate(lines):
        color = '#F59E0B' if i == 0 else '#FFFFFF'
        draw.text((tx, y_cursor), line, font=hfont, fill=color)
        y_cursor += round(size * 1.15 * scale)

    if subtitle:
        sub_font = load_font('Inter.ttf', 24, scale)
        draw.text((tx, y_cursor + 10 * scale), str(subtitle), font=sub_font, fill='#A1A1AA')

    return canvas


def main():
    parser = argparse.ArgumentParser(description='Baoyu Cover Image Generator')
    parser.add_argument('--output', required=True, type=Path, help='Output image path')
    parser.add_argument('--headline', nargs='+', required=True, help='Headline text lines')
    parser.add_argument('--subtitle', default=None, help='Subtitle copy')
    parser.add_argument('--badge', default=None, help='Category or badge text')
    parser.add_argument('--hero', default=None, type=Path, help='Hero portrait or video frame path')
    parser.add_argument('--aspect', default='9:16', choices=['9:16', '16:9', '1:1'], help='Canvas aspect ratio')
    parser.add_argument('--style', default='cinematic', choices=['cinematic', 'editorial', 'minimal-dark', 'bold-type'], help='Cover design style')
    args = parser.parse_args()

    w, h = 1080, 1920
    if args.aspect == '16:9':
        w, h = 1920, 1080
    elif args.aspect == '1:1':
        w, h = 1080, 1080

    scale = 2
    if args.style == 'cinematic':
        canvas = render_cinematic(w, h, scale, args.headline, args.subtitle, args.badge, args.hero)
    elif args.style == 'editorial':
        canvas = render_editorial(w, h, scale, args.headline, args.subtitle, args.badge, args.hero)
    elif args.style == 'minimal-dark':
        canvas = render_minimal_dark(w, h, scale, args.headline, args.subtitle, args.badge, args.hero)
    elif args.style == 'bold-type':
        canvas = render_bold_type(w, h, scale, args.headline, args.subtitle, args.badge, args.hero)
    else:
        canvas = render_cinematic(w, h, scale, args.headline, args.subtitle, args.badge, args.hero)

    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((w, h), Image.Resampling.LANCZOS).save(out, quality=95)

    print(json.dumps({
        'output': str(out),
        'style': args.style,
        'dimensions': [w, h],
        'status': 'rendered'
    }, indent=2))


if __name__ == '__main__':
    main()
