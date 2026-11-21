"""Synthetic data is exclusively under pytest tmp_path, never research data/."""
import copy,csv,io,json,time,zipfile
import pytest
from backend.engine import Engine,LabError
from backend.external import External,public_session
from backend.models import CalibrationPoint,Questionnaire
from backend.practice import practice_action
from backend.assignment import save_plan,plan
from backend.tracks import validate_tracks
from backend.exporting import export_sessions
from backend.export_schema import enrich
from backend.storage import read_json
from pathlib import Path

CHECKS=dict(starting_frame=True,display=True,fullscreen=True,hints_off=True)
def prepare(e,x,track):
 s=x.quick_start(track);sid=s['session_id'];e.attach(sid,'p');e.step(sid,'information');e.step(sid,'consent');e.calibration_start(sid)
 for i in range(5):e.calibration_point(sid,CalibrationPoint(index=i,viewport={'fullscreen':True},presented_at=i))
 assert e.get(sid)['state']=='practice'
 return sid

def test_track_validation_rejects_table_corruption():
 registry=read_json(Path(__file__).parents[1]/'config/tracks.json')
 assert validate_tracks(registry)=={'valid':True,'errors':[],'track_count':30,'unique_configurations':27}
 registry['tracks'][1]['rounds'][1]['variant_label']='Button(Good)+Status(Bad)'
 assert not validate_tracks(registry)['valid']

def test_practice_gate_resume_and_exclusion(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);sid=prepare(e,x,'T07')
 assert e.get(sid)['participant_id']=='P007'
 with pytest.raises(LabError):practice_action(e,sid,'complete')
 with pytest.raises(LabError):e.answers(sid,'pre',{})
 for a in ('button','menu'):practice_action(e,sid,a)
 e=Engine(tmp_path,tmp_path/'configuration.json')
 assert len(e.get(sid)['practice_attempts'][-1]['events'])==2
 for a in ('search','status','complete'):practice_action(e,sid,a)
 assert e.get(sid)['state']=='pre' and e.get(sid)['practice_completed']
 assert e.storage.rows(e.get(sid),'gaze')==[] and e.get(sid)['trials']==[]

