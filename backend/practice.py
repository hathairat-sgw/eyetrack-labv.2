"""Practice evidence is metadata, never appended to research trials or gaze."""
import copy
from .engine import require, utc
VERSION='calibration-practice-pre-v2'
REQUIRED={'button','menu','search','status'}

def after_calibration(s):
    if s.get('workflow_version')==VERSION and not s.get('practice_completed'):
        return 'practice'
    return 'pre' if 'pre' not in s['responses'] else 'instructions'

def practice_action(engine,sid,action):
    with engine.lock:
        s=copy.deepcopy(engine.get(sid))
        require(s.get('workflow_version')==VERSION and s['consent'], 'Practice is unavailable for this legacy session')
        if action=='restart':
            require(s['state'] in ('practice','pre','instructions') and not s['trials'], 'Repeat practice before submitting Pre-test')
            s['state']='practice';s['practice_completed']=False
            s.setdefault('practice_attempts',[]).append({'started_at':utc(),'events':[]})
        elif action in REQUIRED:
            require(s['state']=='practice','Not in practice')
            if not s.get('practice_attempts'):s['practice_attempts']=[{'started_at':utc(),'events':[]}]
            s['practice_attempts'][-1]['events'].append({'action':action,'timestamp':utc(),'source':'native_practice_ui'})
        elif action=='complete':
            require(s['state']=='practice','Not in practice')
            evidence=s.get('practice_attempts',[])
            require(evidence and REQUIRED <= {v['action'] for v in evidence[-1]['events']},'Complete all four practice interactions first')
            evidence[-1]['completed_at']=utc();s['practice_completed']=True;s['state']='instructions' if 'pre' in s['responses'] else 'pre'
        else: require(False,'Unknown practice action',422)
        return engine.commit(s)
