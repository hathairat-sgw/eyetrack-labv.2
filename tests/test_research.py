from pathlib import Path
import copy
import csv
import io
import json
import time
import zipfile
import pytest
from fastapi.testclient import TestClient
from backend.engine import Engine, LabError
from backend.models import CreateSession, CalibrationPoint, Event, Config
from backend.exporting import export_sessions
from backend.main import create_app

@pytest.fixture
def lab(tmp_path):
    (tmp_path / "config.json").write_text((Path(__file__).parent / "fixtures/demo-config.json").read_text(encoding="utf-8"), encoding="utf-8")
    engine = Engine(tmp_path / "data", tmp_path / "config.json")
    yield engine
    for device in engine.devices.values():
        device.stop()

def session(lab, **kwargs):
    p = lab.add_participant()
    created=lab.create(CreateSession(participant_id=p["participant_id"],task_ids=["demo-find","demo-resource"],**kwargs))
    created.pop("workflow_version",None)
    lab.commit(created)
    return created["session_id"]

def ready(lab, sid):
    lab.attach(sid, "client")
    lab.step(sid, "information")
    lab.step(sid, "consent")
    lab.answers(sid, "pre", {"experience":"เคย","frequency":3} if lab.get(sid)["snapshot"]["pre"]["version"]=="demo-1" else {'department':'ข้อมูลทดสอบ','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
    calibrate(lab, sid)
    lab.metadata(sid, {"viewport":{"width":1440,"height":900}, "synchronization":[{"offset_us":10,"uncertainty_us":20}]})

def calibrate(lab, sid):
    lab.calibration_start(sid)
    for index in range(5):
        lab.calibration_point(sid, CalibrationPoint(index=index,viewport={"fullscreen":True},presented_at=100+index))
    assert lab.get(sid)["calibration"]["success"]

def event(lab, sid, target=None, event_id="click-1"):
    s = lab.get(sid)
    return Event(event_id=event_id, event_type="click", trial_id=s["trials"][-1]["trial_id"],
        timestamp=123.45, client_x=50, client_y=100, page_url="http://localhost:5173/stimuli/demo",
        target_element_id=target or s["tasks"][s["task_index"]]["target"])

def test_complete_mock_and_restart(lab):
    sid = session(lab)
    ready(lab,sid)
    for index in range(2):
        lab.start_trial(sid,"client")
        time.sleep(.06)
        lab.tick()
        lab.events(sid,"client",[event(lab,sid,event_id=str(index))])
        lab.complete_trial(sid,"client")
    lab.answers(sid,"post",{"ease":4,"feedback":"ทดสอบ, ภาษาไทย\nบรรทัดใหม่"})
    lab.step(sid,"finish")
    assert lab.get(sid)["state"] == "completed"
    archive = zipfile.ZipFile(io.BytesIO(export_sessions(lab,[sid])))
    assert len(archive.namelist()) == 9
    assert any(n.endswith("/quality_report.json") for n in archive.namelist())
    gaze_name = next(n for n in archive.namelist() if n.endswith("/gaze.csv"))
    gaze = list(csv.DictReader(io.StringIO(archive.read(gaze_name).decode("utf-8-sig"))))
    assert len(gaze) >= 2
    assert {r["mode"] for r in gaze} == {"mock"}
    assert len({r["trial_id"] for r in gaze}) == 2
    for name in archive.namelist():
        if name.endswith(".csv"):
            rows = list(csv.DictReader(io.StringIO(archive.read(name).decode("utf-8-sig"))))
            assert all(r["session_id"] == sid for r in rows)
    reload = Engine(lab.storage.root, lab.config_path)
    assert reload.get(sid)["state"] == "completed"
    assert reload.get(sid)["responses"]["post"]["answers"]["feedback"].endswith("บรรทัดใหม่")

def test_consent_and_required_validation(lab):
    sid = session(lab)
    lab.attach(sid,"client")
    with pytest.raises(LabError):
        lab.start_trial(sid,"client")
    with pytest.raises(LabError):
        lab.metadata(sid,{})
    lab.step(sid,"information")
    lab.step(sid,"consent")
    with pytest.raises(LabError):
        lab.answers(sid,"pre",{"frequency":3})
    with pytest.raises(LabError):
        lab.answers(sid,"pre",{"experience":"เคย","frequency":"3"})
    assert lab.get(sid)["state"] == "pre"
    assert lab.storage.rows(lab.get(sid),"clicks") == []

def test_one_recording_duplicate_and_client(lab):
    sid = session(lab); ready(lab,sid)
    with pytest.raises(LabError):
        lab.attach(sid,"second-window")
    lab.start_trial(sid,"client")
    with pytest.raises(LabError):
        lab.start_trial(sid,"client")
    with pytest.raises(LabError):
        lab.events(sid,"wrong",[event(lab,sid)])
    with pytest.raises(LabError):
        lab.complete_trial(sid,"client")
    click = event(lab,sid)
    lab.events(sid,"client",[click,click])
    assert len(lab.storage.rows(lab.get(sid),"clicks")) == 1
    with pytest.raises(LabError):
        export_sessions(lab,[sid])
    lab.stop(sid)

def test_disconnect_resume_new_trial(lab):
    sid = session(lab); ready(lab,sid)
    lab.start_trial(sid,"client")
    tid = lab.get(sid)["trials"][-1]["trial_id"]
    lab.detach(sid,"client")
    assert lab.get(sid)["state"] == "interrupted"
    assert lab.get(sid)["trials"][-1]["status"] == "incomplete"
    lab.attach(sid,"new")
    lab.step(sid,"resume")
    calibrate(lab,sid)
    lab.start_trial(sid,"new")
    assert lab.get(sid)["trials"][-1]["trial_id"] != tid
    assert lab.get(sid)["task_index"] == 0
    lab.stop(sid,"withdraw",True)
    with pytest.raises(LabError):
        lab.step(sid,"resume")
    assert lab.active is None

def test_seed_and_snapshot(lab):
    sid1=session(lab,order="random",seed=123)
    sid2=session(lab,order="random",seed=123)
    assert lab.get(sid1)["tasks"] == lab.get(sid2)["tasks"]
    original=copy.deepcopy(lab.get(sid1)["snapshot"])
    updated=copy.deepcopy(lab.config)
    updated["pre"]["version"]="2"
    lab.update_config(Config.model_validate(updated))
    assert lab.get(sid1)["snapshot"] == original

def test_timeout_and_heartbeat(lab):
    sid=session(lab);ready(lab,sid);lab.start_trial(sid,"client")
    lab.clients[sid]["heartbeat"] -= 10
    lab.tick()
    assert lab.get(sid)["interruption"] == "heartbeat_timeout"

def test_time_limit(lab):
    sid=session(lab);ready(lab,sid);lab.start_trial(sid,"client")
    lab.get(sid)["trials"][-1]["started_us"] -= 121_000_000
    lab.tick()
    assert lab.get(sid)["trials"][-1]["reason"] == "time_limit"
    assert lab.get(sid)["task_index"] == 1

def test_csv_corruption_rejected(lab):
    sid=session(lab)
    path=lab.storage.session_path(lab.get(sid))/"gaze.csv"
    with path.open("a",encoding="utf-8") as stream: stream.write("incomplete\n")
    with pytest.raises(ValueError):
        export_sessions(lab,[sid])

def test_disk_failure_stops_device(lab, monkeypatch):
    sid=session(lab);ready(lab,sid);lab.start_trial(sid,"client")
    def fail(*args,**kwargs): raise OSError("disk full")
    monkeypatch.setattr(lab.storage,"append",fail)
    time.sleep(.04)
    lab.tick()
    assert lab.active is None
    assert lab.fatal_error == "disk full"
    assert lab.get(sid)["state"] == "interrupted"

def test_calibration_order_and_failure(lab, monkeypatch):
    sid=session(lab);lab.attach(sid,"client");lab.step(sid,"information");lab.step(sid,"consent");lab.answers(sid,"pre",{"experience":"เคย","frequency":3})
    lab.calibration_start(sid)
    with pytest.raises(LabError):
        lab.calibration_point(sid,CalibrationPoint(index=2,viewport={},presented_at=1))
    monkeypatch.setattr(lab.devices["mock"],"collect",lambda x,y:{"success":False,"sdk_status":"mock failure"})
    lab.calibration_point(sid,CalibrationPoint(index=0,viewport={},presented_at=1))
    assert lab.get(sid)["state"] == "calibration"
    assert not lab.get(sid)["calibration"]["success"]

def test_hardware_not_faked(lab):
    p=lab.add_participant()
    with pytest.raises(LabError):
        lab.create(CreateSession(participant_id=p["participant_id"],mode="hardware",task_ids=["demo-find"]))
    status=lab.devices["hardware"].status()
    assert status["simulated"] is False

def test_http_validation_and_websocket_disconnect(tmp_path):
    app=create_app(tmp_path/"api-data", auth_enabled=False)
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        p=client.post("/api/participants").json()
        s=client.post("/api/sessions",json={"participant_id":p["participant_id"],"task_ids":["demo-find"]}).json()
        sid=s["session_id"]
        assert client.post("/api/sessions/"+sid+"/events",json={"events":[]}).status_code == 409
        assert client.post("/api/participants",headers={"Origin":"https://evil.example"}).status_code == 403
        with client.websocket_connect("/ws/sessions/"+sid+"?role=participant&client=test") as ws:
            assert ws.receive_json()["session"]["state"] == "information"
            ws.send_json({"type":"heartbeat"})
            assert ws.receive_json()["session"]["session_id"] == sid
        deadline = time.monotonic() + 2
        while sid in app.state.engine.clients and time.monotonic() < deadline:
            time.sleep(.01)
        assert sid not in app.state.engine.clients

def test_restart_marks_unfinished_trial(lab):
    sid=session(lab);ready(lab,sid);lab.start_trial(sid,"client")
    lab.devices["mock"].stop()
    reload=Engine(lab.storage.root,lab.config_path)
    assert reload.get(sid)["state"] == "interrupted"
    assert reload.get(sid)["trials"][-1]["ended_us"] is None


def test_random_targets_and_unknown_route(lab):
    config=copy.deepcopy(lab.config)
    for t in config["tasks"]:
        t["targets"]=["course-research","resource-guide"]
    lab.update_config(Config.model_validate(config))
    a=session(lab,random_targets=True,seed=12)
    b=session(lab,random_targets=True,seed=12)
    assert [t["target"] for t in lab.get(a)["tasks"]] == [t["target"] for t in lab.get(b)["tasks"]]
    config["tasks"][0]["route"]="/stimuli/unimplemented"
    lab.update_config(Config.model_validate(config))
    with pytest.raises(LabError,match="Stimulus"):
        session(lab)

def test_calibration_exception_is_saved_as_failure(lab,monkeypatch):
    sid=session(lab);lab.attach(sid,"client")
    lab.step(sid,"information");lab.step(sid,"consent")
    lab.answers(sid,"pre",{"experience":"เคย","frequency":3})
    lab.calibration_start(sid)
    def broken(x,y):raise RuntimeError("device failure")
    monkeypatch.setattr(lab.devices["mock"],"collect",broken)
    result=lab.calibration_point(sid,CalibrationPoint(index=0,viewport={},presented_at=1))
    assert result["state"] == "calibration"
    assert result["calibration"]["success"] is False
    assert result["calibration"]["points"][0]["error"] == "device failure"
    assert lab.calibrating is None

def test_http_disk_error_is_visible_and_stops(tmp_path,monkeypatch):
    app=create_app(tmp_path/"fail-data", auth_enabled=False)
    with TestClient(app,raise_server_exceptions=False) as client:
        engine=app.state.engine
        sid=session(engine);ready(engine,sid);engine.start_trial(sid,"client")
        def fail(*args,**kwargs):raise OSError("No space")
        monkeypatch.setattr(engine.storage,"append",fail)
        response=client.post("/api/sessions/"+sid+"/events",json={"events":[event(engine,sid).model_dump()]},headers={"X-Participant-Client":"client"})
        assert response.status_code == 507
        assert "No space" in response.json()["detail"]
        assert engine.active is None

def test_export_rejects_unknown_trial(lab):
    sid=session(lab);ready(lab,sid);lab.start_trial(sid,"client")
    click=event(lab,sid)
    lab.events(sid,"client",[click]);lab.complete_trial(sid,"client")
    path=lab.storage.session_path(lab.get(sid))/"clicks.csv"
    data=path.read_text(encoding="utf-8-sig").replace(click.trial_id,"Tunknown")
    path.write_text(data,encoding="utf-8-sig")
    with pytest.raises(ValueError,match="Unknown trial"):
        export_sessions(lab,[sid])

def test_second_backend_does_not_recover_active_session(tmp_path):
    data=tmp_path/"locked"
    app=create_app(data)
    with TestClient(app):
        engine=app.state.engine
        sid=session(engine);ready(engine,sid);engine.start_trial(sid,"client")
        second=create_app(data)
        with pytest.raises((RuntimeError,OSError)):
            with TestClient(second):
                pass
        assert json.loads((engine.storage.session_path(engine.get(sid))/"session.json").read_text(encoding="utf-8"))["state"] == "recording"
        engine.stop(sid)

def test_clock_metadata_link(lab):
    sid=session(lab);ready(lab,sid);lab.start_trial(sid,"client")
    saved=lab.get(sid)
    trial=saved["trials"][-1]
    assert saved["metadata"][trial["metadata_index"]]["clock_segment_id"] == trial["clock_segment_id"]
    lab.stop(sid)

