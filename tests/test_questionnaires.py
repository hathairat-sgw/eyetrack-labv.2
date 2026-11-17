import copy,json,io,zipfile,csv
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.engine import Engine,LabError
from backend.models import Config,CreateSession
from backend.exporting import export_sessions

ROOT=Path(__file__).resolve().parents[1]
PRE={'department':'เทคโนโลยีมีเดีย','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'}
def setup_engine(tmp_path):
    engine=Engine(tmp_path,tmp_path/'configuration.json')
    config=copy.deepcopy(engine.config);config.update(json.loads((ROOT/'config/questionnaires-irb.json').read_text(encoding='utf-8')))
    engine.update_config(Config.model_validate(config))
    pid=engine.add_participant()['participant_id']
    sid=engine.create(CreateSession(participant_id=pid,task_ids=['demo-find']))['session_id']
    legacy=copy.deepcopy(engine.get(sid));legacy.pop('workflow_version',None);engine.commit(legacy)
    engine.step(sid,'information');engine.step(sid,'consent')
    return engine,sid

def test_source_sections_and_duplicates():
    q=json.loads((ROOT/'config/questionnaires-irb.json').read_text(encoding='utf-8'))
    assert len(q['pre']['questions'])==5
    post=q['post']['questions'];assert len(post)==27
    assert [sum(x['id'].startswith(f'post_{i}_') for x in post) for i in range(1,5)]==[6]*4
    assert post[4]['label'][4:]==post[10]['label'][4:]
    assert 'เหมือนเดิมปแบบภาพ' in post[23]['label']
    assert len(q['post']['scale_labels'])==5

def test_draft_restart_validation_duplicate_and_export(tmp_path):
    e,sid=setup_engine(tmp_path)
    draft=e.save_draft(sid,'pre',{'department':'เทคโนโลยีมีเดีย'},0)
    with pytest.raises(LabError):e.save_draft(sid,'pre',{},0)
    e=Engine(tmp_path,tmp_path/'configuration.json')
    assert e.get(sid)['drafts']['pre']==draft
    with pytest.raises(LabError):e.answers(sid,'pre',{'age':22})
    with pytest.raises(LabError):e.answers(sid,'pre',{**PRE,'age':-1})
    e.answers(sid,'pre',PRE)
    original=copy.deepcopy(e.get(sid)['responses']['pre'])
    with pytest.raises(LabError):e.answers(sid,'pre',PRE)
    with pytest.raises(LabError):e.save_draft(sid,'pre',PRE,1)
    assert e.get(sid)['responses']['pre']==original
    assert 'pre' not in e.get(sid)['drafts']
    # Isolate the post form boundary; full mock lifecycle is covered by test_research.
    s=copy.deepcopy(e.get(sid));s['state']='post';e.commit(s)
    answers={q['id']:4 for q in s['snapshot']['post']['questions'] if q['type']=='likert'}
    answers.update(open_1='ภาษาไทย, comma\nnewline',open_2='',open_3='')
    e.save_draft(sid,'post',answers,0);e.answers(sid,'post',answers)
    archive=zipfile.ZipFile(io.BytesIO(export_sessions(e,[sid])))
    for phase,count in [('pre',5),('post',27)]:
        name=next(n for n in archive.namelist() if n.endswith(f'/{phase}_test.csv'))
        rows=list(csv.DictReader(io.StringIO(archive.read(name).decode('utf-8-sig'))))
        assert len(rows)==count
        assert all(r['session_id']==sid and r['submitted_at'] for r in rows)
    stored=json.loads(archive.read(next(n for n in archive.namelist() if n.endswith('/session.json'))))
    assert stored['responses']['post']['answers']==answers
    assert stored['responses']['pre']['answers']==PRE

def test_role_access_and_drafts(tmp_path,monkeypatch):
    monkeypatch.setenv('EYETRACK_RESEARCHER_PASSWORD','test-password-only')
    app=create_app(tmp_path)
    with TestClient(app) as c:
        assert c.get('/api/sessions').status_code==401
        assert c.post('/api/auth/login',json={'password':'wrong'}).status_code==401
        token=c.post('/api/auth/login',json={'password':'test-password-only'}).json()['token']
        admin={'Authorization':'Bearer '+token}
        # Use actual application's engine for HTTP checks.
        eng=app.state.engine
        cfg=copy.deepcopy(eng.config);cfg.update(json.loads((ROOT/'config/questionnaires-irb.json').read_text(encoding='utf-8')));eng.update_config(Config.model_validate(cfg))
        pid=c.post('/api/participants',headers=admin).json()['participant_id']
        sid=c.post('/api/sessions',headers=admin,json={'participant_id':pid,'task_ids':['demo-find']}).json()['session_id']
        link=c.post(f'/api/sessions/{sid}/participant-link',headers=admin).json()['path']
        participant={'Authorization':'Bearer '+link.split('#access=')[1]}
        assert c.get(f'/api/sessions/{sid}',headers=participant).status_code==200
        for path in ['/api/sessions','/api/export',f'/api/sessions/{sid}/results',f'/api/sessions/{sid}/export','/api/sessions/Sother']:
            assert c.get(path,headers=participant).status_code==403
        assert c.post(f'/api/sessions/{sid}/participant-link',headers=participant).status_code==403
        assert c.put(f'/api/sessions/{sid}/drafts/pre',headers=participant,json={'answers':{},'revision':0}).status_code==409
        legacy=copy.deepcopy(eng.get(sid));legacy.pop('workflow_version',None);eng.commit(legacy)
        for action in ['information','consent']:assert c.post(f'/api/sessions/{sid}/step/{action}',headers=participant).status_code==200
        assert c.put(f'/api/sessions/{sid}/drafts/pre',headers=participant,json={'answers':PRE,'revision':0}).status_code==200
        assert c.post(f'/api/sessions/{sid}/answers/pre',headers=participant,json={'answers':PRE}).status_code==200
        assert c.post(f'/api/sessions/{sid}/answers/pre',headers=participant,json={'answers':PRE}).status_code==409
        assert c.get(f'/api/sessions/{sid}/export',headers=admin).status_code==200
        with c.websocket_connect(f'/ws/sessions/{sid}?role=participant&client=test',subprotocols=['eyetrack',link.split('#access=')[1]]) as ws:
            assert 'session' in ws.receive_json()


def test_full_mock_with_irb_forms(tmp_path):
    from backend.models import CalibrationPoint,Event
    e,sid=setup_engine(tmp_path)
    e.attach(sid,'test');e.answers(sid,'pre',PRE)
    e.calibration_start(sid)
    for index in range(5):e.calibration_point(sid,CalibrationPoint(index=index,viewport={'fullscreen':True},presented_at=100+index))
    e.metadata(sid,{'viewport':{'width':1440,'height':900},'synchronization':[{'offset_us':0,'uncertainty_us':1}]})
    e.start_trial(sid,'test')
    t=e.get(sid)['trials'][-1]
    e.events(sid,'test',[Event(event_id='one',event_type='click',trial_id=t['trial_id'],timestamp=123,page_url='http://localhost/stimuli/demo',target_element_id='course-research')])
    e.complete_trial(sid,'test')
    assert e.get(sid)['state']=='post'
    a={q['id']:3 for q in e.get(sid)['snapshot']['post']['questions'] if q['type']=='likert'}
    e.answers(sid,'post',a);e.step(sid,'finish')
    assert e.get(sid)['state']=='completed'
    restarted=Engine(tmp_path,tmp_path/'configuration.json')
    assert restarted.get(sid)['responses']['pre']['answers']==PRE
    assert export_sessions(restarted,[sid])
