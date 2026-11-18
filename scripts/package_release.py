#!/usr/bin/env python3
"""Make a separate, reviewable public source tree without touching local projects."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
ROOT_FILES={'.gitignore','.nvmrc','README.md','LICENSE','THIRD_PARTY_NOTICES.md','CONTRIBUTING.md',
            'AGENTS.md','CLAUDE.md','GEMINI.md','SOURCE.json','package.json'}
ROOT_DIRS={'.agents','.claude','.gemini','assets','dashboard','docs','examples','scripts','skills','tests','tools'}
PRIVATE_DIRS={'.git','.venv','.cache','__pycache__','node_modules','inputs','outputs'}
PRIVATE_DOCS={'intro-reel-plan.html','intro-reel-script.md','Intro_Reel_Shoot_Plan.pdf'}
VIDEO_TYPES={'.mp4','.mov','.m4v','.mkv','.avi','.webm','.mts','.m2ts'}
AUDIO_TYPES={'.wav','.mp3','.m4a','.aac','.flac','.aif','.aiff','.ogg'}
PUBLIC_AUDIO_DIRS={'tools/techno-reel/public/music','tools/techno-reel/public/sfx','tools/techno-reel/examples/example/audio','assets/audio/voices'}


def excluded(path):
    """Do not infer private footage from its extension: credited library media is public."""
    if path.parts and path.parts[0]=='references':return True
    name=path.name.lower()
    if path.suffix.lower() in VIDEO_TYPES and path.as_posix()!='examples/demo/export/demo.mp4':return True
    if path.suffix.lower() in AUDIO_TYPES and path.parent.as_posix() not in PUBLIC_AUDIO_DIRS:return True
    if len(path.parts)>1:
        if path.parts[:2]==('docs','local'):return True
        discovery={'.agents':'skills','.claude':'skills','.gemini':'commands'}
        if path.parts[0] in discovery and path.parts[1]!=discovery[path.parts[0]]:return True
    if any(p in PRIVATE_DIRS for p in path.parts):return True
    if path.name in PRIVATE_DOCS or name=='.ds_store' or name.endswith(('.pyc','.pem','.key','.p12','.pfx')):return True
    if name=='.env' or name.startswith('.env.') and name!='.env.example':return True
    if name=='credentials.json' or name.startswith('service-account') and name.endswith('.json'):return True
    return False


def inventory(root):
    root=root.resolve();found=[]
    def visit(directory):
        for path in sorted(directory.iterdir()):
            rel=path.relative_to(root)
            if excluded(rel):continue
            if path.is_symlink():
                target=os.readlink(path)
                if rel.parts[0] not in {'.agents','.claude','.gemini'} or os.path.isabs(target):
                    raise ValueError(f'Unexpected publication symlink: {rel}')
                resolved=path.resolve(strict=True)
                if not resolved.is_relative_to(root/'skills'):
                    raise ValueError(f'Discovery link leaves canonical public skills: {rel}')
                found.append((rel,path,target))
            elif path.is_dir():visit(path)
            elif path.is_file():found.append((rel,path,None))
    for name in sorted(ROOT_FILES):
        path=root/name
        if path.is_symlink():raise ValueError(f'Root source cannot be a symlink: {name}')
        if path.is_file():found.append((Path(name),path,None))
    for name in sorted(ROOT_DIRS):
        path=root/name
        if path.is_symlink():raise ValueError(f'Public directory cannot be a symlink: {name}')
        if path.is_dir():visit(path)
    return found


def package(destination,root=ROOT):
    root=root.resolve();destination=Path(destination).absolute()
    if destination.exists() or destination.is_symlink():raise ValueError('Destination already exists. Choose a new empty path; nothing is overwritten.')
    resolved=destination.resolve()
    if root.is_relative_to(resolved) or resolved.is_relative_to(root) and not resolved.is_relative_to(root/'outputs'):
        raise ValueError('Choose a separate destination or a new folder inside outputs/.')
    files=inventory(root)
    # Validate every link before writing a partial package.
    available={p.as_posix() for p,_,_ in files}
    for rel,src,target in files:
        if target is not None:
            real=src.resolve().relative_to(root).as_posix()
            if real not in available and not any(name.startswith(real+'/') for name in available):
                raise ValueError(f'Discovery target is not in the public inventory: {rel}')
    destination.mkdir(parents=True);records=[];size=0
    for rel,src,target in files:
        out=destination/rel;out.parent.mkdir(parents=True,exist_ok=True)
        if target is not None:
            out.symlink_to(target,target_is_directory=src.is_dir())
            records.append({'path':rel.as_posix(),'symlink':target})
        else:
            shutil.copy2(src,out);content=out.read_bytes();size+=len(content)
            records.append({'path':rel.as_posix(),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
    for name in ['inputs','outputs','references']:
        (destination/name).mkdir();(destination/name/'.gitkeep').touch()
        records.append({'path':f'{name}/.gitkeep','bytes':0,'sha256':hashlib.sha256(b'').hexdigest()})
    manifest={'project':'Ravan Reel Studio','repository_name':'ravan-reel-studio','source_bytes':size,
              'files':sorted(records,key=lambda r:r['path']),
              'excluded':'Private recordings, reference media and analysis, outputs, personal documents, environments, caches and credential files. Inspect source text separately before publishing.'}
    (destination/'PUBLICATION_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'destination':str(destination),'files':len(records),'source_bytes':size,'manifest':str(destination/'PUBLICATION_MANIFEST.json')}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    try:print(json.dumps(package(args.output),indent=2))
    except (ValueError,OSError) as error:p.exit(1,f'{error}\n')
