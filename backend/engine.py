import copy
import json
import math
import queue
import random
import secrets
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .devices import MockDevice, TobiiDevice, POINTS
from .native_mouse import NativeMouse
from .storage import append_mouse
from .quality import check_display, valid_point
from .models import Config
from .storage import Storage, atomic_json, read_json

def now_us():
    return time.perf_counter_ns() // 1000

def utc():
    return datetime.now(timezone.utc).isoformat()

class LabError(Exception):
    def __init__(self, message, code=409):
        self.message, self.code = message, code

def require(condition, message, code=409):
    if not condition:
        raise LabError(message, code)

def clean_raw(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {k: clean_raw(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_raw(v) for v in value]
    return value

class Engine:
    def __init__(self, root, config_path, recover=True):
        self.lock = threading.RLock()
        self.storage = Storage(root)
        self.config_path = Path(config_path)
        self.default_path = Path(__file__).resolve().parent.parent / "config" / "default.json"
        self.config = Config.model_validate(read_json(self.config_path if self.config_path.exists() else self.default_path)).model_dump()
        self.sessions = self.storage.load_all()
        self.participants_path = Path(root) / "participants.json"
        self.participants = read_json(self.participants_path) if self.participants_path.exists() else []
        self.devices = {"mock": MockDevice(), "hardware": TobiiDevice()}
        self.mouse = None
        self.mouse_factory = NativeMouse
        self.active = None
        self.calibrating = None
        self.clients = {}
        self.samples = queue.Queue(maxsize=18000)
        self.overflow = False
        self.last_gaze_us = 0
        self.fatal_error = None
        self.clock_segment_id = uuid.uuid4().hex
        if recover:
            self.recover()

    def recover(self):
        for session in self.sessions.values():
            changed=False
            for video in session.get("videos",[]):
                if video["status"]=="recording":
                    video.update(status="incomplete",reason="backend_restart");changed=True
            if changed:self.storage.save(session)
            if session["state"] == "recording":
                trial = session["trials"][-1]
                trial.update(status="incomplete", reason="backend_restart", ended_us=None, duration_ms=None)
                session["state"] = "interrupted"
                session["interruption"] = "backend_restart"
                self.storage.save(session)
            elif session["state"] == "calibrating":
                session["state"] = "calibration"
                self.storage.save(session)

    def get(self, sid):
        require(sid in self.sessions, "ไม่พบ session", 404)
        return self.sessions[sid]

    def commit(self, session):
        previous = self.sessions.get(session["session_id"], {})
        session["revision"] = previous.get("revision", 0) + 1
        self.storage.save(session)
        self.sessions[session["session_id"]] = session
        return copy.deepcopy(session)

    def add_participant(self):
        with self.lock:
            used={p['participant_id'] for p in self.participants}
            number=next((i for i in range(1,31) if f'P{i:03d}' not in used),None)
            require(number is not None,'All P001-P030 participant IDs have been allocated')
            participant = {"participant_id": f"P{number:03d}", "created_at": utc()}
            updated = self.participants + [participant]
            atomic_json(self.participants_path, updated)
            self.participants = updated
            return participant

    def update_config(self, config):
        with self.lock:
            value = config.model_dump()
            atomic_json(self.config_path, value)
            self.config = value
            return value

    def create(self, request, external_authorized=False):
        with self.lock:
            require(any(p["participant_id"] == request.participant_id for p in self.participants), "Participant ID ไม่พบ", 404)
            tasks = {t["id"]: t for t in self.config["tasks"] if t["enabled"]}
            require(len(set(request.task_ids)) == len(request.task_ids), "งานซ้ำ")
            require(all(i in tasks for i in request.task_ids), "กรุณาเลือกงานที่เปิดใช้งาน")
            if request.mode == "hardware":
                require(self.config["protocol"]["approved"], "ต้องยืนยัน protocol ก่อนใช้ Hardware Mode")
                if not external_authorized:
                    raise LabError("Hardware collection is available through the Figma External workflow with independent validation only")
                require(self.devices["hardware"].status().get("connected"), "ไม่พบ Tobii บนเครื่องนี้")
            require(all(tasks[i]["route"] in ("/stimuli/demo", "/stimuli/leb-status-search") for i in request.task_ids), "Stimulus route ยังไม่ได้ implement", 422)
            for i in request.task_ids:
                if tasks[i]["route"] == "/stimuli/leb-status-search":
                    require(request.condition == "mixed", "Status(LS)+Search(HS) ใช้ Mixed เท่านั้น", 422)
                    require(tasks[i]["target"] == "leb-submit" and tasks[i]["completion"] == "target_click", "LEB flow ต้องจบที่ Submit", 422)
                    require(not request.random_targets, "LEB flow มีเป้าหมาย Submit ที่ยืนยันไว้เพียงจุดเดียว", 422)
            seed = request.seed if request.seed is not None else secrets.randbits(32)
            rng = random.Random(seed)
            sequence = copy.deepcopy([tasks[i] for i in request.task_ids])
            if request.order == "random":
                rng.shuffle(sequence)
            for task in sequence:
                if request.random_targets:
                    require(bool(task["targets"]), "งานที่สุ่มเป้าหมายต้องกำหนดรายการ targets")
                    task["target"] = rng.choice(task["targets"])
            sid = "S" + uuid.uuid4().hex[:16]
            session = {
                "schema_version": 1, "revision": 0,
                "workflow_version": "calibration-before-pre-v1",
                "participant_id": request.participant_id, "session_id": sid, "mode": request.mode,
                "condition": request.condition, "order": request.order, "seed": seed,
                "random_targets": request.random_targets, "created_at": utc(), "state": "information",
                "snapshot": copy.deepcopy(self.config), "tasks": sequence, "task_index": 0,
                "trials": [], "responses": {}, "consent": None, "calibration": None,
                "calibration_attempts": [], "metadata": [], "sync_clock": "backend perf_counter microseconds",
                "stimulus_status": "figma_flow_mock_visual_unverified" if any(t["route"] == "/stimuli/leb-status-search" for t in sequence) else "demo_fixture_not_figma", "interruption": None,
            }
            self.storage.initialize(session)
            self.sessions[sid] = session
            return copy.deepcopy(session)

    def step(self, sid, action):
        with self.lock:
            session = copy.deepcopy(self.get(sid))
            if action == "information":
                require(session["state"] == "information", "ขั้นตอนข้อมูลวิจัยไม่ถูกต้อง")
                session["state"] = "consent"
            elif action == "consent":
                require(session["state"] == "consent", "ขั้นตอนยินยอมไม่ถูกต้อง")
                session["consent"] = {"accepted_at": utc(), "protocol_version": session["snapshot"]["protocol"]["version"]}
                session["state"] = "calibration" if session.get("workflow_version") in ("calibration-before-pre-v1","calibration-practice-pre-v2") else "pre"
            elif action == "resume":
                require(session["state"] == "interrupted", "Session ไม่ได้ถูกขัดจังหวะ")
                require(not self.fatal_error, "ต้องแก้ปัญหาการเขียนไฟล์และ restart backend ก่อน")
                session["state"] = "calibration"
                session["calibration"] = None
                session["interruption"] = None
            elif action == "finish":
                require(session["state"] == "thankyou", "ยังไม่ครบขั้นตอน")
                session["state"] = "completed"
                session["completed_at"] = utc()
            else:
                raise LabError("Unknown action", 400)
            return self.commit(session)

    def answers(self, sid, phase, answers):
        with self.lock:
            session = copy.deepcopy(self.get(sid))
            require(session["state"] == phase and phase in ("pre", "post"), "ไม่อยู่ในขั้นตอนแบบสอบถามนี้")
            if phase=='pre' and session.get('workflow_version')=='calibration-practice-pre-v2':
                require(session.get('practice_completed'),'Practice is required before Pre-test')
            questionnaire = session["snapshot"][phase]
            require(set(answers) <= {q["id"] for q in questionnaire["questions"]}, "พบคำตอบที่ไม่มีคำถาม", 422)
            answers=dict(answers)
            for q in questionnaire["questions"]:
                rule=q.get('show_if')
                if rule and answers.get(rule['question_id'])!=rule['equals']:
                    answers.pop(q['id'],None)
                    continue
                value = answers.get(q["id"])
                missing = value is None or value == [] or (isinstance(value, str) and not value.strip())
                if q["required"]:
                    require(not missing, "กรุณาตอบ: " + q["label"], 422)
                if missing:
                    continue
                if q["type"] == "likert":
                    require(type(value) is int and 1 <= value <= 5, "คะแนนต้องอยู่ระหว่าง 1–5", 422)
                elif q["type"] == "number":
                    require(type(value) is int and 0 <= value <= 120, "อายุต้องเป็นจำนวนเต็ม 0–120", 422)
                elif q["type"] == "single":
                    require(isinstance(value, str) and value in q["options"], "ตัวเลือกไม่ถูกต้อง", 422)
                elif q["type"] == "multiple":
                    require(isinstance(value, list) and len(set(value)) == len(value) and all(v in q["options"] for v in value), "ตัวเลือกไม่ถูกต้อง", 422)
                else:
                    require(isinstance(value, str) and len(value) <= (1000 if q["type"] == "short" else 10000), "ข้อความยาวเกินกำหนด", 422)
            session.setdefault("drafts", {}).pop(phase, None)
            session["responses"][phase] = {"version": questionnaire["version"], "answers": answers, "submitted_at": utc()}
            session["state"] = ("instructions" if session.get("workflow_version") in ("calibration-before-pre-v1","calibration-practice-pre-v2") else "calibration") if phase == "pre" else "thankyou"
            # Metadata is authoritative; CSV is materialized during export to avoid partial questionnaire writes.
            return self.commit(session)

    def save_draft(self, sid, phase, answers, revision):
        with self.lock:
            session = copy.deepcopy(self.get(sid))
            require(session["consent"] and session["state"] == phase and phase in ("pre", "post"), "ไม่อยู่ในขั้นตอนแบบสอบถามนี้")
            current = session.get("drafts", {}).get(phase, {})
            require(current.get("revision", 0) == revision, "แบบร่างถูกแก้ไขจากหน้าต่างอื่น กรุณาโหลดใหม่")
            questions = {q["id"]: q for q in session["snapshot"][phase]["questions"]}
            require(set(answers) <= set(questions), "พบคำตอบที่ไม่มีคำถาม", 422)
            for key, value in answers.items():
                require(len(json.dumps(value, ensure_ascii=False)) <= 12000, "คำตอบยาวเกินกำหนด", 422)
                q = questions[key]
                if q["type"] == "number" and value != "":
                    require(type(value) is int and 0 <= value <= 120, "อายุไม่ถูกต้อง", 422)
            draft = {"answers": answers, "revision": revision + 1, "saved_at": utc(), "version": session["snapshot"][phase]["version"]}
            session.setdefault("drafts", {})[phase] = draft
            self.commit(session)
            return draft

    def attach(self, sid, client):
        with self.lock:
            self.get(sid)
            existing = self.clients.get(sid)
            require(not existing or existing["client"] == client or time.monotonic() - existing["heartbeat"] > 6,
                    "มีหน้าต่างผู้เข้าร่วมอื่นเปิด session นี้อยู่")
            self.clients[sid] = {"client": client, "heartbeat": time.monotonic()}

    def heartbeat(self, sid, client):
        with self.lock:
            self.assert_client(sid, client)
            self.clients[sid]["heartbeat"] = time.monotonic()

    def assert_client(self, sid, client):
        require(sid in self.clients and self.clients[sid]["client"] == client, "กรุณาเชื่อมหน้าผู้เข้าร่วมก่อน")
        require(time.monotonic() - self.clients[sid]["heartbeat"] <= 6, "การเชื่อมต่อผู้เข้าร่วมหมดเวลา")

    def detach(self, sid, client):
        with self.lock:
            if self.clients.get(sid, {}).get("client") == client:
                self.clients.pop(sid)
                if (self.active == sid and self.get(sid).get("task_mode") != "figma_external") or self.calibrating == sid:
                    self.stop(sid, "participant_disconnected")

    def metadata(self, sid, value):
        with self.lock:
            session = copy.deepcopy(self.get(sid))
            require(session["consent"], "ต้องยินยอมก่อนบันทึก metadata")
            require(session["state"] not in ("completed", "withdrawn"), "Session สิ้นสุดแล้ว")
            session["metadata"].append({**value, "recorded_at": utc(), "clock_segment_id": self.clock_segment_id})
            return self.commit(session)

    def calibration_start(self, sid):
        with self.lock:
            session = copy.deepcopy(self.get(sid))
            require(session["state"] in ("calibration", "validation", "instructions"), "ขั้นตอน calibration ไม่ถูกต้อง")
            require(self.active is None and self.calibrating is None, "มี session อื่นกำลังใช้อุปกรณ์")
            require(session["consent"], "ต้องให้ความยินยอม")
            device = self.devices[session["mode"]]
            status = device.begin_calibration()
            if session.get("validation"):
                session.setdefault("validation_attempts", []).append(copy.deepcopy(session["validation"]))
            session.pop("validation", None)
            session["state"] = "calibrating"
            session["calibration"] = {"points": [], "success": False, "started_at": utc(), "clock_segment_id": self.clock_segment_id, "device": status}
            try:
                result = self.commit(session)
            except BaseException:
                device.cancel_calibration()
                raise
            self.calibrating = sid
            return result

    def calibration_point(self, sid, point):
        with self.lock:
            session = copy.deepcopy(self.get(sid))
            require(self.calibrating == sid and session["state"] == "calibrating", "Calibration ไม่ได้เริ่ม")
            require(point.index == len(session["calibration"]["points"]), "ลำดับจุด calibration ไม่ถูกต้อง")
            if session["mode"] == "hardware":
                require(point.viewport.get("fullscreen") is True, "Hardware calibration ต้องเต็มจอบนจอ Tobii")
            x, y = POINTS[point.index]
            device = self.devices[session["mode"]]
            try:
                result = device.collect(x, y)
            except Exception as error:
                result = {"success": False, "sdk_status": "exception", "error": str(error)}
            session["calibration"]["points"].append({"x": x, "y": y, **point.model_dump(), **result})
            if not result["success"] or point.index == 4:
                try:
                    final = device.finish_calibration() if result["success"] else {"success": False, "sdk_status": result["sdk_status"]}
                except Exception as error:
                    final = {"success": False, "sdk_status": "exception", "error": str(error)}
                device.cancel_calibration()
                session["calibration"].update(clean_raw(final))
                session["calibration"]["finished_at"] = utc()
                session["calibration_attempts"].append(copy.deepcopy(session["calibration"]))
                session["state"] = ("pre" if session.get("workflow_version") == "calibration-before-pre-v1" and "pre" not in session["responses"] else "instructions") if final["success"] else "calibration"
                if final['success'] and session.get('workflow_version')=='calibration-practice-pre-v2':
                    from .practice import after_calibration
                    session['state']=after_calibration(session)
                self.calibrating = None
                if final["success"] and session["mode"] == "hardware":
                    session["state"] = "validation"
            return self.commit(session)

    def start_trial(self, sid, client, external_authorized=False):
        with self.lock:
            require(self.get(sid).get("task_mode") != "figma_external" or external_authorized, "เริ่มรอบจากศูนย์ควบคุมเท่านั้น")
            self.assert_client(sid, client)
            require(not self.fatal_error, "การบันทึกหยุดเนื่องจากข้อผิดพลาดไฟล์")
            session = copy.deepcopy(self.get(sid))
            require(self.active is None and self.calibrating is None, "มีการบันทึกอยู่แล้ว")
            require(session["state"] == "instructions" and session["consent"], "ยังไม่พร้อมเริ่มงาน")
            require("pre" in session["responses"], "ต้องตอบแบบสอบถามก่อนทดลองก่อนเริ่มงาน")
            require(session["calibration"] and session["calibration"]["success"], "ต้อง calibration สำเร็จก่อน")
            require(session["metadata"], "กรุณารอการเทียบเวลาและข้อมูลจอ")
            if session["mode"] == "hardware":
                validation = session.get("validation", {})
                require(validation.get("passed") and validation.get("clock_segment_id") == self.clock_segment_id,
                        "ต้องตรวจพิกัดหลัง Calibration บนการเปิดระบบครั้งนี้ก่อน")
                status = self.devices["hardware"].status()
                require(status.get("connected") and status.get("serial") == validation.get("serial"), "อุปกรณ์เปลี่ยนหรือขาดการเชื่อมต่อ ต้อง Calibration ใหม่")
                require(session["calibration"]["started_at"] == validation.get("calibration_started_at"), "ผล Validation ไม่ตรง Calibration")
            task = session["tasks"][session["task_index"]]
            trial = {"trial_id": "T" + uuid.uuid4().hex[:16], "task_id": task["id"], "started_us": now_us(),
                     "ended_us": None, "duration_ms": None, "status": "recording", "reason": "",
                     "click_count": 0, "gaze_count": 0, "event_ids": [], "target_reached": False,
                     "clock_segment_id": self.clock_segment_id, "metadata_index": len(session["metadata"]) - 1}
            session["trials"].append(trial)
            session["state"] = "recording"
            self.commit(session)
            self.active = sid
            self.last_gaze_us = now_us()
            self.overflow = False
            device = self.devices[session["mode"]]
            def callback(sample):
                try:
                    self.samples.put_nowait((sid, trial["trial_id"], sample, now_us()))
                except queue.Full:
                    self.overflow = True
            try:
                if session["mode"] == "hardware":
                    session = copy.deepcopy(self.get(sid))
                    session.setdefault("sdk_clock_samples", []).append({"trial_id": trial["trial_id"], "phase":"before_subscription", **device.clock_sample()})
                    self.commit(session)
                if session.get("native_mouse"):
                    self.mouse=self.mouse_factory()
                    self.mouse.start()
                device.start(callback)
                updated = copy.deepcopy(self.get(sid))
                updated["trials"][-1]["device"] = device.status() if session["mode"] == "hardware" else device.status()
                self.commit(updated)
            except Exception:
                self.stop(sid, "device_start_failed")
                raise
            return copy.deepcopy(self.get(sid))

    def drain(self, final=False):
        if self.mouse and self.active:
            session=self.get(self.active);trial=session['trials'][-1]
            for row in self.mouse.drain(18000 if final else 240):
                append_mouse(self.storage,session,{**row,"participant_id":session['participant_id'],"session_id":session['session_id'],"trial_id":trial['trial_id'],"task_id":trial['task_id']})
                trial['native_mouse_count']=trial.get('native_mouse_count',0)+1
                if row['event_type']=='button' and row['pressed'] is True:trial['native_click_count']=trial.get('native_click_count',0)+1
        for _ in range(18000 if final else 240):
            try:
                sid, tid, sample, received = self.samples.get_nowait()
            except queue.Empty:
                return
            session = self.get(sid)
            trial = session["trials"][-1]
            if self.active != sid or trial["trial_id"] != tid:
                continue
            left = sample.get("left_gaze_point_on_display_area", [None, None])
            right = sample.get("right_gaze_point_on_display_area", [None, None])
            row = {"participant_id": session["participant_id"], "session_id": sid, "trial_id": tid, "task_id": trial["task_id"],
                   "mode": session["mode"], "device_timestamp": sample.get("device_time_stamp"),
                   "system_timestamp": sample.get("system_time_stamp"), "backend_received_us": received,
                   "left_gaze_x": left[0], "left_gaze_y": left[1], "left_validity": sample.get("left_gaze_point_validity"),
                   "right_gaze_x": right[0], "right_gaze_y": right[1], "right_validity": sample.get("right_gaze_point_validity"),
                   "raw_json": json.dumps(clean_raw(sample), ensure_ascii=False, allow_nan=False)}
            self.storage.append(session, "gaze", row)
            trial["gaze_count"] += 1
            stream = trial.setdefault("stream", {"left_valid":0,"right_valid":0,"first_received_us":received,"first_sdk_system_us":sample.get("system_time_stamp")})
            for eye in ("left","right"):
                stream[eye+"_valid"] += int(valid_point(sample,eye))
            stream.update(last_received_us=received,last_sdk_system_us=sample.get("system_time_stamp"))
            self.last_gaze_us = received

    def events(self, sid, client, events):
        with self.lock:
            require(self.get(sid).get("task_mode") != "figma_external", "Figma telemetry unavailable")
            self.assert_client(sid, client)
            session = self.get(sid)
            require(self.active == sid and session["state"] == "recording", "ไม่ได้บันทึกงานนี้")
            trial = session["trials"][-1]
            task = session["tasks"][session["task_index"]]
            for event in events:
                require(event.trial_id == trial["trial_id"], "Trial ID ไม่ตรง")
                if event.event_id in trial["event_ids"]:
                    continue
                value = event.model_dump()
                row = {**value, "participant_id": session["participant_id"], "session_id": sid, "task_id": task["id"],
                       "backend_received_us": now_us(), "viewport_json": json.dumps(value["viewport"], ensure_ascii=False)}
                self.storage.append(session, "clicks", row)
                trial["event_ids"].append(event.event_id)
                if event.event_type == "click":
                    trial["click_count"] += 1
                    if event.target_element_id == task["target"]:
                        trial["target_reached"] = True
            return {"accepted": len(events), "target_reached": trial["target_reached"]}

    def end_trial(self, sid, status="completed", reason=""):
        require(self.active == sid, "Session ไม่ได้บันทึก")
        session = self.get(sid)
        device = self.devices[session["mode"]]
        try:
            device.stop()
        finally:
            if self.mouse:self.mouse.stop()
            self.drain(final=True)
            self.mouse=None
        session = copy.deepcopy(self.get(sid))
        trial = session["trials"][-1]
        trial["ended_us"] = now_us()
        trial["duration_ms"] = (trial["ended_us"] - trial["started_us"]) / 1000
        trial["status"], trial["reason"] = status, reason
        if session["mode"] == "hardware":
            try:session.setdefault("sdk_clock_samples", []).append({"trial_id":trial["trial_id"],"phase":"after_unsubscribe",**device.clock_sample()})
            except Exception as error:trial["clock_error"]=str(error)
        self.active = None
        if status == "awaiting_answers" and session.get("task_mode") == "figma_external":
            session["state"] = "external_answers"
        elif status == "incomplete":
            session["state"] = "interrupted"
            session["interruption"] = reason
        else:
            session["task_index"] += 1
            session["state"] = "post" if session["task_index"] == len(session["tasks"]) else "instructions"
        return self.commit(session)

    def complete_trial(self, sid, client):
        with self.lock:
            require(self.get(sid).get("task_mode") != "figma_external", "ใช้คำสั่งจบรอบในศูนย์ควบคุม")
            self.assert_client(sid, client)
            session = self.get(sid)
            require(self.active == sid, "ไม่มีงานที่กำลังบันทึก")
            task = session["tasks"][session["task_index"]]
            require(task["completion"] == "manual" or session["trials"][-1]["target_reached"], "ยังไม่ถึงเป้าหมายงาน")
            return self.end_trial(sid)

    def stop(self, sid, reason="researcher_stop", withdraw=False):
        with self.lock:
            session = self.get(sid)
            require(session["state"] not in ("completed", "withdrawn"), "Session นี้สิ้นสุดแล้ว")
            if self.active == sid:
                self.end_trial(sid, "incomplete", reason)
            if self.calibrating == sid:
                self.devices[session["mode"]].cancel_calibration()
                self.calibrating = None
                session["state"] = "calibration"
                self.commit(session)
            session = copy.deepcopy(self.get(sid))
            if session["mode"] == "hardware":
                if session.get("validation"):session["validation"]["passed"]=False
                if "pre" not in session["responses"]:session["state"]="calibration"
            session["state"] = "withdrawn" if withdraw else ("interrupted" if session["consent"] and "pre" in session["responses"] else session["state"])
            session["interruption"] = reason
            if withdraw:
                session["withdrawn_at"] = utc()
            return self.commit(session)

    def tick(self):
        with self.lock:
            try:
                self.drain()
                if self.active:
                    sid = self.active
                    session = self.get(sid)
                    task = session["tasks"][session["task_index"]]
                    if self.mouse and (self.mouse.overflow or not self.mouse.healthy()):
                        self.stop(sid, "native_mouse_stream_lost_or_overflow")
                    elif self.overflow:
                        self.stop(sid, "gaze_queue_overflow")
                    elif (session.get("task_mode") == "figma_external" and time.monotonic() - self.external.controllers.get(sid, {}).get("heartbeat", 0) > 15) or (session.get("task_mode") != "figma_external" and time.monotonic() - self.clients.get(sid, {}).get("heartbeat", 0) > 6):
                        self.stop(sid, "heartbeat_timeout")
                    elif now_us() - self.last_gaze_us > 3_000_000:
                        self.stop(sid, "gaze_stream_lost")
                    elif task["time_limit"] and now_us() - session["trials"][-1]["started_us"] >= task["time_limit"] * 1_000_000:
                        self.end_trial(sid, "failed", "time_limit")
                if self.calibrating and time.monotonic() - self.clients.get(self.calibrating, {}).get("heartbeat", 0) > 6:
                    self.stop(self.calibrating, "calibration_connection_lost")
            except Exception as error:
                self.fail_closed(error)

    def fail_closed(self, error):
        with self.lock:
            if self.mouse:
                self.mouse.stop()
                self.mouse=None
            self.fatal_error = str(error)
            sid = self.active
            self.active = None
            if sid:
                try:
                    self.devices[self.get(sid)["mode"]].stop()
                except Exception:
                    pass
                session = self.get(sid)
                session["state"] = "interrupted"
                session["interruption"] = "storage_or_device_error: " + str(error)
                session["trials"][-1]["status"] = "incomplete"
                try:
                    self.storage.save(session)
                except OSError:
                    pass

    def summary(self, sid):
        with self.lock:
            session = copy.deepcopy(self.get(sid))
            counts = {}
            for name in ("gaze", "clicks"):
                rows = self.storage.rows(session, name)
                counts[name] = len(rows)
            gaze_rows = self.storage.rows(session, "gaze")
            event_rows = self.storage.rows(session, "clicks")
            for trial in session["trials"]:
                trial["gaze_count"] = sum(r["trial_id"] == trial["trial_id"] for r in gaze_rows)
                trial["click_count"] = sum(r["trial_id"] == trial["trial_id"] and r["event_type"] == "click" for r in event_rows)
            session["counts"] = counts
            return session

