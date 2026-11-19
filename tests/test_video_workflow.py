"""Focused checks for selection and the preview approval boundary."""
import importlib.util
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow', ROOT / 'scripts/video_workflow.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = patch.object(workflow, 'STUDIO', self.root)
        self.workspace.start()
        (self.root / 'inputs').mkdir()
        skill = self.root / 'skills/effects'
        (skill / 'references').mkdir(parents=True)
        (skill / 'scripts').mkdir()
        (skill / 'scripts/fx.py').write_text('test renderer version')
        (skill / 'scripts/text_layers.py').write_text('test text renderer version')
        (skill / 'fonts').mkdir()
        (skill / 'fonts/Inter.ttf').write_bytes(b'test font version')
        (skill / 'references/catalogue.json').write_bytes((ROOT / 'skills/effects/references/catalogue.json').read_bytes())

    def tearDown(self):
        self.workspace.stop()
        self.temp.cleanup()

    def video(self, name='clip.mp4'):
        path = self.root / 'inputs' / name
        path.write_bytes(b'fake source bytes for approval checks')
        return path

    def selected(self):
        self.video()
        workflow.start()
        result = workflow.select(1)
        return workflow.load_session(result['id'])

    def reviewable(self, assets=False):
        folder, session = self.selected()
        info = folder / 'analysis.json'
        workflow.write_json(info, {'duration': 12, 'fps': 30, 'has_audio': True})
        session.update({'chosen_id': '6', 'analysis': workflow.relative(info), 'width': 360})
        plan = {'effects': [{'fx': 'backdrop-word', 'start': 2, 'end': 4, 'text': 'CREATE'}]}
        if assets:
            covers = self.root / 'inputs/covers'
            covers.mkdir()
            (covers / 'one.jpg').write_bytes(b'cover image')
            session['chosen_id'] = '4'
            plan['effects'][0] = {'fx': 'orbit', 'start': 2, 'end': 4, 'images': 'inputs/covers'}
        workflow.write_json(folder / 'plan.json', plan)
        frame, overview = folder / 'frame.png', folder / 'overview.jpg'
        frame.write_bytes(b'actual preview bytes'); overview.write_bytes(b'overview bytes')
        session.update({'plan': workflow.relative(folder / 'plan.json'), 'stage': 'review_preview',
                        'preview': {'frames': [workflow.relative(frame)], 'overview': workflow.relative(overview)}})
        session['preview']['id'] = workflow.preview_id(session)
        workflow.save_session(folder, session)
        return folder, session

    def test_lighting_only_review_binds_the_motion_sample(self):
        folder, session = self.reviewable()
        session.pop('chosen_id')
        session['mode'] = 'lighting'
        plan = {'lighting': {'preset':'adaptive-studio'}, 'effects':[]}
        workflow.write_json(folder / 'plan.json', plan)
        (self.root / 'skills/effects/scripts/studio_lighting.py').write_text('test lighting renderer')
        sample = folder / 'comparison.mp4'
        sample.write_bytes(b'first comparison')
        session['preview']['comparison'] = workflow.relative(sample)
        current = workflow.preview_id(session)
        session['preview']['id'] = current
        workflow.save_session(folder, session)
        self.assertEqual(workflow.engine_plan(plan)['effects'][0]['preset'], 'adaptive-studio')
        with self.assertRaisesRegex(ValueError, 'blocked'):
            workflow.render(session['id'])
        sample.write_bytes(b'replaced comparison')
        with self.assertRaisesRegex(ValueError, 'changed'):
            workflow.approve(session['id'], current, 'fixture review')
        with self.assertRaises(ValueError):
            workflow.validated_plan(session, {**plan, 'effects':[{'fx':'orbit'}]})

    def test_three_recent_arrivals_not_latest_modified(self):
        for name in ['first.mp4', 'second.MOV', 'third.webm', 'fourth.mp4']:
            self.video(name)
        (self.root / 'inputs/not-video.jpg').write_bytes(b'image')
        (self.root / 'inputs/nested').mkdir()
        (self.root / 'inputs/nested/hidden.mp4').write_bytes(b'nested video')
        os.utime(self.root / 'inputs/fourth.mp4', (100, 100))
        arrivals = {'first.mp4': 1, 'second.MOV': 2, 'third.webm': 3, 'fourth.mp4': 4}
        with patch.object(workflow, 'input_arrival', side_effect=lambda p: arrivals[p.name]):
            result = workflow.start()
        self.assertEqual([c['name'] for c in result['videos']], ['fourth.mp4', 'third.webm', 'second.MOV'])

    def test_list_number_keeps_meaning_after_another_file_arrives(self):
        self.video('chosen.mp4')
        workflow.start()
        self.video('newer.mp4')
        self.assertEqual(workflow.select(1)['source'], 'inputs/chosen.mp4')

    def test_registered_arrival_does_not_change_when_video_is_edited(self):
        self.video('first.mp4'); self.video('second.mp4')
        with patch.object(workflow, 'input_arrival', side_effect=lambda p: {'first.mp4': 1, 'second.mp4': 2}[p.name]):
            workflow.start()
        (self.root / 'inputs/first.mp4').write_bytes(b'edited original video')
        with patch.object(workflow, 'input_arrival', return_value=999):
            result = workflow.start()
        self.assertEqual([c['name'] for c in result['videos']], ['second.mp4', 'first.mp4'])

    def test_empty_inputs_and_changed_selection(self):
        self.assertEqual(workflow.start()['stage'], 'add_video')
        source = self.video()
        workflow.start()
        source.write_bytes(b'replaced video')
        with self.assertRaisesRegex(ValueError, 'changed after listing'):
            workflow.select(1)

    def test_render_is_blocked_before_user_approval(self):
        _, session = self.reviewable()
        with patch.object(workflow, 'run') as execute:
            with self.assertRaisesRegex(ValueError, 'blocked until the user approves'):
                workflow.render(session['id'])
            execute.assert_not_called()

    def test_stale_preview_id_cannot_be_approved(self):
        _, session = self.reviewable()
        with self.assertRaisesRegex(ValueError, 'changed'):
            workflow.approve(session['id'], 'wrong preview', 'Approved')
        with self.assertRaisesRegex(ValueError, 'explicit approval'):
            workflow.approve(session['id'], session['preview']['id'], '')

    def test_changes_to_plan_frames_source_or_engine_block_render(self):
        for change in ('plan', 'frame', 'overview', 'source', 'engine', 'text_engine', 'text_layers', 'width'):
            with self.subTest(change=change):
                folder, session = self.reviewable()
                workflow.approve(session['id'], session['preview']['id'], 'These frames and this plan look good')
                if change == 'plan':
                    path = self.root / session['plan']; data = workflow.read_json(path)
                    data['effects'][0]['text'] = 'CHANGED'; workflow.write_json(path, data)
                elif change in ('frame', 'overview'):
                    path = folder / ('frame.png' if change == 'frame' else 'overview.jpg')
                    path.write_bytes(b'changed preview')
                elif change == 'source':
                    (self.root / session['source']).write_bytes(b'changed source')
                elif change == 'engine':
                    (self.root / 'skills/effects/scripts/fx.py').write_text('changed renderer')
                elif change == 'text_engine':
                    (self.root / 'skills/effects/scripts/text_layers.py').write_text('changed text renderer')
                elif change == 'text_layers':
                    path=self.root/session['plan']; data=workflow.read_json(path)
                    data['text_layers']=[{'id':'label','text':'CREATE','color':'#ffffff','fontSize':72,'x':.08,'y':.15}]
                    workflow.write_json(path,data)
                else:
                    _, current = workflow.load_session(session['id']); current['width'] = 720
                    workflow.save_session(folder, current)
                with patch.object(workflow, 'run') as execute:
                    with self.assertRaises(ValueError): workflow.render(session['id'])
                    execute.assert_not_called()

    def test_screenshot_changes_invalidate_approval(self):
        _, session = self.reviewable(assets=True)
        workflow.approve(session['id'], session['preview']['id'], 'Approved')
        (self.root / 'inputs/covers/one.jpg').write_bytes(b'changed cover')
        with self.assertRaisesRegex(ValueError, 'changed'):
            workflow.render(session['id'])

    def test_lighting_is_before_graphics_and_part_of_approval(self):
        for changed in ('config', 'engine'):
            with self.subTest(changed=changed):
                folder, session = self.reviewable()
                module = self.root / 'skills/effects/scripts/studio_lighting.py'
                module.write_text('lighting engine version 1')
                path = self.root / session['plan']
                plan = workflow.read_json(path)
                plan['lighting'] = {'preset': 'natural-studio'}
                normalized = workflow.validated_plan(session, plan)
                self.assertEqual(normalized['lighting'], plan['lighting'])
                compiled = workflow.engine_plan(normalized)
                self.assertEqual([e['fx'] for e in compiled['effects']], ['studio-light', 'backdrop-word'])
                self.assertNotIn('lighting', compiled)
                times = workflow.preview_times(normalized, {'duration': 12, 'fps': 30})
                self.assertTrue(any(t < 2 for t in times))
                self.assertTrue(any(t > 10 for t in times))
                workflow.write_json(path, normalized)
                session['preview']['id'] = workflow.preview_id(session)
                workflow.save_session(folder, session)
                workflow.approve(session['id'], session['preview']['id'], 'Approve these lighting frames')
                if changed == 'config':
                    normalized['lighting']['screen_regions'] = [[[.1,.1],[.2,.1],[.2,.2]]]
                    workflow.write_json(path, normalized)
                else:
                    module.write_text('lighting engine version 2')
                with patch.object(workflow, 'run') as execute:
                    with self.assertRaisesRegex(ValueError, 'changed'):
                        workflow.render(session['id'])
                    execute.assert_not_called()

    def test_plan_matches_the_users_selected_image_and_duration(self):
        _, session = self.reviewable()
        with self.assertRaisesRegex(ValueError, 'chosen image'):
            workflow.validated_plan(session, {'effects': [{'fx': 'orbit', 'start': 2, 'end': 4}]})
        with self.assertRaisesRegex(ValueError, 'inside the selected video'):
            workflow.validated_plan(session, {'effects': [{'fx': 'backdrop-word', 'start': 2, 'end': 20}]})
        with self.assertRaisesRegex(ValueError, 'each chosen effect'):
            workflow.validated_plan(session, {'effects': []})

    def test_multiple_selected_effects_are_preserved_and_clear_approval(self):
        folder, session = self.reviewable()
        session['recommendations'] = 'already shown'
        workflow.save_session(folder, session)
        workflow.approve(session['id'], session['preview']['id'], 'Approved')
        workflow.choose(session['id'], '49,5,6')
        _, current = workflow.load_session(session['id'])
        self.assertEqual(current['chosen_id'], '49')
        self.assertEqual(current['chosen_ids'], ['49', '5', '6'])
        self.assertNotIn('approval', current)
        plan = {'effects': [
            {'fx': 'lean-in', 'start': 1.9, 'end': 3.75, 'zoom': 1.15},
            {'fx': 'huge-strike', 'start': .55, 'end': 1.8, 'text': 'DEVELOPER'},
            {'fx': 'backdrop-word', 'start': 2.65, 'end': 3.75, 'text': 'CEO'}]}
        self.assertEqual(workflow.validated_plan(current, plan), plan)
        with self.assertRaisesRegex(ValueError, 'each chosen effect'):
            workflow.validated_plan(current, {'effects': plan['effects'][:2]})
        duplicate = {'effects': [plan['effects'][0], plan['effects'][1], plan['effects'][1]]}
        with self.assertRaisesRegex(ValueError, 'without duplicates'):
            workflow.validated_plan(current, duplicate)
        with self.assertRaisesRegex(ValueError, 'distinct catalogue'):
            workflow.choose(session['id'], '6,6')

    def test_preview_samples_cover_each_effect_window(self):
        plan = {'effects': [{'start': 0, 'end': 1}, {'start': 5, 'end': 6}, {'start': 8, 'end': 10}]}
        times = workflow.preview_times(plan, {'fps': 30, 'duration': 12})
        self.assertEqual(len(times), 9)
        for effect in plan['effects']:
            self.assertEqual(sum(effect['start'] <= t < effect['end'] for t in times), 3)

    def test_changing_any_effect_in_a_combined_plan_blocks_render(self):
        folder, session = self.reviewable()
        session['chosen_ids'] = ['6', '49']
        data = workflow.read_json(folder / 'plan.json')
        data['effects'].append({'fx': 'huge-strike', 'start': 0, 'end': 1, 'text': 'DEVELOPER'})
        workflow.write_json(folder / 'plan.json', data)
        session['preview']['id'] = workflow.preview_id(session)
        workflow.save_session(folder, session)
        workflow.approve(session['id'], session['preview']['id'], 'Approve both effects')
        data['effects'][1]['text'] = 'CHANGED'
        workflow.write_json(folder / 'plan.json', data)
        with self.assertRaisesRegex(ValueError, 'changed'):
            workflow.render(session['id'])

    def test_sample_selection_clears_existing_approval(self):
        folder, session = self.reviewable()
        session['recommendations'] = 'already shown'
        workflow.save_session(folder, session)
        workflow.approve(session['id'], session['preview']['id'], 'Approved')
        workflow.choose(session['id'], 'B1')
        _, current = workflow.load_session(session['id'])
        self.assertEqual(current['chosen_id'], 'b1')
        self.assertNotIn('preview', current)
        self.assertNotIn('approval', current)
        plan = {'effects': [{'fx': 'spotlight', 'look': 'sparkle', 'start': 2, 'end': 4, 'text': 'SHINE'}]}
        self.assertEqual(workflow.validated_plan(current, plan), plan)

    def test_transcription_failure_is_reported_without_inventing_speech(self):
        folder, session = self.selected()
        def fake_run(command, log=None):
            if any(str(p).endswith('words.py') for p in command):
                raise ValueError('Transcription model unavailable offline')
            Path(command[-1]).write_bytes(b'extracted media')
            return ''
        def fake_board(cards, destination, headings):
            destination.write_bytes(b'source overview')
        with patch.object(workflow, 'probe', return_value={'duration': 2, 'fps': 30, 'width': 360, 'height': 640, 'has_audio': True}), patch.object(workflow, 'run', side_effect=fake_run), patch.object(workflow, 'runtime', return_value=Path(sys.executable)), patch.object(workflow, 'board', side_effect=fake_board):
            result = workflow.analyze(session['id'], transcribe=True)
        self.assertEqual(result['stage'], 'analyzed')
        self.assertIsNone(result['transcript'])
        self.assertIn('unavailable offline', result['transcription_error'])
        self.assertNotIn('spoken_text', result)


if __name__ == '__main__':
    unittest.main()
