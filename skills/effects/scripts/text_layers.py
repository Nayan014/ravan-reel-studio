"""Shared, static text overlays from the local visual editor. Not a catalogue effect."""
import json
import math
from pathlib import Path
import re


def validate_layers(layers):
    if not isinstance(layers,list) or len(layers)>12: raise ValueError('Use at most 12 text layers per scene.')
    ids=set()
    for item in layers:
        if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',item['id']) or item['id'] in ids:
            raise ValueError('Use distinct text layer identifiers.')
        ids.add(item['id'])
        if not isinstance(item.get('text'),str) or not item['text'].strip() or len(item['text'])>400: raise ValueError('Text layers need 1–400 characters.')
        if not isinstance(item.get('color'),str) or not re.fullmatch(r'#[a-fA-F0-9]{6}',item['color']): raise ValueError('Invalid text colour.')
        for key,low,high in [('fontSize',16,240),('x',0,.9),('y',0,.95)]:
            value=item.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high: raise ValueError('Invalid text size or position.')
    return layers


def render_layers(layers,width=1080,height=1920):
    from PIL import Image, ImageDraw, ImageFont
    validate_layers(layers)
    image=Image.new('RGBA',(width,height),(0,0,0,0)); draw=ImageDraw.Draw(image)
    for layer in layers:
        size=max(1,round(layer['fontSize']*width/1080))
        font=ImageFont.truetype(str(Path(__file__).parents[1]/'fonts/Inter.ttf'),size)
        try: font.set_variation_by_axes([32,800])
        except (ValueError,OSError): pass
        box_width=min(.84,1-layer['x'])*width
        lines=[]
        for paragraph in layer['text'].split('\n'):
            line=''
            for char in paragraph:
                if line and font.getlength(line+char)>box_width:
                    split=line.rfind(' ')
                    if split>0:
                        lines.append(line[:split].rstrip());line=line[split+1:]
                    else:
                        lines.append(line.rstrip());line=''
                line+=char
            lines.append(line.rstrip())
        x=(layer['x']*width)+box_width/2; y=layer['y']*height
        for line in lines:
            draw.text((x,y+2*width/1080),line,font=font,fill='#00000080',anchor='mt')
            draw.text((x,y),line,font=font,fill=layer['color'],anchor='mt')
            y+=size*1.15
    return image


if __name__=='__main__':
    import sys
    layers=json.loads(Path(sys.argv[1]).read_text())
    output=Path(sys.argv[2]); output.parent.mkdir(parents=True,exist_ok=True)
    render_layers(layers).save(output)
