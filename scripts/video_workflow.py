#!/usr/bin/env python3
"""Local helpers for the agent-led video-edit workflow. No model API is required."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
from fractions import Fraction
from datetime import datetime, timezone

STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(STUDIO/'skills/effects/scripts'))
from text_layers import validate_layers
from studio_lighting import validate_lighting, expand_lighting
VIDEO_TYPES = {'.mp4', '.mov', '.m4v', '.webm', '.mkv', '.avi'}
IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.webp'}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def relative(path):
    return path.resolve().relative_to(STUDIO.resolve()).as_posix()


def effects_root():
    return STUDIO / 'skills/effects'


def runtime():
    subpath = '.venv/Scripts/python.exe' if os.name == 'nt' else '.venv/bin/python'
    path = effects_root() / subpath
    if not path.is_file():
        raise ValueError('Run the local effects setup first; its Python environment is missing.')
    return path


def run(command, log=None):
    env = os.environ.copy()
    env['MPLCONFIGDIR'] = str(effects_root() / '.cache/matplotlib')
    env['PIP_CACHE_DIR'] = str(effects_root() / '.cache/pip')
    result = subprocess.run([str(x) for x in command], capture_output=True, text=True, env=env)
    if log:
        log.write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    if result.returncode:
        raise ValueError(f'Command failed: {result.stderr[-1800:] or result.stdout[-1800:]}')
    return result.stdout


def probe(path):
    data = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))
    stream = next((s for s in data['streams'] if s['codec_type'] == 'video'
                   and not s.get('disposition', {}).get('attached_pic')), None)
    if stream is None:
        raise ValueError('The selected file has no video stream.')
    duration = float(data.get('format', {}).get('duration') or stream.get('duration') or 0)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('The video duration could not be determined.')
    def frame_rate(value):
        try: return Fraction(value) if Fraction(value)>0 else None
        except (ValueError,ZeroDivisionError,TypeError): return None
    nominal=frame_rate(stream.get('r_frame_rate')); average=frame_rate(stream.get('avg_frame_rate'))
    actual=nominal or average
    if actual is None: raise ValueError('Cannot determine the source frame rate.')
    rotation=float(next((s['rotation'] for s in stream.get('side_data_list',[]) if 'rotation' in s),stream.get('tags',{}).get('rotate',0)))
    width,height=stream['width'],stream['height']
    if round(rotation)%180: width,height=height,width
    audio=next((s for s in data['streams'] if s['codec_type']=='audio'),None)
    return {'duration':duration,'fps':float(actual),'fps_fraction':str(actual),'width':width,'height':height,
            'coded_width':stream['width'],'coded_height':stream['height'],'rotation':rotation,
            'variable_frame_rate':bool(nominal and average and abs(float(nominal-average))>float(nominal)*.001),
            'frame_count':int(stream['nb_frames']) if str(stream.get('nb_frames','')).isdigit() else None,
            'has_audio':audio is not None,'audio_duration':float(audio.get('duration',duration)) if audio else None}


def input_arrival(path):
    stat = path.stat()
    # Copying a file with an old mtime can also preserve/rewind birth time.
    # ctime records that copy's metadata operation. Cache this estimate below
    # so later edits do not move an already discovered input up the list.
    return max(getattr(stat, 'st_birthtime', 0), stat.st_ctime)


def newest_inputs():
    folder = STUDIO / 'inputs'
    folder.mkdir(exist_ok=True)
    videos = [p for p in folder.iterdir()
              if p.is_file() and not p.is_symlink() and not p.name.startswith('.')
              and p.suffix.lower() in VIDEO_TYPES]
    registry_path = STUDIO / 'outputs/.workflow/arrivals.json'
    previous = read_json(registry_path) if registry_path.is_file() else {}
    registry = {}
    for path in videos:
        stat = path.stat()
        identity = [stat.st_dev, stat.st_ino]
        old = previous.get(path.name, {})
        registry[path.name] = old if old.get('identity') == identity else {
            'identity': identity, 'arrival': input_arrival(path)}
    write_json(registry_path, registry)
    return sorted(videos, key=lambda p: (registry[p.name]['arrival'], p.name.casefold()), reverse=True)[:3]


def start():
    videos = newest_inputs()
    candidates = [{'number': n, 'name': p.name, 'path': relative(p),
                   'size': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns}
                  for n, p in enumerate(videos, 1)]
    write_json(STUDIO / 'outputs/.workflow/candidates.json', candidates)
    return {'stage': 'pick_video' if candidates else 'add_video', 'videos': candidates,
            'message': 'Ask the user to pick 1, 2 or 3.' if candidates else 'Add a video to inputs, then start again.',
            'order': 'Newest arrival first, maximum three. First discovery uses filesystem creation/change time; later edits keep their original position.'}


def load_session(session_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', session_id):
        raise ValueError('Use the session identifier returned by select.')
    folder = STUDIO / 'outputs/edits' / session_id
    return folder, read_json(folder / 'session.json')


def save_session(folder, session):
    write_json(folder / 'session.json', session)


def check_source(session):
    source = (STUDIO / session['source']).resolve()
    if not source.is_relative_to((STUDIO / 'inputs').resolve()) or not source.is_file():
        raise ValueError('The input video is missing. Start again and choose a video.')
    if digest(source) != session['source_sha256']:
        raise ValueError('The source video changed. Start again so it can be analyzed and reviewed.')
    return source


def invalidate(session):
    session.pop('preview', None)
    session.pop('approval', None)
    session.pop('render', None)


def select(number):
    candidates = read_json(STUDIO / 'outputs/.workflow/candidates.json')
    candidate = next((c for c in candidates if c['number'] == number), None)
    if candidate is None:
        raise ValueError('Choose a number from the latest displayed list.')
    source = STUDIO / candidate['path']
    if not source.is_file() or source.stat().st_size != candidate['size'] or source.stat().st_mtime_ns != candidate['mtime_ns']:
        raise ValueError('That input changed after listing. Run start again.')
    session_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    session = {'id': session_id, 'source': candidate['path'], 'source_sha256': digest(source), 'stage': 'selected'}
    folder = STUDIO / 'outputs/edits' / session_id
    save_session(folder, session)
    return {'session': session_id, **session}


def board(cards, destination, headings):
    from PIL import Image, ImageDraw, ImageFont
    width, image_w, image_h = 256, 240, 427
    columns = min(3, len(cards))
    sheet = Image.new('RGB', (columns * width, math.ceil(len(cards) / columns) * 490), '#f3f5f7')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(effects_root() / 'fonts/Inter.ttf'), 18)
    for i, (path, label) in enumerate(zip(cards, headings)):
        x, y = (i % columns) * width + 8, (i // columns) * 490 + 8
        image = Image.open(path).convert('RGB')
        image.thumbnail((image_w, image_h))
        sheet.paste(image, (x + (image_w - image.width) // 2, y))
        lines = []
        while font.getlength(label) > image_w:
            count = len(label)
            while font.getlength(label[:count]) > image_w:
                count -= 1
            split = max(label.rfind(' ', 0, count + 1), label.rfind('-', 0, count + 1) + 1)
            split = split if split > count // 2 else count
            lines.append(label[:split].strip())
            label = label[split:].strip()
        lines.append(label)
        for j, line in enumerate(lines[:2]):
            draw.text((x, y + image_h + 4 + j * 22), line, font=font, fill='#15191c')
    sheet.save(destination)


def analyze(session_id, transcribe=False):
    folder, session = load_session(session_id)
    source = check_source(session)
    invalidate(session)
    session.pop('chosen_id', None)
    session.pop('chosen_ids', None)
    session.pop('recommendations', None)
    session['stage'] = 'analyzing'
    save_session(folder, session)
    info = probe(source)
    output = folder / 'analysis'
    output.mkdir(exist_ok=True)
    last_frame = max(0, math.ceil(info['duration'] * info['fps']) - 1)
    times = [round(math.floor(last_frame * f) / info['fps'], 6) for f in (.05, .2, .4, .6, .8, .95)]
    frames = []
    for i, second in enumerate(times, 1):
        target = output / f'source-{i}.jpg'
        run(['ffmpeg', '-v', 'error', '-y', '-ss', second, '-i', source, '-frames:v', '1',
             '-vf', 'scale=640:640:force_original_aspect_ratio=decrease', target])
        if not target.is_file():
            raise ValueError('A source frame could not be decoded.')
        frames.append(target)
    board(frames, output / 'source-overview.jpg', [f'{t:.2f} seconds' for t in times])
    info.update({'frames': [relative(p) for p in frames], 'overview': relative(output / 'source-overview.jpg'),
                 'frame_times': times, 'transcript': None})
    if info['has_audio']:
        audio = output / 'speech.wav'
        run(['ffmpeg', '-v', 'error', '-y', '-i', source, '-vn', '-ac', '1', '-ar', '16000', audio])
        info['audio'] = relative(audio)
        if transcribe:
            try:
                run([runtime(), effects_root() / 'scripts/words.py', audio], output / 'transcription.log')
                transcript = audio.with_suffix('.words.json')
                words = read_json(transcript)
                info['transcript'] = relative(transcript)
                info['spoken_text'] = ' '.join(w['w'] for w in words)
            except (ValueError, OSError, json.JSONDecodeError) as exc:
                info['transcription_error'] = str(exc)
    write_json(output / 'analysis.json', info)
    session['analysis'] = relative(output / 'analysis.json')
    session['stage'] = 'analyzed'
    save_session(folder, session)
    return {'session': session_id, 'stage': session['stage'], **info,
            'next': 'Inspect these frames and the speech content before proposing effects.'}


def catalogue():
    return {str(item['id']).lower(): item for item in read_json(effects_root() / 'references/catalogue.json')}


def recommend(session_id, file):
    folder, session = load_session(session_id)
    check_source(session)
    if 'analysis' not in session:
        raise ValueError('Analyze the selected video before recommending effects.')
    data = read_json(file)
    suggestions = data.get('recommendations', [])
    if not data.get('summary') or not 1 <= len(suggestions) <= 3:
        raise ValueError('Provide a video summary and one to three recommendations.')
    entries = catalogue()
    seen = set()
    images, labels = [], []
    for item in suggestions:
        key = str(item['id']).lower()
        if key not in entries or key in seen or not str(item.get('reason', '')).strip():
            raise ValueError('Each recommendation needs a unique catalogue ID and a reason.')
        seen.add(key)
        entry = entries[key]
        item['id'], item['name'] = entry['id'], entry['name']
        item['sample'] = relative(effects_root() / entry['preview'])
        images.append(STUDIO / item['sample'])
        labels.append(f"{entry['id']}  {entry['name']}")
    board(images, folder / 'recommendations.jpg', labels)
    write_json(folder / 'recommendations.json', data)
    invalidate(session)
    session.pop('chosen_id', None)
    session.pop('chosen_ids', None)
    session['recommendations'] = relative(folder / 'recommendations.json')
    session['stage'] = 'pick_effect'
    save_session(folder, session)
    return {'session': session_id, 'stage': session['stage'], **data,
            'recommended_samples': relative(folder / 'recommendations.jpg'),
            'all_sample_sheets': [f'docs/effect-gallery/effects-{i}.jpg' for i in range(1, 7)],
            'next': 'Show the recommended dummy samples and all six sample sheets. Ask the user to choose an image number.'}


def choose(session_id, effect_id):
    folder, session = load_session(session_id)
    check_source(session)
    if 'recommendations' not in session:
        raise ValueError('Show recommendations and the sample gallery before asking for a choice.')
    ids = [key.strip().lower() for key in str(effect_id).split(',')]
    entries = catalogue()
    if len(ids) != len(set(ids)) or any(key not in entries for key in ids):
        raise ValueError('Choose distinct catalogue numbers from 1 to 51 or B1 to B3; separate multiple choices with commas.')
    selected = [entries[key] for key in ids]
    invalidate(session)
    session['chosen_id'] = ids[0]  # Preserve the original single-choice session field.
    session['chosen_ids'] = ids
    session['stage'] = 'effect_chosen'
    save_session(folder, session)
    return {'session': session_id, 'stage': session['stage'], 'chosen': selected[0], 'chosen_all': selected,
            'next': 'Draft a plan containing each chosen effect, using real words, timings and values from the video.'}


def validated_plan(session, data):
    entries = catalogue()
    selected = session.get('chosen_ids', [session['chosen_id']])
    remaining = [(entries[key]['config']['fx'], entries[key]['config'].get('look')) for key in selected]
    rows = data.get('effects') if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows or len(rows) != len(selected):
        raise ValueError('The plan must include each chosen effect exactly once.')
    info = read_json(STUDIO / session['analysis'])
    normalized = []
    for row in rows:
        effect = dict(row)
        # The canonical fx and look distinguish bonus cards from base effects.
        if effect.get('fx') == 'glitter-spotlight':
            effect['fx'], effect['look'] = 'spotlight', 'sparkle'
        identity = (effect.get('fx'), effect.get('look'))
        if identity not in remaining:
            raise ValueError('The plan must match the chosen images, including bonus looks, without duplicates.')
        remaining.remove(identity)
        start, end = float(effect['start']), float(effect['end'])
        if not all(math.isfinite(x) for x in (start, end)) or not 0 <= start < end <= info['duration']:
            raise ValueError('Effect timing must be inside the selected video.')
        if end - start < 1 / info['fps']:
            raise ValueError('The effect must last at least one video frame.')
        effect['start'], effect['end'] = start, end
        for key in ('text', 'lines', 'name', 'handle', 'title', 'label', 'images'):
            if key in effect and not isinstance(effect[key], str):
                raise ValueError(f'{key} must be text.')
        if 'images' in effect:
            assets = Path(effect['images'])
            assets = assets if assets.is_absolute() else STUDIO / assets
            if not assets.is_dir():
                raise ValueError('The selected screenshot folder does not exist.')
            effect['images'] = relative(assets) if assets.resolve().is_relative_to(STUDIO.resolve()) else str(assets.resolve())
        normalized.append(effect)
    result={'effects': normalized}
    if 'lighting' in data:
        result['lighting'] = validate_lighting(data['lighting'])
    if data.get('text_layers'):
        result['text_layers']=validate_layers(data['text_layers'])
    return result


def preview_times(plan, info):
    fps = info['fps']
    times = set()
    if plan.get('lighting'):
        last = max(0, math.ceil(info['duration'] * fps) - 1)
        times.update(round(round(last * fraction) / fps, 6) for fraction in (.1, .5, .9))
    for effect in plan['effects']:
        first = math.ceil(effect['start'] * fps)
        last = min(math.ceil(effect['end'] * fps) - 1, max(0, math.ceil(info['duration'] * fps) - 1))
        times.update(round((first + round((last - first) * fraction)) / fps, 6)
                     for fraction in (.2, .5, .8))
    return sorted(times)


def engine_plan(plan):
    data = expand_lighting(json.loads(json.dumps(plan)))
    for effect in data['effects']:
        if 'images' in effect and not Path(effect['images']).is_absolute():
            effect['images'] = str((STUDIO / effect['images']).resolve())
    return data


def fingerprint(session):
    source = check_source(session)
    plan = validated_plan(session, read_json(STUDIO / session['plan']))
    assets = []
    for effect in engine_plan(plan)['effects']:
        if effect.get('images'):
            for path in sorted(Path(effect['images']).iterdir()):
                if path.is_file() and path.suffix.lower() in IMAGE_TYPES | VIDEO_TYPES:
                    assets.append([path.name, digest(path)])
    result = {'source': digest(source), 'plan': plan, 'assets': assets,
            'engine': digest(effects_root() / 'scripts/fx.py'),
            'text_engine': digest(effects_root() / 'scripts/text_layers.py'),
            'text_font': digest(effects_root()/'fonts/Inter.ttf') if plan.get('text_layers') else None,
            'width': session['width']}
    if plan.get('lighting'):
        result['lighting_engine'] = digest(effects_root() / 'scripts/studio_lighting.py')
    return result


def preview_id(session):
    preview = session.get('preview')
    if not preview:
        raise ValueError('Create actual video preview frames before approval or rendering.')
    data = {'inputs': fingerprint(session),
            'frames': [[name, digest(STUDIO / name)] for name in preview['frames']],
            'overview': digest(STUDIO / preview['overview'])}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def preview(session_id, file, width=1080):
    folder, session = load_session(session_id)
    source = check_source(session)
    if 'chosen_id' not in session:
        raise ValueError('The user must choose an effect sample before real preview frames are created.')
    plan = validated_plan(session, read_json(file))
    if width < 144 or width > 2160 or width % 2:
        raise ValueError('Preview width must be an even value between 144 and 2160.')
    invalidate(session)
    session['stage'] = 'previewing'
    session['width'] = width
    # Version the preview so a revised plan never overwrites frames the user saw.
    output = folder / ('preview-' + uuid.uuid4().hex[:8])
    output.mkdir()
    write_json(output / 'plan.json', plan)
    session['plan'] = relative(output / 'plan.json')
    save_session(folder, session)
    write_json(output / 'engine-plan.json', engine_plan(plan))
    info = read_json(STUDIO / session['analysis'])
    times = preview_times(plan, info)
    run([runtime(), effects_root() / 'scripts/fx.py', '--plan', output / 'engine-plan.json',
         source, output / 'frame.png', '--still', ','.join(str(t) for t in times), '--width', width],
        output / 'preview.log')
    frames = sorted(output.glob('frame*.png'))
    if len(frames) != len(times):
        raise ValueError('The renderer did not create all requested preview frames. Inspect preview.log.')
    board(frames, output / 'overview.jpg', [f'{t:.2f} seconds' for t in times])
    session['preview'] = {'frames': [relative(p) for p in frames], 'times': times,
                          'overview': relative(output / 'overview.jpg')}
    session['preview']['id'] = preview_id(session)
    session['stage'] = 'review_preview'
    save_session(folder, session)
    return {'session': session_id, 'stage': session['stage'], 'plan': plan, **session['preview'],
            'next': 'Show the actual frames and this plan. Wait for explicit user approval before calling approve or render.'}


def approve(session_id, expected_id, message):
    folder, session = load_session(session_id)
    if session['stage'] != 'review_preview' or not message.strip():
        raise ValueError('Approval needs a current preview and the user\'s explicit approval message.')
    current = preview_id(session)
    if current != expected_id or current != session['preview']['id']:
        raise ValueError('The plan, source, assets or preview changed. Create and review new frames.')
    session['approval'] = {'preview_id': current, 'user_message': message,
                           'at': datetime.now(timezone.utc).isoformat()}
    session['stage'] = 'approved'
    save_session(folder, session)
    return {'session': session_id, 'stage': 'approved', 'preview_id': current}


def render(session_id):
    folder, session = load_session(session_id)
    approval = session.get('approval')
    if not approval or session['stage'] not in ('approved', 'rendered'):
        raise ValueError('Rendering is blocked until the user approves the actual preview frames and plan.')
    current = preview_id(session)
    if current != approval['preview_id'] or current != session['preview']['id']:
        raise ValueError('The reviewed plan, source, assets or frames changed. Preview and obtain approval again.')
    source = check_source(session)
    plan = read_json(STUDIO / session['plan'])
    output = folder / 'renders'
    output.mkdir(exist_ok=True)
    destination = output / f'{source.stem}_effects_{current[:12]}.mp4'
    if destination.exists() and session.get('render') != relative(destination):
        raise ValueError('An unverified output already exists. Move it aside before retrying.')
    if session.get('render') != relative(destination):
        write_json(output / 'engine-plan.json', engine_plan(plan))
        run([runtime(), effects_root() / 'scripts/fx.py', '--plan', output / 'engine-plan.json', source,
             destination, '--width', session['width']], output / 'render.log')
    result = probe(destination)
    original = read_json(STUDIO / session['analysis'])
    if original['has_audio'] and not result['has_audio']:
        raise ValueError('The output is missing the source audio. Inspect render.log before delivering.')
    if abs(result['duration'] - original['duration']) > max(.2, 2 / original['fps']):
        raise ValueError('The output duration does not match the source. Inspect render.log before delivering.')
    session['render'], session['stage'] = relative(destination), 'rendered'
    save_session(folder, session)
    return {'session': session_id, 'stage': 'rendered', 'video': str(destination), 'info': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('start', help='List at most three newest input videos; wait for a choice.')
    pick = commands.add_parser('select'); pick.add_argument('number', type=int)
    for name in ('analyze', 'recommend', 'choose', 'preview', 'approve', 'render', 'status'):
        command = commands.add_parser(name)
        command.add_argument('--session', required=True)
        if name == 'analyze': command.add_argument('--transcribe', action='store_true')
        if name == 'recommend': command.add_argument('--file', required=True, type=Path)
        if name == 'choose': command.add_argument('effect_id')
        if name == 'preview':
            command.add_argument('--plan', required=True, type=Path)
            command.add_argument('--width', default=1080, type=int)
        if name == 'approve':
            command.add_argument('--preview-id', required=True)
            command.add_argument('--message', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'start': result = start()
        elif args.command == 'select': result = select(args.number)
        elif args.command == 'analyze': result = analyze(args.session, args.transcribe)
        elif args.command == 'recommend': result = recommend(args.session, args.file)
        elif args.command == 'choose': result = choose(args.session, args.effect_id)
        elif args.command == 'preview': result = preview(args.session, args.plan, args.width)
        elif args.command == 'approve': result = approve(args.session, args.preview_id, args.message)
        elif args.command == 'render': result = render(args.session)
        else: result = load_session(args.session)[1]
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
