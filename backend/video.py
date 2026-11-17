"""Ordered local screen-video chunks. A partial recording is never marked complete."""
import copy
import hashlib
import json
import os
import uuid
from .engine import require,utc,now_us

class Video:
    def __init__(self, engine):self.e=engine
    def start(self,sid,metadata):
        with self.e.lock:
            s=copy.deepcopy(self.e.get(sid))
            require(s['consent'] and s['state'] in ('instructions','recording'), 'เริ่มวิดีโอหลังยินยอมและก่อนทำงานเท่านั้น')
            require(not any(v['status']=='recording' for v in s.get('videos',[])), 'มีวิดีโอกำลังบันทึก')
            require(len(json.dumps(metadata))<20000,'Video metadata ใหญ่เกินไป',422)
            cid=uuid.uuid4().hex
            item={'capture_id':cid,'filename':cid+'.webm','status':'recording','started_at':utc(),'backend_start_received_us':now_us(),
                  'clock_segment_id':self.e.clock_segment_id,'metadata':metadata,'chunks':[], 'bytes':0,
                  'timing_note':'browser MediaRecorder start event and clock estimates; not frame-accurate hardware synchronization'}
            s.setdefault('videos',[]).append(item)
            (self.e.storage.session_path(s)/(cid+'.webm.part')).touch(exist_ok=False)
            self.e.commit(s)
            return item
    def chunk(self,sid,cid,index,data):
        with self.e.lock:
            s=copy.deepcopy(self.e.get(sid));require(s['consent'] and s['state']!='withdrawn','หยุดรับวิดีโอแล้ว')
            v=next((v for v in s.get('videos',[]) if v['capture_id']==cid),None)
            require(v and v['status']=='recording','ไม่พบการบันทึกวิดีโอ')
            require(0<len(data)<=8*1024*1024,'ขนาด chunk ไม่ถูกต้อง',422)
            digest=hashlib.sha256(data).hexdigest()
            if 0<=index<len(v['chunks']):
                require(v['chunks'][index]['sha256']==digest,'Chunk เดิมมีข้อมูลต่างกัน')
                return {'ok':True,'index':index}
            require(index==len(v['chunks']),'ลำดับวิดีโอไม่ต่อเนื่อง')
            require(v['bytes']+len(data)<=1024*1024*1024,'วิดีโอเกิน 1 GB กรุณาหยุดและเริ่มคลิปใหม่')
            path=self.e.storage.session_path(s)/(cid+'.webm.part')
            require(path.stat().st_size==v['bytes'],'ขนาดไฟล์วิดีโอไม่ตรง manifest ให้หยุดคลิปและเก็บเป็น incomplete')
            with path.open('ab') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
            v['chunks'].append({'index':index,'bytes':len(data),'sha256':digest,'received_us':now_us()});v['bytes']+=len(data)
            self.e.commit(s);return {'ok':True,'index':index}
    def finish(self,sid,cid,metadata):
        with self.e.lock:
            s=copy.deepcopy(self.e.get(sid));v=next((v for v in s.get('videos',[]) if v['capture_id']==cid),None)
            require(v,'ไม่พบวิดีโอ',404)
            if v['status']!='recording':return v
            require(len(json.dumps(metadata))<20000,'Video metadata ใหญ่เกินไป',422)
            path=self.e.storage.session_path(s)/(cid+'.webm.part')
            complete=bool(v['chunks']) and metadata.get('complete') is True and s['state']!='withdrawn' and path.stat().st_size==v['bytes']
            v.update(status='completed' if complete else 'incomplete',ended_at=utc(),backend_end_received_us=now_us(),end_metadata=metadata)
            if complete:os.replace(path,path.with_suffix(''))
            self.e.commit(s);return v
