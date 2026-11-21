import asyncio
import copy
import os
import time
import re
import json
from .external import External, public_session
from .video import Video
from .validation import Validation
from .models import ExternalSessionRequest
from .access import Access
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from .engine import Engine, LabError, now_us
from .exporting import export_sessions
from .models import Config, CreateSession, Events, Answers, DraftAnswers, Metadata, CalibrationPoint
from .storage import read_json

ROOT = Path(__file__).resolve().parent.parent

def create_app(data_root=None, auth_enabled=True):
    root = Path(data_root or os.environ.get("EYETRACK_DATA_DIR", ROOT / "data"))
    engine = Engine(root, root / "configuration.json", recover=False)

    video = Video(engine)
    validation = Validation(engine)
    external = External(engine)
    engine.external = external
    access = None

    @asynccontextmanager
    async def lifespan(app):
        nonlocal access
        access = Access(root) if auth_enabled else None
        lock_file = (root / ".backend.lock").open("a+b")
        lock_file.seek(0)
        lock_file.write(b"0")
        lock_file.flush()
        lock_file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lock_file.close()
            raise RuntimeError("Another backend owns this data directory. Use one worker.")
        engine.sessions = engine.storage.load_all()
        engine.recover()
        async def monitor():
            while True:
                await asyncio.sleep(0.05)
                await asyncio.to_thread(engine.tick)
        task = asyncio.create_task(monitor())
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            with engine.lock:
                if engine.active:
                    engine.stop(engine.active, "backend_shutdown")
                if engine.calibrating:
                    engine.stop(engine.calibrating, "backend_shutdown")
            lock_file.close()

    app = FastAPI(title="EyeTrack Lab", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    if os.environ.get("EYETRACK_FRONTEND_PORT"):
        origins.append("http://127.0.0.1:" + str(int(os.environ["EYETRACK_FRONTEND_PORT"])))
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PUT"], allow_headers=["Content-Type", "X-Participant-Client"])

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and origin not in origins:
            return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
        return await call_next(request)

    @app.middleware("http")
    async def authorize(request: Request, call_next):
        path = request.url.path
        identity = None
        if access and path.startswith("/api/") and path not in ("/api/health", "/api/clock", "/api/auth/login") and request.method != "OPTIONS":
            token = request.headers.get("authorization", "").removeprefix("Bearer ")
            identity = access.verify(token)
            if not identity:
                return JSONResponse({"detail": "กรุณาเข้าสู่ระบบ หรือใช้ลิงก์ session ที่ได้รับ"}, status_code=401)
            if identity["role"] != "researcher":
                prefix = "/api/sessions/" + identity["sid"]
                suffix = path[len(prefix):] if path.startswith(prefix) else None
                allowed = (request.method == "GET" and suffix == "") or (request.method in ("POST", "PUT") and suffix is not None and re.fullmatch(r"/(?:practice/(?:button|menu|search|status|complete)|answers/(?:pre|post)|drafts/(?:pre|post)|metadata|calibration/(?:start|point)|validation/(?:start|point)|trials/(?:start|complete)|events|stop|withdraw|step/(?:information|consent|resume|finish))", suffix))
                if not allowed:
                    return JSONResponse({"detail": "บทบาทนี้ไม่มีสิทธิ์เข้าถึงข้อมูลนี้"}, status_code=403)
        response = await call_next(request)
        if identity and identity["role"] == "participant" and "application/json" in response.headers.get("content-type", ""):
            body = b"".join([chunk async for chunk in response.body_iterator])
            data = json.loads(body)
            if isinstance(data, dict) and "session_id" in data:data = public_session(data)
            return JSONResponse(data, status_code=response.status_code)
        return response

    @app.post("/api/auth/login")
    async def login(request: Request):
        body = await request.json()
        token = access.login(body.get("password"), request.client.host) if access else "test-only"
        if not token:
            return JSONResponse({"detail": "รหัสไม่ถูกต้อง หรือพยายามเกินจำนวน กรุณารอ 1 นาที"}, status_code=401)
        return {"token": token, "role": "researcher"}

    @app.post("/api/sessions/{sid}/participant-link")
    def participant_link(sid: str):
        engine.get(sid)
        return {"path": "/participant/" + sid + "#access=" + (access.issue("participant", sid) if access else "test-only")}

    @app.exception_handler(LabError)
    async def lab_error(request, error):
        return JSONResponse({"detail": error.message}, status_code=error.code)

    @app.exception_handler(OSError)
    async def disk_error(request, error):
        engine.fail_closed(error)
        return JSONResponse({"detail": "บันทึกไฟล์ไม่สำเร็จ ระบบหยุดการบันทึก: " + str(error)}, status_code=507)

    @app.exception_handler(ValueError)
    async def invalid_data(request, error):
        return JSONResponse({"detail": "ข้อมูลไม่ผ่านการตรวจ: " + str(error)}, status_code=422)

    @app.exception_handler(RuntimeError)
    async def runtime_error(request, error):
        engine.fail_closed(error)
        return JSONResponse({"detail": str(error)}, status_code=503)

    @app.get("/api/health")
    def health():
        return {"ok": not bool(engine.fatal_error), "error": engine.fatal_error, "recording": engine.active, "calibrating": engine.calibrating}

    @app.get("/api/clock")
    def clock():
        return {"backend_us": now_us(), "unit": "microseconds", "origin": "perf_counter", "clock_segment_id": engine.clock_segment_id, "utc_ms": time.time() * 1000}

    @app.get("/api/config")
    def config():
        return engine.config

    @app.put("/api/config")
    def config_update(value: Config):
        return engine.update_config(value)

    @app.get("/api/questionnaire-template")
    def questionnaire_template():
        return read_json(ROOT / "config" / "questionnaires-irb.json")

    @app.put("/api/sessions/{sid}/drafts/{phase}")
    def save_draft(sid: str, phase: str, value: DraftAnswers):
        return engine.save_draft(sid, phase, value.answers, value.revision)

    @app.get("/api/prototypes")
    def prototypes(): return external.prototypes()

    @app.put("/api/prototypes")
    def prototype_update(value: dict): return external.update(value.get("name"), value.get("url", ""), value.get("status"))

    @app.post("/api/external/quick-start")
    def external_quick_start(value: ExternalSessionRequest):
        session = external.quick_start(value.track_id,value.mode,value.validation_limits.model_dump(),value.native_mouse)
        sid = session["session_id"]
        return {**session, "participant_path": "/participant/" + sid + "#access=" + (access.issue("participant",sid) if access else "test-only")}

    @app.post("/api/external/sessions")
    def external_create(value: ExternalSessionRequest): return external.create(value.participant_id, value.track_id,value.mode,value.validation_limits.model_dump(),value.native_mouse)

    @app.post("/api/external/{sid}/{action}")
    def external_action(sid: str, action: str, value: dict, x_participant_client: str = Header(default="")):
        if action in ('pause','resume','abort'):return external.control(sid,action)
        if action == "heartbeat":return external.beat(sid,x_participant_client)
        if action == "start":return external.start(sid,x_participant_client,value)
        if action == "end":return external.end(sid,x_participant_client)
        if action == "amend":return external.amend(sid,value.get("trial_id"),value.get("late"),value.get("quiz"),value.get("reason"))
        if action == "reset":return external.reset(sid,value.get("reason"))
        if action == "release":return external.release(sid,value.get("reason"))
        if action == "answer":return external.answer(sid,value.get("late"),value.get("quiz"))
        raise LabError("Unknown external action",404)

    @app.get('/api/assignments')
    def assignments(mode: str = 'mock'):
        from .assignment import plan
        return plan(engine,mode)

    @app.put('/api/assignments')
    def assignments_update(value: dict):
        from .assignment import save_plan
        return save_plan(engine,value.get('mode'),value.get('seed'))

    @app.get('/api/tracks/validate')
    def tracks_validate():
        from .tracks import validate_tracks
        return validate_tracks()

    @app.post('/api/sessions/{sid}/practice/{action}')
    def practice(sid: str, action: str):
        from .practice import practice_action
        return practice_action(engine,sid,action)

    @app.get("/api/tracks")
    def tracks(mode: str | None = None):
        if mode not in (None,"mock","hardware"):raise LabError("Unknown mode",422)
        return external.catalog(mode)

    @app.get("/api/stimuli")
    def stimuli():
        return read_json(ROOT / "config" / "stimuli.json")

    @app.get("/api/participants")
    def participants():
        return engine.participants

    @app.post("/api/participants", status_code=201)
    def participant_create():
        return engine.add_participant()

    @app.get("/api/sessions")
    def sessions():
        with engine.lock:
            return copy.deepcopy(list(engine.sessions.values()))[::-1]

    @app.post("/api/sessions", status_code=201)
    def session_create(value: CreateSession):
        return engine.create(value)

    @app.get('/api/dataset/validate')
    def dataset_validate():
        from .quality import quality_report
        from .tracks import validate_tracks
        with engine.lock:
            return {'tracks':validate_tracks(),'sessions':[quality_report(s,engine.storage.rows(s,'gaze')) for s in engine.sessions.values()]}

    @app.get('/api/export/history')
    def export_history():
        from .export_history import history
        return history(engine)

    @app.get("/api/export")
    def export_all(include_demo: bool = False):
        from .export_history import record_export
        with engine.lock:
            ids=[sid for sid,s in engine.sessions.items() if include_demo or s['mode']=='hardware']
            data=record_export(engine,ids,export_sessions(engine,ids))
        return Response(data, media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="eyetrack-all.zip"'})

    @app.get("/api/sessions/{sid}")
    def session_get(sid: str):
        with engine.lock:
            return copy.deepcopy(engine.get(sid))

    @app.get("/api/sessions/{sid}/results")
    def results(sid: str):
        return engine.summary(sid)

    @app.get("/api/sessions/{sid}/files")
    def files(sid: str):
        session = engine.get(sid)
        folder = engine.storage.session_path(session)
        return {"folder": str(folder), "files": [{"name": p.name, "bytes": p.stat().st_size} for p in folder.iterdir() if p.is_file()]}

    @app.get("/api/sessions/{sid}/export")
    def export(sid: str):
        from .export_history import record_export
        with engine.lock:
            data=record_export(engine,[sid],export_sessions(engine,[sid]))
        return Response(data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{sid}.zip"'})

    @app.post("/api/sessions/{sid}/step/{action}")
    def step(sid: str, action: str):
        return engine.step(sid, action)

    @app.post("/api/sessions/{sid}/answers/{phase}")
    def answers(sid: str, phase: str, value: Answers):
        return engine.answers(sid, phase, value.answers)

    @app.post("/api/sessions/{sid}/metadata")
    def metadata(sid: str, value: Metadata):
        return engine.metadata(sid, value.model_dump())

    @app.post("/api/sessions/{sid}/calibration/start")
    def calibration_start(sid: str, x_participant_client: str = Header(default="")):
        with engine.lock:
            engine.assert_client(sid, x_participant_client)
        return engine.calibration_start(sid)

    @app.post("/api/sessions/{sid}/calibration/point")
    def calibration_point(sid: str, value: CalibrationPoint, x_participant_client: str = Header(default="")):
        with engine.lock:
            engine.assert_client(sid, x_participant_client)
        return engine.calibration_point(sid, value)

    @app.post("/api/sessions/{sid}/trials/start")
    def trial_start(sid: str, x_participant_client: str = Header(default="")):
        return engine.start_trial(sid, x_participant_client)

    @app.post("/api/sessions/{sid}/events")
    def events(sid: str, value: Events, x_participant_client: str = Header(default="")):
        return engine.events(sid, x_participant_client, value.events)

    @app.post("/api/sessions/{sid}/trials/complete")
    def complete(sid: str, x_participant_client: str = Header(default="")):
        return engine.complete_trial(sid, x_participant_client)

    @app.post("/api/sessions/{sid}/stop")
    def stop(sid: str):
        return engine.stop(sid)

    @app.post("/api/sessions/{sid}/withdraw")
    def withdraw(sid: str):
        return engine.stop(sid, "participant_withdrawal", True)

    @app.post("/api/sessions/{sid}/video/start")
    def video_start(sid: str, value: dict):return video.start(sid,value)

    @app.put("/api/sessions/{sid}/video/{cid}/{index}")
    async def video_chunk(sid: str, cid: str, index: int, request: Request):
        data=bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data)>8*1024*1024:raise LabError("Video chunk เกิน 8 MB",413)
        return await asyncio.to_thread(video.chunk,sid,cid,index,bytes(data))

    @app.post("/api/sessions/{sid}/video/{cid}/finish")
    def video_finish(sid: str, cid: str, value: dict):return video.finish(sid,cid,value)

    @app.post("/api/sessions/{sid}/validation/start")
    def validation_start(sid: str, x_participant_client: str = Header(default="")):
        engine.assert_client(sid,x_participant_client)
        return validation.start(sid)

    @app.post("/api/sessions/{sid}/validation/point")
    def validation_point(sid: str, value: CalibrationPoint, x_participant_client: str = Header(default="")):
        engine.assert_client(sid,x_participant_client)
        return validation.point(sid,value)

    @app.get("/api/sessions/{sid}/stream-status")
    def stream_status(sid: str):
        with engine.lock:
            s=engine.get(sid); trial=s["trials"][-1] if s["trials"] else {}
            stream=trial.get("stream",{}); count=trial.get("gaze_count",0)
            span=stream.get("last_received_us",0)-stream.get("first_received_us",0)
            return {"mode":s["mode"],"simulated":s["mode"]!="hardware", "recording":engine.active==sid,
                    "sample_count":count,"last_sample_age_ms":(now_us()-stream["last_received_us"])/1000 if stream.get("last_received_us") else None,
                    "observed_hz":(count-1)*1e6/span if span>0 else None,
                    "left_valid_fraction":stream.get("left_valid",0)/count if count else 0,
                    "right_valid_fraction":stream.get("right_valid",0)/count if count else 0,
                    "device":trial.get("device") or (s.get("calibration") or {}).get("device"),
                    "validation_passed":s.get("validation",{}).get("passed",False)}

    @app.get("/api/device/{mode}")
    def device(mode: str):
        if mode not in engine.devices:
            raise LabError("Unknown device mode", 404)
        with engine.lock:
            if engine.active:
                session = engine.get(engine.active)
                if session["mode"] == mode:
                    return {**(session["calibration"] or {}).get("device", {}), "recording": True}
            return engine.devices[mode].status()

    @app.websocket("/ws/sessions/{sid}")
    async def socket(ws: WebSocket, sid: str, client: str = "", role: str = "observer"):
        if ws.headers.get("origin") not in origins + [None]:
            await ws.close(code=1008)
            return
        if access:
            protocols = ws.headers.get("sec-websocket-protocol", "").split(",")
            identity = access.verify(protocols[-1].strip()) if len(protocols)>1 else None
            if not identity or (identity["role"] != "researcher" and (identity["sid"] != sid or role != "participant")):
                await ws.close(code=1008)
                return
        await ws.accept(subprotocol="eyetrack" if access else None)
        attached = False
        try:
            if role == "participant":
                if not client or len(client) > 100:
                    raise LabError("Invalid participant client")
                engine.attach(sid, client)
                attached = True
            if role == "controller":
                if engine.get(sid).get("task_mode") != "figma_external":raise LabError("External session required")
                external.beat(sid,client)
            while True:
                if role == "controller":await asyncio.sleep(1)
                with engine.lock:
                    state = public_session(engine.get(sid)) if role == "participant" else copy.deepcopy(engine.get(sid))
                await ws.send_json({"type": "session", "session": state, "error": engine.fatal_error})
                try:
                    message = await asyncio.wait_for(ws.receive_json(), timeout=1)
                    if role == "controller" and message.get("type") == "heartbeat":
                        external.beat(sid,client)
                    if attached and message.get("type") == "heartbeat":
                        engine.heartbeat(sid, client)
                except asyncio.TimeoutError:
                    pass
        except LabError as error:
            await ws.send_json({"type": "error", "error": error.message})
            await ws.close(code=1008)
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            if role == "controller" and external.controllers.get(sid,{}).get("client") == client:
                with engine.lock:
                    external.controllers.pop(sid,None)
                    if engine.active == sid:engine.stop(sid,"controller_disconnected")
            if attached:
                # Finalization must run even when the websocket task is cancelled.
                engine.detach(sid, client)

    return app

app = create_app()

