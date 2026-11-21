import copy,csv,io,json,time,zipfile
import pytest
from backend.engine import Engine,LabError
from backend.external import External,public_session,valid_url
from backend.models import CalibrationPoint
from backend.exporting import export_sessions

def setup(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);e.external=x
 for v in x.prototypes()['variants']:x.update(v['name'],v['url'],'verified')
 s=x.create(e.add_participant()['participant_id'],'T01');sid=s['session_id']
 e.attach(sid,'participant');e.step(sid,'information');e.step(sid,'consent');e.calibration_start(sid)
 for i in range(5):e.calibration_point(sid,CalibrationPoint(index=i,viewport={'fullscreen':True},presented_at=i))
 from backend.practice import practice_action
 if e.get(sid)['state']=='practice':
  for action in ('button','menu','search','status','complete'):practice_action(e,sid,action)
 e.answers(sid,'pre',{'department':'ข้อมูลทดสอบ','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'});e.metadata(sid,{'viewport':{'width':1440},'synchronization':[{}]})
 return e,x,sid
CHECKS=dict(starting_frame=True,display=True,fullscreen=True,hints_off=True)
def test_external_four_rounds_restart_export(tmp_path):
 e,x,sid=setup(tmp_path)
 with pytest.raises(LabError):x.create(e.add_participant()['participant_id'],'T01')
 for i,(late,quiz) in enumerate([(1,2),(2,1),(1,2),(0,0)]):
  with pytest.raises(LabError):x.start(sid,'researcher',{})
  x.start(sid,'researcher',CHECKS)
  with pytest.raises(LabError):x.start(sid,'researcher',CHECKS)
  # Losing participant focus/connection must not stop external recording.
  e.detach(sid,'participant');time.sleep(.04);e.tick();assert e.active==sid
  x.end(sid,'researcher')
  with pytest.raises(LabError):x.end(sid,'researcher')
  assert e.get(sid)['task_index']==i
  with pytest.raises(LabError):x.answer(sid,None,0)
  x.answer(sid,late,quiz)
 x.amend(sid,e.get(sid)['trials'][-1]['trial_id'],2,1,'correct transcription')
 assert e.get(sid)['audit'][-1]['previous_trial']['decision_error']==1
 assert e.get(sid)['state']=='post'
 assert [t['decision_error'] for t in e.get(sid)['trials']]==[0,0,0,0]
 e.answers(sid,'post',{q['id']:4 for q in e.get(sid)['snapshot']['post']['questions'] if q['type']=='likert'});e.step(sid,'finish')
 restarted=Engine(tmp_path,tmp_path/'configuration.json')
 archive=zipfile.ZipFile(io.BytesIO(export_sessions(restarted,[sid])))
 rows=list(csv.DictReader(io.StringIO(archive.read(next(n for n in archive.namelist() if n.endswith('/rounds.csv'))).decode('utf-8-sig'))))
 assert len(rows)==4 and all(r['figma_events']=='unavailable' and r['start_trigger']=='researcher_manual' for r in rows)
 visible=json.dumps(public_session(e.get(sid)))
 assert 'expected_late' not in visible and 'expected_quiz' not in visible and 'expected_quiz' not in visible

def test_external_watchdog_reset_and_recovery(tmp_path):
 e,x,sid=setup(tmp_path);x.start(sid,'r',CHECKS)
 x.controllers[sid]['heartbeat']=time.monotonic()-16;e.tick()
 assert e.get(sid)['state']=='interrupted'
 e.step(sid,'resume');e.attach(sid,'participant');e.calibration_start(sid)
 for i in range(5):e.calibration_point(sid,CalibrationPoint(index=i,viewport={'fullscreen':True},presented_at=i))
 x.start(sid,'r',CHECKS);x.end(sid,'r');x.reset(sid,'wrong starting frame')
 assert len(e.get(sid)['trials'])==2 and e.get(sid)['audit'][-1]['reason']=='wrong starting frame'
 x.start(sid,'r',CHECKS)
 e.devices['mock'].stop()
 restarted=Engine(tmp_path,tmp_path/'configuration.json')
 assert restarted.get(sid)['trials'][-1]['status']=='incomplete'
 assert restarted.get(sid)['trials'][-1]['ended_us'] is None

@pytest.mark.parametrize('url',['https://evil.com/proto/x/a?node-id=1','http://www.figma.com/proto/x/a?node-id=1','https://www.figma.com/design/x/a?node-id=1','https://www.figma.com.evil.com/proto/x/a?node-id=1'])
def test_external_url_restriction(url):
 with pytest.raises(LabError):valid_url(url)

