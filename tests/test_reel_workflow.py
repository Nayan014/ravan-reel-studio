import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reel_workflow as rw


class CombinedReelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=rw.STUDIO/'outputs')
        self.folder=Path(self.temp.name)
        for name in ['raw','assets','working']: (self.folder/name).mkdir()
        source=self.folder/'raw/1.mp4'; source.write_bytes(b'source media fixture')
        self.plan={'version':1,'slug':'test','title':'Test reel','style':'flat','palette':'clay',
                   'visual_selection':'Use the clean shot without effects.',
                   'shots':[{'id':'01','source':'1.mp4','source_sha256':rw.digest(source),
                     'clip':[0,2],'say':'Build with AI.','words':[
                         {'text':'Build','start':0.1,'end':0.5},
                         {'text':'with','start':0.6,'end':0.8},
                         {'text':'AI.','start':0.9,'end':1.2}],
                     'caption_pages':['Build with','AI.'],'text_confirmed':True,
                     'layout':'full','focus':[0.5,0.4],
                     'vibha':{'status':'none','effects':[]},'remotion':{'status':'none'}}]}
        self.probe=patch.object(rw,'probe',return_value={'duration':2,'has_audio':True})
        self.probe.start(); self.addCleanup(self.probe.stop)
        rw.write_json(self.folder/'plan.json',self.plan)
    def tearDown(self): self.temp.cleanup()
    def validate(self): return rw.validate(self.folder,self.plan)
    def test_valid_clean_scene(self): self.validate()
    def test_pending_visuals_block_preview(self):
        self.plan['shots'][0]['vibha']['status']='pending'
        with self.assertRaisesRegex(ValueError,'pending'): self.validate()
    def test_unverified_speech_blocks_preview(self):
        self.plan['shots'][0]['text_confirmed']=False
        with self.assertRaisesRegex(ValueError,'transcript'): self.validate()
    def test_captions_must_match_actual_speech(self):
        self.plan['shots'][0]['caption_pages']=['Invented words']
        with self.assertRaisesRegex(ValueError,'Caption'): self.validate()
    def test_changed_source_is_rejected(self):
        (self.folder/'raw/1.mp4').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'source changed'): self.validate()
    def test_effect_timing_relative_to_trim(self):
        self.plan['shots'][0]['vibha']={'status':'selected','effects':[{'id':13,'start':1,'end':3}]}
        with self.assertRaisesRegex(ValueError,'inside'): self.validate()
    def test_full_graphic_cannot_hide_selected_effect(self):
        shot=self.plan['shots'][0]; shot['layout']='graphic'
        shot['vibha']={'status':'selected','effects':[{'id':13,'start':0,'end':1}]}
        shot['remotion']={'status':'selected','scene':'Statement','props':{'text':'BUILD'}}
        with self.assertRaisesRegex(ValueError,'hidden'): self.validate()
    def test_camera_effect_does_not_double_punch(self):
        shot=self.plan['shots'][0]; shot['layout']='punch'
        shot['vibha']={'status':'selected','effects':[{'id':5,'start':0,'end':1}]}
        with self.assertRaisesRegex(ValueError,'double zoom'): self.validate()
    def test_screenshot_needs_actual_asset(self):
        shot=self.plan['shots'][0]; shot['layout']='graphic'
        shot['remotion']={'status':'selected','scene':'Screenshot','props':{'src':'assets/missing.png'}}
        with self.assertRaisesRegex(ValueError,'existing files'): self.validate()
    def test_assets_cannot_escape_project(self):
        with self.assertRaisesRegex(ValueError,'assets'): rw.asset(self.folder,'../outside.png')
    def reviewed(self):
        png=self.folder/'frame.png'; png.write_bytes(b'actual fixture frame')
        review=self.folder/'review.html'; review.write_text('Reviewed scene')
        record={'inputs':rw.input_hash(self.folder),'files':[str(png),str(review)],'review':str(review)}
        record['id']=rw.preview_digest(record)
        rw.write_json(self.folder/'preview.json',record)
        rw.write_json(self.folder/'approval.json',{'preview_id':record['id'],'message':'Approve fixture'})
    def test_render_requires_actual_preview_approval(self):
        with self.assertRaisesRegex(ValueError,'No approval'): rw.approval_check(self.folder)
    def test_current_approved_revision_is_accepted(self):
        self.reviewed(); rw.approval_check(self.folder)
    def test_plan_change_invalidates_approval(self):
        self.reviewed(); self.plan['title']='Revised'; rw.write_json(self.folder/'plan.json',self.plan)
        with self.assertRaisesRegex(ValueError,'No approval'): rw.approval_check(self.folder)
    def test_visual_text_edit_invalidates_approval(self):
        self.reviewed()
        self.plan['shots'][0]['text_layers']=[{'id':'headline','text':'BUILD','color':'#ffffff','fontSize':72,'x':.08,'y':.15}]
        rw.write_json(self.folder/'plan.json',self.plan)
        with self.assertRaisesRegex(ValueError,'No approval'): rw.approval_check(self.folder)
    def test_preview_image_change_invalidates_approval(self):
        self.reviewed(); (self.folder/'frame.png').write_bytes(b'changed preview')
        with self.assertRaisesRegex(ValueError,'No approval'): rw.approval_check(self.folder)
    def test_asset_change_invalidates_approval(self):
        self.reviewed(); (self.folder/'assets/screen.png').write_bytes(b'new screenshot')
        with self.assertRaisesRegex(ValueError,'No approval'): rw.approval_check(self.folder)
    def test_prepared_video_change_invalidates_approval(self):
        self.reviewed()
        prepared=self.folder/'working/normalized.mp4'; prepared.write_bytes(b'prepared video')
        record=rw.read_json(self.folder/'preview.json'); record['media_files']=[str(prepared)]
        record['id']=rw.preview_digest(record)
        rw.write_json(self.folder/'preview.json',record)
        rw.write_json(self.folder/'approval.json',{'preview_id':record['id']})
        prepared.write_bytes(b'changed prepared video')
        with self.assertRaisesRegex(ValueError,'No approval'): rw.approval_check(self.folder)
    def test_html_has_takes_and_one_integrated_table(self):
        output=rw.make_html(self.folder,self.plan)
        content=output.read_text()
        self.assertEqual(content.count('<table>'),1)
        for value in ['Take 01','What I say','CC on screen','Vibha effect','Remotion graphic','Build with AI.']:
            self.assertIn(value,content)
    def test_generated_review_can_be_reimported_as_script(self):
        output=rw.make_html(self.folder,self.plan)
        parser=rw.ScriptLines(); parser.feed(output.read_text())
        self.assertEqual(parser.lines,['Build with AI.'])
    def test_html_explains_framing_and_take_join(self):
        second=copy.deepcopy(self.plan['shots'][0]); second.update(id='02',layout='punch',join_note='Use a closer crop for this take.')
        self.plan['shots'].append(second)
        content=rw.make_html(self.folder,self.plan).read_text()
        self.assertIn('closer crop',content)
        self.assertIn('Edit join:',content)
        self.assertIn('Use a closer crop for this take.',content)
    def test_graphic_review_uses_plain_text_instead_of_json(self):
        shot=self.plan['shots'][0]; shot['layout']='graphic'
        shot['remotion']={'status':'selected','scene':'Statement','props':{'text':'BUILD WITH AI'}}
        content=rw.make_html(self.folder,self.plan).read_text()
        self.assertIn('Text: BUILD WITH AI',content)
        self.assertNotIn('&quot;text&quot;:',content)
    def test_suggested_reference_does_not_select_the_effect(self):
        shot=self.plan['shots'][0]
        shot['vibha']={'status':'pending','effects':[],
                       'suggestions':[{'id':42,'title':'Gentle option','reason':'A subtle opening.'}]}
        content=rw.make_html(self.folder,self.plan).read_text()
        self.assertIn('#42',content)
        self.assertIn('Dummy reference · not applied',content)
        with self.assertRaisesRegex(ValueError,'pending'): self.validate()
    def test_hyperframes_project_cannot_silently_use_remotion_preview(self):
        self.plan['renderer']='hyperframes';rw.write_json(self.folder/'plan.json',self.plan)
        with patch.object(rw,'project',return_value=self.folder):
            with self.assertRaisesRegex(ValueError,'Hyperframes'): rw.preview('test')
    def test_hyperframes_project_cannot_silently_use_remotion_render(self):
        self.plan['renderer']='hyperframes';rw.write_json(self.folder/'plan.json',self.plan)
        with patch.object(rw,'project',return_value=self.folder):
            with self.assertRaisesRegex(ValueError,'Hyperframes'): rw.render('test')

if __name__=='__main__': unittest.main()
