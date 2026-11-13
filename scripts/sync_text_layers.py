"""Sync saved scene text into a local Hyperframes composition before preview/render."""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from video_workflow import STUDIO, read_json
from text_layers import render_layers


def sync(composition):
    composition=Path(composition).resolve(); index=composition/'index.html'
    if not index.is_file(): return {'changed':False}
    root=(STUDIO/'outputs/reels').resolve()
    project=next((p for p in [composition,*composition.parents] if p.parent==root and (p/'plan.json').is_file()),None)
    if project is None: return {'changed':False}
    plan=read_json(project/'plan.json'); html=index.read_text()
    marker=re.compile(r'<!-- STUDIO TEXT START -->.*?<!-- STUDIO TEXT END -->',re.S)
    shots=[s for s in plan.get('shots',[]) if s.get('text_layers')]
    if not shots and not marker.search(html): return {'changed':False}
    nodes=re.findall(r'<(?:div|section)\b[^>]*>',html)
    content=[]; cues=[]; total=0; changed=False
    def write(path,bytes_):
        nonlocal changed
        if not path.exists() or path.read_bytes()!=bytes_:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(bytes_);changed=True
    import io
    for shot in shots:
        ident=str(shot['id'])
        if not re.fullmatch(r'[A-Za-z0-9_-]+',ident): raise ValueError('Invalid scene identifier.')
        node=next((n for n in nodes if re.search(r'(?:^|\s)id=["\']shot-'+re.escape(ident)+r'["\']',n)),None)
        if not node: raise ValueError(f'Cannot map text layer scene {ident} to the Hyperframes timeline.')
        def attr(name):
            match=re.search(r'\b'+name+r'=["\']([^"\']+)',node)
            if not match: raise ValueError(f'Missing Hyperframes {name} for {ident}.')
            return float(match[1])
        start=attr('data-start'); duration=attr('data-duration'); total=max(total,start+duration)
        buffer=io.BytesIO();render_layers(shot['text_layers']).save(buffer,format='PNG')
        write(composition/f'assets/studio-text/{ident}.png',buffer.getvalue())
        content.append(f'<img id="text-{ident}" src="assets/studio-text/{ident}.png" style="position:absolute;inset:0;width:1080px;height:1920px;opacity:0">')
        cues.append(f'tl.set("#text-{ident}",{{opacity:1}},{start}).set("#text-{ident}",{{opacity:0}},{start+duration});')
    if content:
        template='<template><div id="root" data-composition-id="studio-visual-text" data-width="1080" data-height="1920">'+''.join(content)+'</div><script>const tl=gsap.timeline({paused:true});'+''.join(cues)+'window.__timelines=window.__timelines||{};window.__timelines["studio-visual-text"]=tl;</script></template>'
        write(composition/'compositions/studio-visual-text.html',template.encode())
        addition=f'<!-- STUDIO TEXT START --><div id="studio-visual-text" class="clip" data-composition-id="studio-visual-text" data-composition-src="compositions/studio-visual-text.html" data-start="0" data-duration="{total}" data-track-index="35" data-width="1080" data-height="1920" style="position:absolute;inset:0;z-index:35;pointer-events:none"></div><!-- STUDIO TEXT END -->'
    else: addition=''
    updated=marker.sub('',html)
    if '</body>' not in updated: raise ValueError('Hyperframes index needs a body element.')
    updated=updated.replace('</body>',addition+'</body>')
    write(index,updated.encode())
    return {'changed':changed,'text_scenes':len(shots)}


if __name__=='__main__':
    import json
    print(json.dumps(sync(sys.argv[1] if len(sys.argv)>1 else Path.cwd())))
