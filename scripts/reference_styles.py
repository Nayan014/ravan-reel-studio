#!/usr/bin/env python3
"""Local reference sampling and reusable, agent-authored editing style notes."""
import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from video_workflow import STUDIO, digest, probe, read_json

VERSION = 1
VIDEO_TYPES = {'.mp4', '.mov', '.m4v', '.mkv', '.avi', '.webm', '.mts', '.m2ts'}
PATTERNS = ('pacing', 'typography', 'colour', 'framing', 'transitions', 'graphics', 'audio')


def safe_path(path):
    """Keep reference media, caches and project snapshots inside this workspace."""
    path = Path(path)
    if not path.is_relative_to(STUDIO):
        raise ValueError('Choose a path inside this studio.')
    current = STUDIO
    for part in path.relative_to(STUDIO).parts:
        if part in ('.', '..'):
            raise ValueError('Invalid reference path.')
        current = current / part
        if current.is_symlink():
            raise ValueError('Reference media and storage cannot use symlinks.')
    return path


def write_json(path, value):
    path = safe_path(path)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix='.reference-', suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, indent=2)
            stream.write('\n')
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def reference_file(name):
    relative = Path(name)
    if relative.parts and relative.parts[0] == 'references':
        relative = Path(*relative.parts[1:])
    if relative.is_absolute() or not relative.parts or any(part.startswith('.') for part in relative.parts):
        raise ValueError('Choose a video filename relative to references/.')
    source = safe_path(STUDIO / 'references' / relative)
    if source.suffix.lower() not in VIDEO_TYPES or not source.is_file():
        raise ValueError('The selected reference video is missing or unsupported.')
    return source


def cache_at(sha):
    return safe_path(STUDIO / '.cache' / 'reference-styles' / f'v{VERSION}' / sha)


def library():
    folder = safe_path(STUDIO / 'references')
    if not folder.exists():
        return {'references': []}
    entries = []
    for source in sorted(folder.iterdir(), key=lambda item: item.name.casefold()):
        if source.is_symlink() or not source.is_file() or source.suffix.lower() not in VIDEO_TYPES:
            continue
        # Listing stays cheap. Content hashes are computed only for a selected file.
        entries.append({'name': source.name, 'bytes': source.stat().st_size})
    return {'references': entries}


def ffmpeg(arguments, folder):
    log = folder / 'sampling.log'
    with log.open('w') as stream:
        result = subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', *map(str, arguments)],
                                cwd=folder, stdout=subprocess.DEVNULL, stderr=stream)
    if result.returncode:
        raise ValueError('Reference sampling failed. See ' + str(log))


def ready_profile(folder, sha):
    file = safe_path(folder / 'profile.json')
    if not file.is_file():
        return None
    value = read_json(file)
    if not isinstance(value, dict):
        return None
    if value.get('version') != VERSION or value.get('source_sha256') != sha:
        return None
    return value


