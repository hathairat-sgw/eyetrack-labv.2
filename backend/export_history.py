"""Content-addressed export audit; repeated identical exports do not add duplicates."""
import hashlib,json
from .storage import atomic_json,read_json
from .engine import utc

def history(engine):
    path=engine.storage.root/'export-history.json'
    return read_json(path) if path.exists() else []

def record_export(engine,ids,data):
    with engine.lock:
        key=hashlib.sha256(json.dumps([engine.get(sid) for sid in sorted(ids)],sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
        items=history(engine)
        if not any(item['snapshot_sha256']==key for item in items):
            items.append({'snapshot_sha256':key,'first_exported_at':utc(),'session_ids':list(ids),'zip_bytes':len(data)})
            atomic_json(engine.storage.root/'export-history.json',items)
    return data
