#!/usr/bin/env python3
"""
Hybrid Cover Image Generator: AI Topic Visual + Real Human Creator
Combines the AI-generated mobile engineering visual (3D smartphone, code, architecture)
with the real creator portrait in perfect aspect ratio (0% distortion).
"""
import argparse
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


def crop_human_face(hd_image_path, target_w, target_h):
    """
    Extracts the creator from 4K source with EXACT aspect ratio preservation.
    Zero stretching or distortion.
    """
    with Image.open(hd_image_path) as img:
        img = ImageOps.exif_transpose(img).convert('RGBA')
        iw, ih = img.size

        # Nayan's face and upper torso center is roughly at x=50%, y=30%
        target_ratio = target_w / target_h

        # Calculate crop rectangle that fits target_ratio
        if (iw / ih) > target_ratio:
            # Image is wider than target ratio
            ch = round(ih * 0.70)
            cw = round(ch * target_ratio)
        else:
            # Image is taller than target ratio
            cw = round(iw * 0.82)
            ch = round(cw / target_ratio)

        # Center horizontally, position slightly higher vertically to capture head + shoulders
        cx = (iw - cw) // 2
        cy = round(ih * 0.15)
        # Ensure within bounds
        if cy + ch > ih:
            cy = ih - ch

        cropped = img.crop((cx, cy, cx + cw, cy + ch))
        return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def round_card(img, radius):
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.width, img.height), radius=radius, fill=255)
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result.paste(img, (0, 0), mask=mask)
    return result


