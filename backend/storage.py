import csv
import io
import json
import os
import tempfile
import time
from pathlib import Path

FIELDS = {
    "participants": ["participant_id", "session_id", "mode", "condition", "created_at"],
    "pre_test": ["participant_id", "session_id", "version", "question_id", "answer", "submitted_at"],
    "post_test": ["participant_id", "session_id", "version", "question_id", "answer", "submitted_at"],
    "gaze": ["participant_id", "session_id", "trial_id", "task_id", "mode", "device_timestamp", "system_timestamp", "backend_received_us", "left_gaze_x", "left_gaze_y", "left_validity", "right_gaze_x", "right_gaze_y", "right_validity", "raw_json"],
    "clicks": ["participant_id", "session_id", "trial_id", "task_id", "event_id", "event_type", "timestamp", "backend_received_us", "client_x", "client_y", "screen_x", "screen_y", "scroll_x", "scroll_y", "page_url", "target_element_id", "viewport_json"],
    "trials": ["participant_id", "session_id", "trial_id", "task_id", "started_us", "ended_us", "duration_ms", "status", "reason", "click_count", "gaze_count", "native_mouse_count", "native_click_count"],
}

def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(5):
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.02 * (attempt + 1))
    except BaseException:
        if os.path.exists(temp):
            os.unlink(temp)
        raise

def read_json(path):
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)

class Storage:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def session_path(self, session):
        return self.root / session["mode"] / "participants" / session["participant_id"] / session["session_id"]

    def save(self, session):
        atomic_json(self.session_path(session) / "session.json", session)

    def initialize(self, session):
        folder = self.session_path(session)
        folder.mkdir(parents=True, exist_ok=False)
        for name, columns in FIELDS.items():
            with (folder / (name + ".csv")).open("x", encoding="utf-8-sig", newline="") as stream:
                csv.DictWriter(stream, fieldnames=columns).writeheader()
        self.append(session, "participants", {k: session[k] for k in FIELDS["participants"]})
        self.save(session)

    def append(self, session, name, row):
        path = self.session_path(session) / (name + ".csv")
        with path.open("a", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS[name], extrasaction="ignore")
            writer.writerow(row)
            stream.flush()
            os.fsync(stream.fileno())

    def rows(self, session, name):
        with (self.session_path(session) / (name + ".csv")).open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != FIELDS[name]:
                raise ValueError("Invalid CSV header: " + name)
            rows = list(reader)
        for row in rows:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Incomplete CSV row: " + name)
            if row["session_id"] != session["session_id"] or row["participant_id"] != session["participant_id"]:
                raise ValueError("Identifier mismatch: " + name)
        return rows

    def load_all(self):
        result = {}
        for path in self.root.glob("*/participants/P*/S*/session.json"):
            session = read_json(path)
            result[session["session_id"]] = session
        return result



NATIVE_FIELDS = ["participant_id","session_id","trial_id","task_id","event_type","backend_us","screen_x","screen_y","button","pressed","scroll_dx","scroll_dy","foreground_title","coordinate_space","source","page_url","target_element_id"]

def append_mouse(storage, session, row):
    path=storage.session_path(session)/"mouse.csv"
    fresh=not path.exists()
    with path.open("a",encoding="utf-8-sig" if fresh else "utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=NATIVE_FIELDS)
        if fresh:writer.writeheader()
        writer.writerow(row);stream.flush();os.fsync(stream.fileno())

def mouse_rows(storage, session):
    path=storage.session_path(session)/"mouse.csv"
    if not path.exists():return []
    with path.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=NATIVE_FIELDS:raise ValueError("Invalid mouse CSV header")
        rows=list(reader)
    for row in rows:
        if None in row or any(v is None for v in row.values()):raise ValueError("Incomplete mouse row")
        if row["session_id"]!=session["session_id"] or row["participant_id"]!=session["participant_id"]:raise ValueError("Mouse identifiers mismatch")
        trial=next((t for t in session['trials'] if t['trial_id']==row['trial_id']),None)
        if trial is None or trial['task_id']!=row['task_id']:raise ValueError('Unknown mouse trial/task')
    return rows
