import math
import sys
import os
import random
import threading
import time

POINTS = [(0.1, 0.1), (0.9, 0.1), (0.5, 0.5), (0.1, 0.9), (0.9, 0.9)]

class MockDevice:
    mode = "mock"

    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None

    def status(self):
        return {"connected": True, "simulated": True, "model": "Demo gaze generator", "serial": "MOCK", "message": "ข้อมูลจำลอง ไม่ใช่ Tobii"}

    def begin_calibration(self):
        return self.status()

    def collect(self, x, y):
        return {"success": True, "sdk_status": "simulated"}

    def finish_calibration(self):
        return {"success": True, "sdk_status": "simulated", "simulated": True}

    def cancel_calibration(self):
        pass

    def start(self, callback):
        self.stop_event = threading.Event()
        stop = self.stop_event
        def generate():
            rng = random.Random(42)
            while not stop.wait(1 / 60):
                now = time.perf_counter_ns() // 1000
                callback({"device_time_stamp": now, "system_time_stamp": now,
                    "left_gaze_point_on_display_area": [rng.random(), rng.random()],
                    "right_gaze_point_on_display_area": [rng.random(), rng.random()],
                    "left_gaze_point_validity": 1, "right_gaze_point_validity": 1})
        self.thread = threading.Thread(target=generate, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

class TobiiDevice:
    mode = "hardware"

    def __init__(self):
        self.sdk = None
        self.tracker = None
        self.calibration = None
        self.callback = None
        self.cached_status = None

    def status(self):
        if self.callback is not None and self.cached_status:
            return dict(self.cached_status)
        try:
            import tobii_research as sdk
            self.sdk = sdk
            devices = sdk.find_all_eyetrackers()
            if not devices:
                self.tracker = None
                return {"connected": False, "simulated": False, "python_executable": sys.executable, "message": "ไม่พบ Tobii บนเครื่องที่รัน backend นี้ ตรวจสาย USB และ active display ใน Eye Tracker Manager ถ้า Tobii อยู่อีกเครื่อง ต้องเปิดโปรแกรมบนเครื่องนั้น"}
            serial = os.environ.get("EYETRACK_TOBII_SERIAL")
            if serial:
                devices = tuple(d for d in devices if d.serial_number == serial)
                if not devices:
                    self.tracker = None
                    return {"connected": False, "simulated": False, "message": "Configured Tobii serial not found"}
            if len(devices) != 1:
                self.tracker = None
                return {"connected": False, "simulated": False, "message": "Multiple devices found. Set EYETRACK_TOBII_SERIAL.",
                        "devices": [{"serial": d.serial_number, "model": d.model} for d in devices]}
            self.tracker = devices[0]
            self.cached_status = {"connected": True, "simulated": False, "model": self.tracker.model,
                    "serial": self.tracker.serial_number, "address": self.tracker.address,
                    "sdk_version": sdk.__version__ if hasattr(sdk, "__version__") else "unknown"}
            try:
                self.cached_status["configured_hz"] = self.tracker.get_gaze_output_frequency()
                area=self.tracker.get_display_area()
                self.cached_status["display_area_mm"]={key:list(getattr(area,key)) for key in ("top_left","top_right","bottom_left")}
            except Exception as error:
                self.cached_status["metadata_error"] = str(error)
            return dict(self.cached_status)
        except (ImportError, OSError) as error:
            return {"connected": False, "simulated": False, "message": "Tobii SDK ไม่พร้อม: " + str(error) + " — ใช้ Python 3.10 x64 สำหรับ tobii-research 2.1.0"}
        except Exception as error:
            return {"connected": False, "simulated": False, "message": str(error)}

    def begin_calibration(self):
        status = self.status()
        if not status["connected"]:
            raise RuntimeError(status["message"])
        self.calibration = self.sdk.ScreenBasedCalibration(self.tracker)
        self.calibration.enter_calibration_mode()
        return status

    def collect(self, x, y):
        if self.calibration is None:
            raise RuntimeError("Calibration not started")
        status = self.calibration.collect_data(x, y)
        return {"success": status == self.sdk.CALIBRATION_STATUS_SUCCESS, "sdk_status": str(status)}

    def finish_calibration(self):
        try:
            result = self.calibration.compute_and_apply()
            return {"success": result.status == self.sdk.CALIBRATION_STATUS_SUCCESS,
                    "sdk_status": str(result.status), "simulated": False,
                    "sdk_points": [{"target":list(p.position_on_display_area),"samples":[{
                        eye:{"position":list(getattr(sample,eye+"_eye").position_on_display_area),"validity":str(getattr(sample,eye+"_eye").validity)}
                        for eye in ("left","right")} for sample in p.calibration_samples]} for p in result.calibration_points]}
        finally:
            self.cancel_calibration()

    def cancel_calibration(self):
        if self.calibration is not None:
            try:
                self.calibration.leave_calibration_mode()
            finally:
                self.calibration = None

    def clock_sample(self):
        before = time.perf_counter_ns() // 1000
        sdk_us = self.sdk.get_system_time_stamp()
        after = time.perf_counter_ns() // 1000
        return {"sdk_system_us": sdk_us, "backend_midpoint_us": (before + after) / 2, "uncertainty_us": (after - before) / 2}

    def start(self, callback):
        if not self.status()["connected"]:
            raise RuntimeError("Tobii disconnected")
        if self.callback is not None:
            raise RuntimeError("Gaze subscription already active")
        self.callback = callback
        try:
            self.tracker.subscribe_to(self.sdk.EYETRACKER_GAZE_DATA, callback, as_dictionary=True)
        except BaseException:
            self.callback = None
            raise

    def stop(self):
        if self.callback is not None and self.tracker is not None:
            callback, self.callback = self.callback, None
            self.tracker.unsubscribe_from(self.sdk.EYETRACKER_GAZE_DATA, callback)

