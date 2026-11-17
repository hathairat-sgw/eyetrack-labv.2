import io,json,zipfile
import pytest
from backend.engine import Engine,LabError
from backend.external import External
from backend.video import Video
from backend.exporting import export_sessions

def ready(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');x=External(e);s=x.quick_start('T01');sid=s['session_id'];e.get(sid)['consent']={'accepted':True};e.get(sid)['state']='instructions';e.commit(e.get(sid))
 return e,Video(e),sid

def test_video_order_deduplication_export_and_restart(tmp_path):
 e,v,sid=ready(tmp_path);cap=v.start(sid,{'browser_started_ms':123});cid=cap['capture_id']
 with pytest.raises(LabError):v.start(sid,{})
 with pytest.raises(LabError):v.chunk(sid,cid,1,b'chunk')
 v.chunk(sid,cid,0,b'WEBM-TEST-HEADER');v.chunk(sid,cid,0,b'WEBM-TEST-HEADER')
 with pytest.raises(LabError):v.chunk(sid,cid,0,b'changed')
 with pytest.raises(LabError):export_sessions(e,[sid])
 v.chunk(sid,cid,1,b'WEBM-TEST-END')
 assert v.finish(sid,cid,{'complete':True})['status']=='completed'
 z=zipfile.ZipFile(io.BytesIO(export_sessions(e,[sid])))
 assert z.read(next(n for n in z.namelist() if n.endswith('/video/'+cid+'.webm')))==b'WEBM-TEST-HEADERWEBM-TEST-END'
 assert Engine(tmp_path,tmp_path/'configuration.json').get(sid)['videos'][0]['status']=='completed'

def test_video_incomplete_and_consent_guards(tmp_path):
 e,v,sid=ready(tmp_path);e.get(sid)['consent']=None
 with pytest.raises(LabError):v.start(sid,{})
 e.get(sid)['consent']={'accepted':True};cap=v.start(sid,{})
 restarted=Engine(tmp_path,tmp_path/'configuration.json')
 assert restarted.get(sid)['videos'][0]['status']=='incomplete'
 z=zipfile.ZipFile(io.BytesIO(export_sessions(restarted,[sid])))
 assert any(n.endswith('.webm.part') for n in z.namelist())

def test_video_write_failure_not_reported_success(tmp_path):
 e,v,sid=ready(tmp_path);cap=v.start(sid,{});cid=cap['capture_id']
 path=e.storage.session_path(e.get(sid))/(cid+'.webm.part');path.write_bytes(b'uncommitted')
 with pytest.raises(LabError):v.chunk(sid,cid,0,b'data')
 assert v.finish(sid,cid,{'complete':True})['status']=='incomplete'

def test_participant_cannot_control_or_read_researcher_stream(tmp_path):
 from fastapi.testclient import TestClient
 from backend.main import create_app
 from backend.access import Access
 app=create_app(tmp_path)
 with TestClient(app) as client:
  x=app.state.engine.external;s=x.quick_start('T01');sid=s['session_id'];token=Access(tmp_path).issue('participant',sid)
  headers={'Authorization':'Bearer '+token}
  assert client.get('/api/sessions/'+sid+'/stream-status',headers=headers).status_code==403
  assert client.post('/api/sessions/'+sid+'/video/start',headers=headers,json={}).status_code==403


def test_video_export_rejects_changed_file(tmp_path):
 e,v,sid=ready(tmp_path);cap=v.start(sid,{});cid=cap['capture_id'];v.chunk(sid,cid,0,b'original');v.finish(sid,cid,{'complete':True})
 (e.storage.session_path(e.get(sid))/(cid+'.webm')).write_bytes(b'changed!')
 with pytest.raises(ValueError):export_sessions(e,[sid])
