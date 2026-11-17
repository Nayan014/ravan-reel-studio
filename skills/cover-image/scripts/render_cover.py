#!/usr/bin/env python3
"""Render a cover from a project JSON composition using Pillow and bundled fonts."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path(__file__).resolve().parents[1]


def render(spec_path, output):
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text())
    token_path = spec_path.parent / spec['style_tokens'] if spec.get('style_tokens') else SKILL / 'assets/style.json'
    style = json.loads(token_path.read_text())
    w, h = spec.get('size', [1080, 1920])
    if not (320 <= w <= 3840 and 320 <= h <= 3840):
        raise ValueError('Canvas edges must be between 320 and 3840 pixels.')
    lines = spec['headline']
    if not 1 <= len(lines) <= 4 or any(not line.strip() for line in lines):
        raise ValueError('Supply one to four nonempty headline lines.')
    scale = 2
    canvas = Image.new('RGB', (w * scale, h * scale))
    # A subtle vertical charcoal gradient, rendered entirely locally.
    d = ImageDraw.Draw(canvas)
    if style.get('background'):
        d.rectangle((0,0,w*scale,h*scale),fill=style['background'])
    else:
        for y in range(h * scale):
            t = y / (h * scale)
            d.line((0, y, w * scale, y), fill=(7 + int(4*t), 13 + int(5*t), 21 + int(6*t)))

    def font(name, size):
        return ImageFont.truetype(str(ROOT / style[name]), round(size * scale))

    def rect(box):
        return tuple(round(v * scale) for v in box)

    # All boxes in the spec are fractions of the canvas, making a landscape
    # composition explicit rather than cropping a finished portrait cover.
    hero = spec.get('hero', {})
    bx, by, bw, bh = hero.get('box', [.1, .48, .8, .30])
    bx, by, bw, bh = bx*w, by*h, bw*w, bh*h
    horizon = by + bh*.20
    if style.get('glow',True):
        glow = Image.new('RGB', canvas.size)
        gd = ImageDraw.Draw(glow)
        gd.ellipse(rect((bx+bw*.15, horizon-35, bx+bw*.85, horizon+100)), fill='#075766')
        glow = glow.filter(ImageFilter.GaussianBlur(65*scale))
        from PIL import ImageChops
        canvas = ImageChops.add(canvas, glow)
    d = ImageDraw.Draw(canvas)
    if style.get('grid',True):
        for j in range(14):
            t = j/13
            y = horizon + (h-horizon)*(t*t)
            d.line(rect((0,y,w,y)), fill='#102A35', width=scale)
        for j in range(-12, 14):
            d.line(rect((w*.5+j*30,horizon,w*.5+j*160,h)), fill='#102A35', width=scale)

    polygons = hero.get('polygons', [])
    projected = [[((bx+x*bw)*scale, (by+y*bh)*scale) for x,y in ring] for ring in polygons]
    depth = hero.get('depth', 24) * scale
    for offset in range(round(depth), 0, -1):
        for ring in projected:
            d.polygon([(x,y+offset) for x,y in ring], fill='#09232C')
    for ring in projected:
        d.polygon(ring, fill=style.get('hero_fill','#172B37'))
    if projected and style.get('engraving',True):
        # Fine diagonal engraving clipped inside the polygon mask.
        mask = Image.new('L', canvas.size)
        md = ImageDraw.Draw(mask)
        for ring in projected:
            md.polygon(ring, fill=255)
        engraving = canvas.copy()
        ed = ImageDraw.Draw(engraving)
        for y in range(round(by), round(by+bh), 7):
            ed.line(rect((bx,y,bx+bw,y-bw*.15)), fill='#1E3642', width=scale)
        canvas.paste(engraving, mask=mask)
        d = ImageDraw.Draw(canvas)
    for ring in projected:
        d.line(ring+[ring[0]], fill=style['accent'], width=round(style.get('outline_width',3)*scale), joint='curve')
    if hero.get('image'):
        asset = (spec_path.parent / hero['image']).resolve()
        with Image.open(asset) as image:
            image = ImageOps.exif_transpose(image).convert('RGBA')
            image.thumbnail((round(bw*scale),round(bh*scale)), Image.Resampling.LANCZOS)
            canvas.paste(image,(round((bx+bw)*scale-image.width),round((by+bh)*scale-image.height)),image)

    brand_x, brand_y = spec.get('brand_position', [.09, .235])
    brand_x, brand_y = round(brand_x*w*scale), round(brand_y*h*scale)
    bf = font('brand_font', spec.get('brand_size', 36))
    # Explicit compact word gap; monospace's natural space is too wide here.
    gap = spec.get('brand_size',36)*style['brand_gap_em']
    advance = d.textlength('TECHNO', font=bf) + gap*scale
    d.text((brand_x,brand_y),'TECHNO',font=bf,fill=style['techno'],anchor='lt')
    d.text((brand_x+advance,brand_y),'RAVAN',font=bf,fill=style['ravan'],anchor='lt')

    tx, ty, tw = spec.get('headline_box', [.085, .285, .83])
    x, y, limit = round(tx*w*scale), round(ty*h*scale), tw*w*scale
    sizes = []
    for i, text in enumerate(lines):
        size = min(w,h)*spec.get('headline_size', .125)
        while size >= 16:
            hf = font('headline_font',size)
            box = d.textbbox((0,0),text,font=hf)
            if max(box[2]-box[0],d.textlength(text,font=hf)) <= limit:
                break
            size -= 1
        else:
            raise ValueError('Headline cannot fit; shorten the copy or add line breaks.')
        d.text((x,y),text,font=hf,fill=style.get('headline_accent',style['accent']) if i==len(lines)-1 else style['text'],anchor='lt')
        y += round((size*1.12+12)*scale)
        sizes.append(round(size,2))
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    canvas.resize((w,h),Image.Resampling.LANCZOS).save(output)
    return {'output':str(output.resolve()),'size':[w,h],
            'brand_gap_px':round(gap,2),
            'headline_sizes':sizes,'style_version':style['version']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.spec,args.output),indent=2))
    except (ValueError,OSError,KeyError) as error:
        parser.exit(1,f'{error}\n')
