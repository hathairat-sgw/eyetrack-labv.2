import csv
import hashlib
import io
import json
import zipfile
from .storage import FIELDS, NATIVE_FIELDS, mouse_rows
from .quality import quality_report

def csv_bytes(name, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS[name], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")

def export_sessions(engine, ids):
    output = io.BytesIO()
    with engine.lock, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for sid in ids:
            session = engine.get(sid)
            if session["state"] in ("recording", "calibrating"):
                from .engine import LabError
                raise LabError("หยุดการบันทึกก่อน export เพื่อให้ได้ snapshot ที่ครบถ้วน")
            prefix = f'{session["mode"]}/{session["participant_id"]}/{sid}/'
            for name in FIELDS:
                if name in ("pre_test", "post_test"):
                    phase = "pre" if name == "pre_test" else "post"
                    response = session["responses"].get(phase)
                    rows = [] if response is None else [
                        {"participant_id": session["participant_id"], "session_id": sid,
                         "version": response["version"], "question_id": q,
                         "answer": json.dumps(answer, ensure_ascii=False), "submitted_at": response["submitted_at"]}
                        for q, answer in response["answers"].items()]
                elif name == "trials":
                    rows = [{**t, "participant_id": session["participant_id"], "session_id": sid} for t in session["trials"]]
                    # Reconcile against actual raw files after a process interruption.
                    for trial in rows:
                        trial["gaze_count"] = sum(r["trial_id"] == trial["trial_id"] for r in engine.storage.rows(session, "gaze"))
                        trial["click_count"] = sum(r["trial_id"] == trial["trial_id"] and r["event_type"] == "click" for r in engine.storage.rows(session, "clicks"))
                else:
                    rows = engine.storage.rows(session, name)
                if name in ("gaze", "clicks"):
                    trial_ids = {t["trial_id"] for t in session["trials"]}
                    task_ids = {t["id"] for t in session["tasks"]}
                    if any(r["trial_id"] not in trial_ids or r["task_id"] not in task_ids for r in rows):
                        raise ValueError("Unknown trial/task identifier in " + name)
                archive.writestr(prefix + name + ".csv", csv_bytes(name, rows))
            if session.get("task_mode") == "figma_external":
                from .gaze_features import derive_gaze
                features = derive_gaze(engine.storage.rows(session,"gaze"),session)
                if features:
                    feature_stream=io.StringIO(newline="")
                    feature_writer=csv.DictWriter(feature_stream,fieldnames=list(features[0]))
                    feature_writer.writeheader();feature_writer.writerows(features)
                    archive.writestr(prefix+"gaze_features_exploratory.csv",feature_stream.getvalue().encode("utf-8-sig"))
                columns = ["participant_id","session_id","track_id","group","duplicate_of","configuration_version","trial_id","test_index","variant_id","course_id","prototype_url","starting_node_id","attempt","mode","simulated","started_at","ended_at","duration_ms","start_trigger","end_trigger","late_answer","quiz_answer","expected_late","expected_quiz","decision_error","status","reason","figma_events"]
                stream = io.StringIO(newline="")
                writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                for trial in session["trials"]:
                    writer.writerow({**session["external"], **trial, "participant_id":session["participant_id"],"session_id":sid,"mode":session["mode"]})
                archive.writestr(prefix + "rounds.csv",stream.getvalue().encode("utf-8-sig"))
            if any(v["status"]=="recording" for v in session.get("videos",[])):
                from .engine import LabError
                raise LabError("หยุดและบันทึกวิดีโอก่อน Export")
            for video in session.get("videos",[]):
                filename=video["filename"]+(".part" if video["status"]!="completed" else "")
                path=engine.storage.session_path(session)/filename
                # Recovery may have a completed rename before JSON commit; preserve as incomplete evidence.
                if not path.exists() and video["status"]!="completed":path=engine.storage.session_path(session)/video["filename"]
                if not path.exists():raise ValueError("Video file missing: "+filename)
                if video["status"]=="completed":
                    with path.open("rb") as stream:
                        for chunk in video["chunks"]:
                            data=stream.read(chunk["bytes"])
                            if len(data)!=chunk["bytes"] or hashlib.sha256(data).hexdigest()!=chunk["sha256"]:raise ValueError("Video integrity check failed: "+filename)
                        if stream.read(1):raise ValueError("Unexpected video bytes: "+filename)
                archive.write(path,prefix+"video/"+filename)
            if session.get("videos"):
                archive.writestr(prefix+"video_manifest.json",json.dumps(session["videos"],ensure_ascii=False,indent=2))
            mouse=mouse_rows(engine.storage,session)
            if session.get("native_mouse") or mouse:
                stream=io.StringIO(newline="");writer=csv.DictWriter(stream,fieldnames=NATIVE_FIELDS);writer.writeheader();writer.writerows(mouse)
                archive.writestr(prefix+"mouse.csv",stream.getvalue().encode("utf-8-sig"))
            archive.writestr(prefix + "quality_report.json", json.dumps(quality_report(session, engine.storage.rows(session,"gaze")),ensure_ascii=False,indent=2))
            if session.get("validation"):
                archive.writestr(prefix + "validation.json", json.dumps({"current":session["validation"],"previous_attempts":session.get("validation_attempts",[])},ensure_ascii=False,indent=2))
            archive.writestr(prefix + "session.json", json.dumps(session, ensure_ascii=False, indent=2))
            archive.writestr(prefix + "README.txt", "Raw timestamps retain their original units. Browser timestamp = performance.now() milliseconds. Backend = perf_counter microseconds. Tobii timestamps = SDK microseconds. See session metadata for clock alignment. Incomplete trials are never assigned a fabricated end time. Demo data is not research data.")
    return output.getvalue()

