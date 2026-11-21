"""Persist a reproducible, mode-isolated permutation before session allocation."""
import random
from .storage import atomic_json,read_json
from .engine import require,utc

def plan(engine,mode):
    require(mode in ('mock','hardware'),'Unknown mode',422)
    path=engine.storage.root/('assignments-'+mode+'.json')
    if path.exists():return read_json(path)
    return {'mode':mode,'method':'assigned','seed':None,'assignments':{f'P{i:03d}':f'T{i:02d}' for i in range(1,31)}}

def save_plan(engine,mode,seed):
    with engine.lock:
        require(mode in ('mock','hardware'),'Unknown mode',422)
        require(not any(s['mode']==mode and s.get('task_mode')=='figma_external' for s in engine.sessions.values()),'Assignment is locked after the first session; existing data must not be reassigned')
        require(seed is None or type(seed) is int and 0<=seed<2**32,'Seed must be a 32-bit nonnegative integer',422)
        tracks=[f'T{i:02d}' for i in range(1,31)]
        if seed is not None:random.Random(seed).shuffle(tracks)
        result={'mode':mode,'method':'random_without_replacement' if seed is not None else 'assigned','seed':seed,'created_at':utc(),'assignments':{f'P{i:03d}':t for i,t in enumerate(tracks,1)}}
        atomic_json(engine.storage.root/('assignments-'+mode+'.json'),result)
        return result