def test_seeded_assignment_is_unique_reproducible_and_locked(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');a=save_plan(e,'mock',731)
 assert len(set(a['assignments'].values()))==30
 assert plan(Engine(tmp_path,tmp_path/'configuration.json'),'mock')==a
 other=Engine(tmp_path/'other',tmp_path/'other/configuration.json')
 assert save_plan(other,'mock',731)['assignments']==a['assignments']
 x=External(e);s=x.quick_start('T01');pid=next(p for p,t in a['assignments'].items() if t=='T01')
 assert s['participant_id']==pid and s['assignment']['seed']==731
 with pytest.raises(LabError):save_plan(e,'mock',1)
 assert x.quick_start('T01')['session_id']==s['session_id']

def test_combined_gaze_validity_and_missing_coordinates():
 s={'trials':[{'trial_id':'a','metadata_index':0}],'metadata':[{'viewport':{'screen_width':1920,'screen_height':1080}}],'mode':'hardware','external':{}}
 row={'trial_id':'a','left_gaze_x':'.2','left_gaze_y':'.4','left_validity':'1','right_gaze_x':'.6','right_gaze_y':'.8','right_validity':'1','raw_json':'{}'}
 r=next(enrich('gaze',[row],s));assert r['gaze_x']==.4 and r['gaze_y']==pytest.approx(.6)
 row['right_validity']='0';assert next(enrich('gaze',[row],s))['gaze_x']==.2
 row['left_gaze_x']='nan';r=next(enrich('gaze',[row],s));assert r['gaze_x'] is None and r['gaze_y'] is None

def test_all_thirty_participants_four_trials_and_nine_export_files(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);e.external=x
 for v in x.prototypes()['variants']:x.update(v['name'],v['url'],'verified')
 for n in range(1,31):
  sid=prepare(e,x,f'T{n:02d}')
  for a in ('button','menu','search','status','complete'):practice_action(e,sid,a)
  e.answers(sid,'pre',{'department':'TEST ONLY','age':22,'gender':e.config['pre']['questions'][2]['options'][0],'year':e.config['pre']['questions'][3]['options'][0],'leb2_frequency':e.config['pre']['questions'][4]['options'][0]})
  e.metadata(sid,{'viewport':{'screen_width':1920,'screen_height':1080},'synchronization':[]})
  for i in range(4):
   x.start(sid,'test',CHECKS);time.sleep(.02);x.end(sid,'test');x.answer(sid,0,0)
  e.answers(sid,'post',{q['id']:4 for q in e.config['post']['questions'] if q['type']=='likert'});e.step(sid,'finish')
 assert len(e.sessions)==30 and len(e.participants)==30
 z=zipfile.ZipFile(io.BytesIO(export_sessions(e,list(e.sessions))))
 required={'clicks.csv','gaze.csv','participants.csv','pre_test.csv','post_test.csv','quality_report.json','README.txt','session.json','trials.csv'}
 for s in e.sessions.values():
  prefix=f"mock/{s['participant_id']}/{s['session_id']}/"
  assert required<={n[len(prefix):] for n in z.namelist() if n.startswith(prefix)}
  assert len(list(csv.DictReader(io.StringIO(z.read(prefix+'trials.csv').decode('utf-8-sig')))))==4
  for filename in ('participants.csv','gaze.csv','clicks.csv','pre_test.csv','post_test.csv','trials.csv'):
   rows=list(csv.DictReader(io.StringIO(z.read(prefix+filename).decode('utf-8-sig'))))
   assert all(r['participant_id']==s['participant_id'] and r['session_id']==s['session_id'] for r in rows)
  assert json.loads(z.read(prefix+'quality_report.json'))['simulated'] is True

def test_default_all_export_excludes_mock_and_public_hides_serial(tmp_path):
 from backend.main import create_app
 from fastapi.testclient import TestClient
 with TestClient(create_app(tmp_path,auth_enabled=False)) as client:
  s=client.post('/api/external/quick-start',json={'track_id':'T01'}).json()
  assert zipfile.ZipFile(io.BytesIO(client.get('/api/export').content)).namelist()==[]
  assert zipfile.ZipFile(io.BytesIO(client.get('/api/export?include_demo=true').content)).namelist()
  s['calibration']={'device':{'serial':'PRIVATE','model':'Spark'}}
  assert 'PRIVATE' not in json.dumps(public_session(s))

def test_conditional_question_validation_and_hidden_answers(tmp_path):
 definition={'version':'test','questions':[{'id':'a','label':'A','type':'single','options':['yes','no']},{'id':'b','label':'B','type':'short','show_if':{'question_id':'a','equals':'yes'}}]}
 Questionnaire.model_validate(definition)
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);sid=prepare(e,x,'T01')
 for a in ('button','menu','search','status','complete'):practice_action(e,sid,a)
 s=copy.deepcopy(e.get(sid));s['snapshot']['pre']=Questionnaire.model_validate(definition).model_dump();e.commit(s)
 e.answers(sid,'pre',{'a':'no','b':'stale hidden data'})
 assert e.get(sid)['responses']['pre']['answers']=={'a':'no'}


def test_participant_cap_and_export_history_deduplication(tmp_path):
 from backend.export_history import record_export,history
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e)
 s=x.quick_start('T01');sid=s['session_id']
 for _ in range(29):e.add_participant()
 with pytest.raises(LabError):e.add_participant()
 for _ in range(2):record_export(e,[sid],export_sessions(e,[sid]))
 assert len(history(e))==1


def test_pause_resume_abort_preserves_trial_and_track(tmp_path):
 from test_external import setup
 e,x,sid=setup(tmp_path);x.start(sid,'r',CHECKS)
 paused=x.control(sid,'pause')
 assert paused['state']=='interrupted' and paused['trials'][-1]['status']=='incomplete'
 resumed=x.control(sid,'resume');assert resumed['state']=='calibration'
 aborted=x.control(sid,'abort');assert aborted['state']=='withdrawn'
 assert [a['action'] for a in aborted['audit']][-3:]==['pause','resume','abort']
 assert x.catalog('mock')['tracks'][0]['allocation_status']=='withdrawn'
 assert x.quick_start('T01')['session_id']==sid
 with pytest.raises(LabError):x.create(e.add_participant()['participant_id'],'T01')