def test_external_api_roles_and_no_answer_key(tmp_path,monkeypatch):
 from fastapi.testclient import TestClient
 from backend.main import create_app
 monkeypatch.setenv('EYETRACK_RESEARCHER_PASSWORD','external-test-password')
 app=create_app(tmp_path)
 with TestClient(app) as c:
  token=c.post('/api/auth/login',json={'password':'external-test-password'}).json()['token'];headers={'Authorization':'Bearer '+token}
  assert c.get('/api/prototypes').status_code==401
  for v in c.get('/api/prototypes',headers=headers).json()['variants']:
   assert c.put('/api/prototypes',headers=headers,json={'name':v['name'],'url':v['url'],'status':'verified'}).status_code==200
  pid=c.post('/api/participants',headers=headers).json()['participant_id']
  s=c.post('/api/external/sessions',headers=headers,json={'participant_id':pid,'track_id':'T02'}).json();sid=s['session_id']
  assert s['task_mode']=='figma_external'
  link=c.post(f'/api/sessions/{sid}/participant-link',headers=headers).json()['path'];pt=link.split('#access=')[1];participant={'Authorization':'Bearer '+pt}
  assert c.get('/api/prototypes',headers=participant).status_code==403
  assert c.post(f'/api/external/{sid}/start',headers=participant,json=CHECKS).status_code==403
  data=c.get(f'/api/sessions/{sid}',headers=participant).json()
  assert 'external' not in data and 'condition' not in data
  assert 'expected_late' not in json.dumps(data)
  with c.websocket_connect(f'/ws/sessions/{sid}?role=participant&client=p',subprotocols=['eyetrack',pt]) as ws:
   value=ws.receive_json();assert 'expected_quiz' not in json.dumps(value)
  assert c.post(f'/api/external/{sid}/release',headers=headers,json={'reason':''}).status_code==422
  assert c.post(f'/api/external/{sid}/release',headers=headers,json={'reason':'test cancellation'}).status_code==200
  assert c.get('/api/tracks',headers=headers).json()['tracks'][1]['allocation_status']=='available'


def test_quick_start_reopens_same_person_without_duplicate_allocation(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);e.external=x
 first=x.quick_start('T03');second=x.quick_start('T03')
 assert first['session_id']==second['session_id']
 assert len(e.participants)==1 and len(e.sessions)==1
 public=public_session(first)
 assert public['external_task']['prototype_url'].startswith('https://www.figma.com/proto/')
 assert 'expected_late' not in json.dumps(public)
 assert len(public['tasks'])==4

def test_end_round_persists_answer_boundary_atomically(tmp_path,monkeypatch):
 e,x,sid=setup(tmp_path);x.start(sid,'r',CHECKS)
 states=[];original=e.storage.save
 def save(s):
  states.append((s['state'],s['task_index']))
  return original(s)
 monkeypatch.setattr(e.storage,'save',save)
 x.end(sid,'r')
 assert states and all(state=='external_answers' and index==0 for state,index in states)
 restarted=Engine(tmp_path,tmp_path/'configuration.json')
 assert restarted.get(sid)['state']=='external_answers' and restarted.get(sid)['task_index']==0

def test_external_create_validates_before_allocating_session(tmp_path,monkeypatch):
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);e.external=x
 pid=e.add_participant()['participant_id']
 monkeypatch.setattr(x,'prototypes',lambda:{'variants':[]})
 with pytest.raises(LabError):x.create(pid,'T01')
 assert not e.sessions

def test_external_start_after_all_rounds_returns_conflict(tmp_path):
 e,x,sid=setup(tmp_path)
 s=copy.deepcopy(e.get(sid));s['task_index']=4;s['state']='post';e.commit(s)
 with pytest.raises(LabError):x.start(sid,'r',CHECKS)

def test_updated_url_node_id_is_snapshotted_consistently(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);e.external=x
 v=x.prototypes()['variants'][0]
 updated=v['url'].replace('node-id=888-87148','node-id=123-456')
 x.update(v['name'],updated,'verified')
 s=x.quick_start('T01')
 assert s['external']['rounds'][0]['starting_node_id']=='123-456'
 assert s['external']['rounds'][0]['prototype_url']==updated

def test_one_click_returns_scoped_participant_link_without_storing_token(tmp_path,monkeypatch):
 from fastapi.testclient import TestClient
 from backend.main import create_app
 monkeypatch.setenv('EYETRACK_RESEARCHER_PASSWORD','one-click-test')
 with TestClient(create_app(tmp_path)) as c:
  token=c.post('/api/auth/login',json={'password':'one-click-test'}).json()['token'];admin={'Authorization':'Bearer '+token}
  response=c.post('/api/external/quick-start',headers=admin,json={'track_id':'T05'})
  assert response.status_code==200
  s=response.json();sid=s['session_id'];path=s['participant_path']
  assert path.startswith('/participant/'+sid+'#access=')
  participant={'Authorization':'Bearer '+path.split('#access=')[1]}
  public=c.get('/api/sessions/'+sid,headers=participant)
  assert public.status_code==200
  assert 'participant_path' not in public.json() and 'expected_late' not in public.text
  assert c.post('/api/external/quick-start',headers=participant,json={'track_id':'T06'}).status_code==403
  again=c.post('/api/external/quick-start',headers=admin,json={'track_id':'T05'}).json()
  assert again['session_id']==sid
  assert len(c.get('/api/participants',headers=admin).json())==1
  assert len(s['tasks'])==4 and len(s['snapshot']['pre']['questions'])==5 and len(s['snapshot']['post']['questions'])==27