def build_hybrid_cover(visual_path, creator_path, output_path, variant='split'):
    w, h = 1080, 1920
    scale = 2
    sw, sh = w * scale, h * scale

    # 1. Base Canvas & AI Topic Visual
    with Image.open(visual_path) as vimg:
        vimg = ImageOps.exif_transpose(vimg).convert('RGB')
        c_ratio = sw / sh
        i_ratio = vimg.width / vimg.height
        if i_ratio > c_ratio:
            nh = sh
            nw = round(nh * i_ratio)
        else:
            nw = sw
            nh = round(nw / i_ratio)
        resized_v = vimg.resize((nw, nh), Image.Resampling.LANCZOS)
        cx = (nw - sw) // 2
        cy = (nh - sh) // 2
        canvas = resized_v.crop((cx, cy, cx + sw, cy + sh))

    # 2. Gradient Scrim for Top Legibility
    top_scrim = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(top_scrim)
    scrim_end = round(sh * 0.36)
    for y in range(scrim_end):
        t = 1.0 - (y / scrim_end)
        alpha = int(230 * (t ** 1.3))
        sdraw.line((0, y, sw, y), fill=(8, 10, 16, alpha))

    # Bottom scrim for creator base & footer
    bot_scrim = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bot_scrim)
    bot_start = round(sh * 0.72)
    for y in range(bot_start, sh):
        t = (y - bot_start) / (sh - bot_start)
        alpha = int(220 * (t ** 1.4))
        bdraw.line((0, y, sw, y), fill=(8, 10, 16, alpha))

    canvas = Image.alpha_composite(canvas.convert('RGBA'), top_scrim)
    canvas = Image.alpha_composite(canvas, bot_scrim).convert('RGB')
    draw = ImageDraw.Draw(canvas)

    # 3. Brand Header
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
    bw = draw.textlength(badge_text, font=b_font) + 22 * scale
    bh = 32 * scale
    rx = sw - round(sw * 0.08) - bw
    ry = by + 2 * scale
    draw.rounded_rectangle((rx, ry, rx + bw, ry + bh), radius=6 * scale, fill=(15, 23, 42, 210), outline='#F59E0B', width=scale)
    draw.text((rx + 11 * scale, ry + 7 * scale), badge_text, font=b_font, fill='#F59E0B')

    # 4. Headline Typography
    lines = ["10 YEARS", "BUILDING MOBILE APPS"]
    max_w = round(sw * 0.84)
    size = 74
    while size >= 32:
        hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)
        if all(draw.textlength(l, font=hfont) <= max_w for l in lines):
            break
        size -= 2
    hfont = load_font('ArchivoBlack-Regular.ttf', size, scale)

    ty = by + 60 * scale
    for i, line in enumerate(lines):
        color = '#F59E0B' if i == 1 else '#FFFFFF'
        # Drop shadow for readability
        draw.text((bx + 2 * scale, ty + 2 * scale), line, font=hfont, fill=(0, 0, 0, 240))
        draw.text((bx, ty), line, font=hfont, fill=color)
        ty += round(size * 1.15 * scale)

    # Subtitle
    sub_font = load_font('Inter.ttf', 22, scale)
    sub_text = "Architecture - Lessons - What Really Matters"
    draw.text((bx + scale, ty + 6 * scale + scale), sub_text, font=sub_font, fill=(0, 0, 0, 200))
    draw.text((bx, ty + 6 * scale), sub_text, font=sub_font, fill='#CBD5E1')

    # 5. Integrate Real Human Creator (with 0% distortion / perfect aspect ratio)
    if creator_path and Path(creator_path).is_file():
        if variant == 'split':
            # Prominent portrait card in the lower third (perfect 4:5 ratio)
            card_w = round(280 * scale)
            card_h = round(350 * scale)
            card_x = round(sw * 0.08)
            card_y = sh - card_h - round(sh * 0.08)

            human_crop = crop_human_face(creator_path, card_w, card_h)
            rounded_human = round_card(human_crop, radius=18 * scale)

            # Drop shadow under the human card
            shadow = Image.new('RGBA', (card_w + 24 * scale, card_h + 24 * scale), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(shadow)
            s_draw.rounded_rectangle(
                (6 * scale, 6 * scale, card_w + 18 * scale, card_h + 18 * scale),
                radius=20 * scale,
                fill=(0, 0, 0, 180)
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(10 * scale))
            canvas.paste(shadow, (card_x - 12 * scale, card_y - 12 * scale), mask=shadow)

            # Draw outer accent border
            draw.rounded_rectangle(
                (card_x - 2 * scale, card_y - 2 * scale, card_x + card_w + 2 * scale, card_y + card_h + 2 * scale),
                radius=20 * scale,
                outline='#F59E0B',
                width=round(2.5 * scale)
            )
            canvas.paste(rounded_human, (card_x, card_y), mask=rounded_human)

            # Verified Creator Pill Label attached below the photo
            pill_w = round(card_w * 0.92)
            pill_h = round(42 * scale)
            pill_x = card_x + (card_w - pill_w) // 2
            pill_y = card_y + card_h - round(pill_h * 0.65)

            draw.rounded_rectangle(
                (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
                radius=8 * scale,
                fill=(15, 23, 42, 240),
                outline='#F59E0B',
                width=scale
            )
            name_font = load_font('Inter.ttf', 14, scale)
            verified_text = "NAYAN V.  [10+ YRS]"
            v_len = draw.textlength(verified_text, font=name_font)
            draw.text(
                (pill_x + (pill_w - v_len) / 2, pill_y + 10 * scale),
                verified_text,
                font=name_font,
                fill='#FFFFFF'
            )

            # Floating Context Pill on the right side pointing to the smartphone
            ctx_font = load_font('SpaceMono-Bold.ttf', 13, scale)
            ctx_text = "SWIFT // KOTLIN // PRODUCTION"
            cw = draw.textlength(ctx_text, font=ctx_font) + 20 * scale
            ch = 30 * scale
            cx_pos = sw - round(sw * 0.08) - cw
            cy_pos = sh - round(sh * 0.10)
            draw.rounded_rectangle(
                (cx_pos, cy_pos, cx_pos + cw, cy_pos + ch),
                radius=6 * scale,
                fill=(15, 23, 42, 220),
                outline='#38BDF8',
                width=scale
            )
            draw.text((cx_pos + 10 * scale, cy_pos + 6 * scale), ctx_text, font=ctx_font, fill='#38BDF8')

        elif variant == 'circle':
            # Perfectly proportioned 1:1 circle (0% distortion)
            card_sz = round(200 * scale)
            pos_x = round(sw * 0.08)
            pos_y = sh - card_sz - round(sh * 0.08)

            human_crop = crop_human_face(creator_path, card_sz, card_sz)

            # Circular mask
            mask = Image.new('L', (card_sz, card_sz), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse((0, 0, card_sz, card_sz), fill=255)

            # Outer ring & glow
            draw.ellipse(
                (pos_x - 3 * scale, pos_y - 3 * scale, pos_x + card_sz + 3 * scale, pos_y + card_sz + 3 * scale),
                fill=(15, 23, 42),
                outline='#F59E0B',
                width=round(2.5 * scale)
            )
            canvas.paste(human_crop, (pos_x, pos_y), mask=mask)

            # Creator Badge Tag beside the avatar
            lbl_font_bold = load_font('Inter.ttf', 18, scale)
            lbl_font_muted = load_font('SpaceMono-Bold.ttf', 13, scale)
            tx_c = pos_x + card_sz + 18 * scale
            ty_c = pos_y + 40 * scale

            lbl_w = round(240 * scale)
            lbl_h = round(64 * scale)
            draw.rounded_rectangle(
                (tx_c - 8 * scale, ty_c - 8 * scale, tx_c + lbl_w, ty_c + lbl_h),
                radius=10 * scale,
                fill=(15, 23, 42, 230),
                outline=(51, 65, 85),
                width=scale
            )
            draw.text((tx_c, ty_c), "NAYAN V.", font=lbl_font_bold, fill='#FFFFFF')
            draw.text((tx_c, ty_c + 26 * scale), "10+ YRS MOBILE DEV", font=lbl_font_muted, fill='#F59E0B')

    # 6. Save final output
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((w, h), Image.Resampling.LANCZOS).save(out, quality=95)
    print(f"Hybrid Cover Rendered: {out}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--visual', required=True)
    parser.add_argument('--creator', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--variant', default='split', choices=['split', 'circle'])
    args = parser.parse_args()
    build_hybrid_cover(args.visual, args.creator, args.output, variant=args.variant)