def prepare(name):
    source = reference_file(name)
    sha = digest(source)
    folder = cache_at(sha)
    if folder.exists():
        for child in folder.rglob('*'):
            safe_path(child)
    folder.mkdir(parents=True, exist_ok=True)
    profile = ready_profile(folder, sha)
    if profile:
        return {'status': 'cached_style', 'name': name, 'source_sha256': sha,
                'summary': profile['summary'], 'patterns': profile['patterns'],
                'profile': str(folder / 'profile.json'), 'notes': str(folder / 'notes.md')}
    manifest = folder / 'samples.json'
    if manifest.is_file():
        saved = read_json(manifest)
        if saved.get('version') == VERSION and saved.get('source_sha256') == sha:
            paths = [folder / saved['board'], *[folder / f['file'] for f in saved['frames']]]
            if all(safe_path(file).is_file() for file in paths):
                return {'status': 'samples_ready', 'name': name, 'source_sha256': sha,
                        'board': str(folder / saved['board']), 'observations': str(manifest),
                        'next': 'Inspect the sampled frames and timings, then save evidence-based style notes.'}
    info = probe(source)
    duration = info['duration']
    scan_duration = min(duration, 120)
    # Coarse cut candidates are measured locally, not presented as exact edit boundaries.
    ffmpeg(['-i', source, '-t', scan_duration, '-an', '-vf',
            "fps=4,scale=320:-2,select='gt(scene,0.28)',metadata=print:file=cuts.txt",
            '-f', 'null', '-'], folder)
    cut_file = folder / 'cuts.txt'
    cut_text = cut_file.read_text() if cut_file.exists() else ''
    cuts = [float(value) for value in re.findall(r'pts_time:([0-9.]+)', cut_text)]
    cuts = sorted(set(value for value in cuts if 0 < value < scan_duration))
    moments = [duration * fraction for fraction in (.08, .35, .65, .9)]
    moments += [cuts[0], cuts[len(cuts)//2]] if cuts else [duration*.2, duration*.8]
    moments = sorted(set(round(value, 4) for value in moments))
    frames = []
    for index, moment in enumerate(moments):
        for offset, label in [(-.12, 'before'), (.12, 'after')]:
            time = max(0, min(moment + offset, max(0, duration-.05)))
            filename = f'frame-{index:02d}-{label}.jpg'
            ffmpeg(['-ss', time, '-i', source, '-an', '-vf', 'scale=480:-2',
                    '-frames:v', '1', filename], folder)
            frames.append({'time': time, 'file': filename})
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    font = ImageFont.truetype(str(STUDIO/'skills/effects/fonts/Inter.ttf'), 18)
    cell_width = 300
    cell_height = 436 if info['height'] > info['width'] else 196
    board = Image.new('RGB', (cell_width*4, (cell_height+32)*math.ceil(len(frames)/4)), '#f5f1e9')
    draw = ImageDraw.Draw(board)
    for index, frame in enumerate(frames):
        x, y = (index % 4)*cell_width, (index // 4)*(cell_height+32)
        with Image.open(folder/frame['file']) as image:
            thumb = ImageOps.contain(image.convert('RGB'), (cell_width-12, cell_height-12))
            board.paste(thumb, (x+(cell_width-thumb.width)//2, y+(cell_height-thumb.height)//2))
        draw.text((x+8, y+cell_height+4), f'{frame["time"]:.2f}s', font=font, fill='#493d39')
    board.save(folder/'contact-sheet.jpg', quality=88)
    if digest(source) != sha:
        raise ValueError('The reference changed while sampling. Prepare the current file again.')
    write_json(manifest, {'version': VERSION, 'source_sha256': sha, 'media': info,
                         'cut_scan_seconds': scan_duration, 'coarse_cut_times': cuts,
                         'frames': frames, 'board': 'contact-sheet.jpg',
                         'coverage': 'Six paired sample moments across the video; coarse cut scan covers at most the first 120 seconds. Audio is not transcribed or analysed.'})
    return {'status': 'samples_ready', 'name': name, 'source_sha256': sha,
            'board': str(folder/'contact-sheet.jpg'), 'observations': str(manifest),
            'next': 'Inspect frames and timings. Save observed patterns, uncertainties and production suggestions.'}


def save_profile(name, file):
    source = reference_file(name)
    sha = digest(source)
    folder = cache_at(sha)
    manifest = read_json(safe_path(folder/'samples.json'))
    if manifest.get('version') != VERSION or manifest.get('source_sha256') != sha:
        raise ValueError('Prepare the current reference before saving its style.')
    candidate = Path(file).read_bytes()
    if len(candidate) > 65536:
        raise ValueError('Keep the reference profile under 64 KB.')
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError('Provide a reference style JSON object.')
    if not isinstance(value.get('summary'), str) or not value['summary'].strip() or len(value['summary']) > 800:
        raise ValueError('Provide a concise reference summary, up to 800 characters.')
    patterns = value.get('patterns', {})
    if not isinstance(patterns, dict) or set(patterns) != set(PATTERNS):
        raise ValueError('Describe pacing, typography, colour, framing, transitions, graphics and audio.')
    if any(not isinstance(text, str) or not text.strip() or len(text) > 1000 for text in patterns.values()):
        raise ValueError('Keep each pattern description between 1 and 1000 characters.')
    evidence = value.get('evidence', [])
    if not isinstance(evidence, list) or not evidence or len(evidence) > 12:
        raise ValueError('Provide 1–12 timestamped observations from the reference samples.')
    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError('Each evidence item needs a time and observation.')
        time = item.get('time')
        if not isinstance(time, (float, int)) or not math.isfinite(time) or not 0 <= time <= manifest['media']['duration']:
            raise ValueError('Evidence timestamps must lie inside the reference.')
        if not isinstance(item.get('observation'), str) or not item['observation'].strip() or len(item['observation']) > 500:
            raise ValueError('Each observation needs concise supporting text.')
    profile = {'version': VERSION, 'source_sha256': sha, 'summary': value['summary'].strip(),
               'patterns': patterns, 'evidence': evidence, 'coverage': manifest['coverage']}
    notes = '# Reference style\n\n' + profile['summary'] + '\n\n'
    for key in PATTERNS:
        notes += f'## {key.capitalize()}\n\n{patterns[key]}\n\n'
    notes += '## Evidence\n\n' + ''.join(f'- {item["time"]:.2f}s — {item["observation"]}\n' for item in evidence)
    notes += '\n## Coverage\n\n' + profile['coverage'] + '\n'
    safe_path(folder/'notes.md').write_text(notes)
    write_json(safe_path(folder/'profile.json'), profile)
    return {'status': 'style_saved', 'name': name, 'summary': profile['summary'],
            'profile': str(folder/'profile.json'), 'notes': str(folder/'notes.md')}


def use_style(kind, slug, name=None):
    import reel_workflow as workflow
    workflow.PROJECT_KIND = kind
    folder, plan = workflow.plan_at(slug)
    safe_path(folder/'plan.json')
    if plan.get('pipeline_version') != 2 or plan.get('phase') == 'draft':
        raise ValueError('Reference style selection starts after footage is imported or attached.')
    previous = plan.get('reference_style')
    if name is None:
        plan['reference_style'] = None
        plan['reference_selection'] = 'none'
    else:
        source = reference_file(name)
        sha = digest(source)
        cached = cache_at(sha)
        profile = ready_profile(cached, sha)
        if not profile:
            raise ValueError('Prepare and save this reference style before selecting it.')
        target = safe_path(folder/'assets/reference-styles'/digest(cached/'profile.json'))
        target.mkdir(parents=True, exist_ok=True)
        # Snapshot the style, not the reference footage. External library edits cannot change approval.
        write_json(safe_path(target/'profile.json'), profile)
        notes = safe_path(cached/'notes.md').read_text()
        safe_path(target/'notes.md').write_text(notes)
        plan['reference_style'] = {'name': name, 'source_sha256': sha, 'summary': profile['summary'],
                                   'profile_sha256': digest(target/'profile.json'),
                                   'profile': (target/'profile.json').relative_to(folder).as_posix(),
                                   'notes': (target/'notes.md').relative_to(folder).as_posix()}
        plan['reference_selection'] = 'selected'
    if previous != plan['reference_style']:
        plan['visual_selection'] = None
        for shot in plan['shots']:
            shot.pop('reference_note', None)
    write_json(folder/'plan.json', plan)
    workflow.make_html(folder, plan)
    return {'project': slug, 'kind': kind, 'reference_style': plan['reference_style'],
            'next': 'Use the saved style to propose scene treatments, then review the production plan and actual frames.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    for name in ('prepare', 'save'):
        command = commands.add_parser(name)
        command.add_argument('--file', required=True)
        if name == 'save':
            command.add_argument('--profile', required=True)
    command = commands.add_parser('use')
    command.add_argument('--kind', choices=['reels','videos'], required=True)
    command.add_argument('--project', required=True)
    choice = command.add_mutually_exclusive_group(required=True)
    choice.add_argument('--file')
    choice.add_argument('--none', action='store_true')
    args = parser.parse_args()
    if args.command == 'list':
        result = library()
    elif args.command == 'prepare':
        result = prepare(args.file)
    elif args.command == 'save':
        result = save_profile(args.file, args.profile)
    else:
        result = use_style(args.kind, args.project, args.file)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        sys.exit(1)
