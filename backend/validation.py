"""Independent validation samples are saved separately from task gaze."""
import copy
import threading
import time
from .engine import require, utc, now_us, clean_raw
from .quality import VALIDATION_POINTS, DEFAULT_LIMITS, point_metrics, check_display

class Validation:
    def __init__(self, engine):
        self.e = engine
        self.capture_seconds = 1.2

    def start(self, sid):
        with self.e.lock:
            s = copy.deepcopy(self.e.get(sid))
            require(s["mode"] == "hardware" and s["state"] == "validation" and s["consent"], "ยังไม่พร้อมตรวจพิกัด")
            require(self.e.active is None and self.e.calibrating is None, "อุปกรณ์กำลังใช้งาน")
            require(s["calibration"].get("clock_segment_id")==self.e.clock_segment_id,"ระบบเปิดใหม่ ต้อง Calibration อีกครั้ง")
            status = self.e.devices["hardware"].status()
            require(status.get("connected") and status.get("serial") == s["calibration"]["device"].get("serial"), "อุปกรณ์ไม่ตรงกับ Calibration")
            if s.get("validation"):
                s.setdefault("validation_attempts", []).append(s["validation"])
            s["validation"] = {"started_at":utc(),"serial":status["serial"],"simulated":False,
                "calibration_started_at":s["calibration"]["started_at"],"clock_segment_id":self.e.clock_segment_id,
                "limits":copy.deepcopy(s.get("validation_limits",DEFAULT_LIMITS)),"units":"normalized display coordinates; not degrees",
                "points":[],"passed":False}
            return self.e.commit(s)

    def point(self, sid, point):
        with self.e.lock:
            s = copy.deepcopy(self.e.get(sid))
            require(s["state"] == "validation" and s.get("validation") and s["consent"], "ยังไม่เริ่มตรวจพิกัด")
            require(self.e.active is None and self.e.calibrating is None, "อุปกรณ์กำลังใช้งาน")
            v=s["validation"]
            require(point.index == len(v["points"]), "ลำดับจุดตรวจไม่ถูกต้อง")
            require(check_display(point.viewport), "ต้องเต็มจอบนจอทดลองและ browser zoom 100%")
            if v["points"]:
                previous=v["points"][0]["viewport"]
                require(all(point.viewport.get(k)==previous.get(k) for k in ("screen_width","screen_height","device_pixel_ratio","screen_x","screen_y")), "จอเปลี่ยนระหว่างตรวจ ต้อง Calibration ใหม่")
            device=self.e.devices["hardware"]
            status=device.status()
            require(status.get("connected") and status.get("serial")==v["serial"], "อุปกรณ์เปลี่ยนหรือหลุด")
            samples=[]; gate=threading.Lock(); accepting=True
            def callback(raw):
                nonlocal accepting
                with gate:
                    if accepting and len(samples)<2000:
                        samples.append({"backend_received_us":now_us(),"raw":clean_raw(raw)})
            started=now_us(); error=None
            try:
                device.start(callback)
                time.sleep(self.capture_seconds)
            except Exception as exc:
                error=str(exc)
            finally:
                with gate:accepting=False
                try:device.stop()
                except Exception as exc:error=str(exc)
            target=VALIDATION_POINTS[point.index]
            metrics=point_metrics([sample["raw"] for sample in samples],target,v["limits"])
            entry={**point.model_dump(),"target":list(target),"started_us":started,"ended_us":now_us(),
                   "metrics":metrics,"samples":samples,"error":error}
            v["points"].append(entry)
            if error:metrics["passed"]=False
            if point.index==4:
                v["finished_at"]=utc()
                v["passed"]=all(p["metrics"]["passed"] for p in v["points"])
                if v["passed"]:
                    s["state"]="pre" if "pre" not in s["responses"] else "instructions"
            return self.e.commit(s)
