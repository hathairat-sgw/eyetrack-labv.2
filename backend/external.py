import copy,re,time,uuid
from urllib.parse import urlparse,parse_qs
from .engine import require,utc
from .models import CreateSession
from .storage import read_json,atomic_json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def valid_url(url):
    p=urlparse(url)
    require(p.scheme=='https' and p.hostname=='www.figma.com' and not p.username and not p.password and p.port in (None,443) and re.match(r'^/proto/[A-Za-z0-9]+/',p.path) and bool(parse_qs(p.query).get('node-id')), 'ต้องเป็น HTTPS www.figma.com/proto URL พร้อม node-id',422)
    return url

def public_session(s):
    if s.get('task_mode')!='figma_external':return copy.deepcopy(s)
    result=copy.deepcopy(s)
    result.pop('external',None);result.pop('audit',None);result.pop('condition',None)
    result.pop('videos',None);result.pop('validation_attempts',None)
    if result.get('validation'):
        for point in result['validation'].get('points',[]):point.pop('samples',None)
    if s['task_index'] < 4:
        r=s['external']['rounds'][s['task_index']]
        result['external_task']={'test_index':r['test_index'],'course_id':r['course_id'],'prototype_url':r['prototype_url']}

    result['tasks']=[{'id':t['id'],'name':'ภารกิจ '+str(i+1),'instruction':'ทำภารกิจตามคำชี้แจงในหน้าต้นแบบ'} for i,t in enumerate(s['tasks'])]
    result['snapshot'].pop('tasks',None)
    for t in result['trials']:
        for k in ['variant_id','prototype_url','starting_node_id','expected_late','expected_quiz','decision_error']:t.pop(k,None)
    return result

class External:
    def __init__(self,e):self.e=e;self.controllers={}
    def prototypes(self):
        p=self.e.storage.root/'prototypes.json'
        d=read_json(p if p.exists() else ROOT/'config/figma-links.json')
        for v in d['variants']:
            parts=re.findall(r'(Menu|Button|Status|Search)\((HS|LS)\)',v['name'])
            v['components']=[{'element':c,'quality':'Good' if q=='HS' else 'Bad','source_level':q} for c,q in parts]
            levels=[q for _,q in parts]
            v['condition']='baseline' if not levels else 'GG' if levels==['HS','HS'] else 'BB' if levels==['LS','LS'] else 'GB'
            v.setdefault('link_status','unverified')
            v.setdefault('variant_id','baseline' if not parts else re.sub(r'[^a-z0-9]+','-',v['name'].lower()).strip('-'))
        return d
    def update(self,name,url,status):
        valid_url(url);require(status in ('unverified','verified','broken'),'สถานะไม่ถูกต้อง',422)
        d=self.prototypes();v=next((v for v in d['variants'] if v['name']==name),None);require(v,'ไม่พบ variant',404)
        v.update(url=url,starting_node_id=parse_qs(urlparse(url).query)['node-id'][0],link_status=status,checked_at=utc() if status=='verified' else None)
        atomic_json(self.e.storage.root/'prototypes.json',d);return d
    def catalog(self,mode=None):
        d=read_json(ROOT/'config/tracks.json')
        for t in d['tracks']:
            sessions=[s for s in self.e.sessions.values() if s.get('external',{}).get('track_id')==t['track_id'] and s['state']!='withdrawn' and (mode is None or s['mode']==mode)]
            t['allocations']=[{'session_id':s['session_id'],'participant_id':s['participant_id'],'status':'completed' if s['state']=='completed' else 'in_progress' if s['consent'] else 'reserved'} for s in sessions]
            t['allocation_status']=t['allocations'][-1]['status'] if sessions else 'available'
        return d
    def create(self,pid,track_id,mode="mock",limits=None,native_mouse=False):
        with self.e.lock:
            require(mode in ("mock","hardware"), "โหมดไม่ถูกต้อง",422)
            if mode=="hardware":
                require(self.e.config["protocol"]["approved"], "ตรวจข้อความยินยอมและยืนยัน protocol ใน Questionnaires ก่อนใช้ Tobii จริง")
                require(self.e.devices["hardware"].status().get("connected"), "ไม่พบ Tobii บนเครื่องนี้ ตรวจสายและ Eye Tracker Manager")
            track=next((t for t in self.catalog(mode)['tracks'] if t['track_id']==track_id),None)
            require(track and track['allocation_status']=='available','Track ไม่ว่างหรือไม่พบ')
            task_id=next((t['id'] for t in self.e.config['tasks'] if t['enabled'] and t['route']=='/stimuli/demo'),None)
            require(task_id is not None,'ต้องมี Demo fixture ที่เปิดใช้งานสำหรับ bootstrap session',422)
            links={v['name']:v for v in self.prototypes()['variants']}
            rounds=[]
            registry=read_json(ROOT/'config/tracks.json')
            for r in track['rounds']:
                v=links.get(r['figma_variant']);require(v,'ไม่พบ prototype ของ '+r['figma_variant'],422);valid_url(v['url'])
                key=registry['round_reference'][r['test_index']]
                rounds.append({**r,'starting_node_id':v['starting_node_id'],'prototype_url':v['url'],'link_status':v.get('link_status','unverified'),'expected_late':key['late'],'expected_quiz':key['quiz_pending']})
            s=self.e.create(CreateSession(participant_id=pid,task_ids=[task_id],mode=mode),external_authorized=True)
            s.update(mode=mode,schema_version=2,task_mode='figma_external',external={'track_id':track_id,'group':track['group'],'duplicate_of':track['copy_of'],'configuration_version':registry['version'],'rounds':rounds},audit=[],stimulus_status='external_figma_manual_telemetry_unavailable')
            if mode=="hardware":
                from .quality import DEFAULT_LIMITS
                s['validation_limits']=copy.deepcopy(limits or DEFAULT_LIMITS)
                s['native_mouse']=native_mouse
            s['tasks']=[dict(id='external-'+str(i),name='Test '+str(i),instruction='ทำภารกิจใน Figma',route='/stimuli/figma-external',target='manual',completion='manual',time_limit=None) for i in range(4)]
            return self.e.commit(s)
    def beat(self,sid,client):
        with self.e.lock:
            self.e.get(sid);current=self.controllers.get(sid)
            require(not current or current['client']==client or time.monotonic()-current['heartbeat']>15,'มีศูนย์ควบคุมอื่นใช้งาน session นี้')
            self.controllers[sid]={'client':client,'heartbeat':time.monotonic()}
            return {'ok':True}
    def start(self,sid,client,checks):
        with self.e.lock:
            s=self.e.get(sid);require(s.get('task_mode')=='figma_external','โหมดไม่ตรง')
            require(all(checks.get(k) is True for k in ['starting_frame','display','fullscreen','hints_off']),'ยืนยันหน้าตั้งต้น จอ fullscreen และ hints ก่อน')
            require(s['state']=='instructions' and 0 <= s['task_index'] < 4,'รอบนี้ยังไม่พร้อมเริ่มหรือสิ้นสุดแล้ว')
            r=s['external']['rounds'][s['task_index']];require(r['link_status']=='verified','ต้องตรวจลิงก์ก่อนเริ่ม')
            self.beat(sid,client)
            # Existing engine client guard uses controller for external recording only.
            previous=self.e.clients.get(sid)
            self.e.clients[sid]={'client':client,'heartbeat':time.monotonic()}
            try: result=self.e.start_trial(sid,client,external_authorized=True)
            finally:
                if previous:self.e.clients[sid]=previous
                else:self.e.clients.pop(sid,None)
            result=copy.deepcopy(result)
            result['trials'][-1].update(track_id=s['external']['track_id'],group=s['external']['group'],test_index=s['task_index'],variant_id=r['variant_id'],course_id=r['course_id'],prototype_url=r['prototype_url'],starting_node_id=r['starting_node_id'],configuration_version=s['external']['configuration_version'],attempt=1+sum(t['task_id']==result['trials'][-1]['task_id'] for t in result['trials'][:-1]),simulated=s["mode"]!="hardware",started_at=utc(),start_trigger='researcher_manual',figma_events='unavailable',checks=checks)
            return self.e.commit(result)
    def end(self,sid,client):
        with self.e.lock:
            self.beat(sid,client);s=self.e.get(sid);require(s['state']=='recording','ไม่ได้บันทึก')
            require(self.controllers[sid]['client']==client,'controller ไม่ตรง')
            result=self.e.end_trial(sid,'awaiting_answers')
            result['trials'][-1].update(ended_at=utc(),end_trigger='researcher_manual')
            return self.e.commit(result)
    def answer(self,sid,late,quiz):
        with self.e.lock:
            s=copy.deepcopy(self.e.get(sid));require(s['state']=='external_answers','รอบนี้ไม่รอคำตอบ')
            require(type(late) is int and type(quiz) is int and late>=0 and quiz>=0,'คำตอบต้องเป็นจำนวนเต็มตั้งแต่ 0',422)
            r=s['external']['rounds'][s['task_index']]
            s['trials'][-1].update(late_answer=late,quiz_answer=quiz,expected_late=r['expected_late'],expected_quiz=r['expected_quiz'],decision_error=int((late,quiz)!=(r['expected_late'],r['expected_quiz'])),status='completed',answered_at=utc())
            s['audit'].append({'action':'answer','actor':'researcher','at':utc(),'trial_id':s['trials'][-1]['trial_id']})
            s['task_index']+=1;s['state']='post' if s['task_index']==4 else 'instructions'
            return self.e.commit(s)

    def reset(self,sid,reason):
        with self.e.lock:
            s=copy.deepcopy(self.e.get(sid))
            require(s.get('task_mode')=='figma_external' and s['state']=='external_answers','รีเซ็ตได้เฉพาะรอบปัจจุบันที่หยุดบันทึกแล้ว')
            require(isinstance(reason,str) and reason.strip(),'ต้องระบุเหตุผล',422)
            s['audit'].append({'action':'reset_current_round','actor':'researcher','at':utc(),'reason':reason,'previous_trial':copy.deepcopy(s['trials'][-1])})
            s['trials'][-1].update(status='incomplete',reason='researcher_reset: '+reason)
            s['state']='instructions'
            return self.e.commit(s)
    def release(self,sid,reason):
        with self.e.lock:
            s=copy.deepcopy(self.e.get(sid))
            require(s.get('task_mode')=='figma_external' and not s['consent'],'ปล่อยได้เฉพาะ reservation ที่ยังไม่ยินยอม')
            require(isinstance(reason,str) and reason.strip(),'ต้องระบุเหตุผล',422)
            s['audit'].append({'action':'release','actor':'researcher','at':utc(),'reason':reason})
            s['state']='withdrawn';s['withdrawn_at']=utc()
            return self.e.commit(s)
    def amend(self,sid,trial_id,late,quiz,reason):
        with self.e.lock:
            s=copy.deepcopy(self.e.get(sid))
            require(s.get('task_mode')=='figma_external' and self.e.active!=sid,'หยุด recording ก่อนแก้คำตอบ')
            require(isinstance(reason,str) and reason.strip(),'ต้องระบุเหตุผล',422)
            require(type(late) is int and type(quiz) is int and min(late,quiz)>=0,'คำตอบต้องเป็นจำนวนเต็มตั้งแต่ 0',422)
            t=next((t for t in s['trials'] if t['trial_id']==trial_id),None)
            require(t and t['status']=='completed','ไม่พบรอบที่ส่งคำตอบแล้ว')
            s['audit'].append({'action':'amend_answer','actor':'researcher','at':utc(),'reason':reason,'previous_trial':copy.deepcopy(t)})
            t.update(late_answer=late,quiz_answer=quiz,decision_error=int((late,quiz)!=(t['expected_late'],t['expected_quiz'])),answered_at=utc())
            return self.e.commit(s)

    def quick_start(self,track_id,mode="mock",limits=None,native_mouse=False):
        with self.e.lock:
            track=next((t for t in self.catalog(mode)['tracks'] if t['track_id']==track_id),None)
            require(track,'ไม่พบ Track',404)
            if track['allocations']:
                existing=self.e.get(track['allocations'][-1]['session_id'])
                require(existing['mode']==mode, 'คนนี้มี session โหมด '+existing['mode']+' แล้ว เลือกโหมดให้ตรงก่อนทำต่อ')
                return copy.deepcopy(existing)
            # Check hardware before allocating a participant; no orphan on missing device.
            require(mode in ('mock','hardware'),'โหมดไม่ถูกต้อง',422)
            if mode=='hardware':
                require(self.e.config['protocol']['approved'],'ตรวจและยืนยัน protocol ใน Questionnaires ก่อนใช้ Tobii จริง')
                require(self.e.devices['hardware'].status().get('connected'),'ไม่พบ Tobii บนเครื่องนี้')
            p=self.e.add_participant()
            return self.create(p['participant_id'],track_id,mode,limits,native_mouse)
