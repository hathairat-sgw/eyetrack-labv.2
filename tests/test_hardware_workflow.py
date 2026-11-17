"""Contract tests with an explicitly fake adapter; these do NOT validate physical Tobii."""
import copy, io, json, zipfile
import pytest
from backend.engine import Engine, LabError, now_us
from backend.external import External
from backend.devices import MockDevice
from backend.models import CalibrationPoint
from backend.validation import Validation
from backend.quality import VALIDATION_POINTS, DEFAULT_LIMITS, point_metrics
from backend.exporting import export_sessions

VIEW={"fullscreen":True,"width":1920,"height":1080,"screen_width":1920,"screen_height":1080,"scale":1,"screen_x":0,"screen_y":0,"device_pixel_ratio":1}
CHECKS=dict(starting_frame=True,display=True,fullscreen=True,hints_off=True)
class FakeTobii(MockDevice):
    def __init__(self):
        super().__init__();self.serial="TEST-FAKE";self.target=(.5,.5);self.connected=True;self.count=30
    def status(self):return {"connected":self.connected,"simulated":False,"serial":self.serial,"model":"TEST DOUBLE, not hardware"}
    def finish_calibration(self):return {"success":True,"simulated":False,"sdk_status":"fake-success"}
    def clock_sample(self):return {"sdk_system_us":now_us(),"backend_midpoint_us":now_us(),"uncertainty_us":1}
    def start(self, callback):
        for i in range(self.count):
            stamp=now_us()+i*16667
            callback({"device_time_stamp":stamp,"system_time_stamp":stamp,
                "left_gaze_point_on_display_area":self.target,"right_gaze_point_on_display_area":self.target,
                "left_gaze_point_validity":1,"right_gaze_point_validity":1})

def prepared(tmp_path):
    e=Engine(tmp_path,tmp_path/'configuration.json');d=FakeTobii();e.devices['hardware']=d;e.config['protocol']['approved']=True
    x=External(e);e.external=x
    for p in x.prototypes()['variants']:x.update(p['name'],p['url'],'verified')
    s=x.quick_start('T01','hardware');sid=s['session_id']
    assert s['mode']=='hardware' and not list((tmp_path/'mock').rglob('session.json'))
    e.attach(sid,'p');e.step(sid,'information');e.step(sid,'consent');e.calibration_start(sid)
    for i in range(5):e.calibration_point(sid,CalibrationPoint(index=i,viewport=VIEW,presented_at=i))
    assert e.get(sid)['state']=='validation'
    v=Validation(e);v.capture_seconds=0
    return e,x,d,v,sid

def validate(e,d,v,sid,shift=0):
    v.start(sid)
    for i,target in enumerate(VALIDATION_POINTS):
        d.target=(target[0]+shift,target[1])
        v.point(sid,CalibrationPoint(index=i,viewport=VIEW,presented_at=i))

def test_hardware_validation_record_export_and_restart(tmp_path):
    e,x,d,v,sid=prepared(tmp_path);validate(e,d,v,sid)
    assert e.get(sid)['state']=='pre'
    e.answers(sid,'pre',{'department':'QA','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
    e.metadata(sid,{'viewport':VIEW,'synchronization':[]})
    for i in range(4):
        x.start(sid,'r',CHECKS);e.drain();assert e.get(sid)['trials'][-1]['gaze_count']==30
        x.end(sid,'r');x.answer(sid,1,2)
    e.answers(sid,'post',{q['id']:4 for q in e.get(sid)['snapshot']['post']['questions'] if q['type']=='likert'})
    e.step(sid,'finish')
    z=zipfile.ZipFile(io.BytesIO(export_sessions(e,[sid])))
    assert all(n.startswith('hardware/') for n in z.namelist())
    report=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/quality_report.json'))))
    assert not report['simulated'] and report['validation_passed'] and len(report['trials'])==4
    assert all(t['sample_count']==30 and t['valid_fraction']['left']==1 for t in report['trials'])
    assert all(t['simulated'] is False for t in e.get(sid)['trials'])
    restarted=Engine(tmp_path,tmp_path/'configuration.json')
    assert restarted.get(sid)['state']=='completed'
    assert len(restarted.sessions)==1

def test_validation_failure_retry_preserves_evidence(tmp_path):
    e,x,d,v,sid=prepared(tmp_path);validate(e,d,v,sid,shift=.2)
    assert e.get(sid)['state']=='validation' and not e.get(sid)['validation']['passed']
    validate(e,d,v,sid)
    assert e.get(sid)['validation']['passed'] and len(e.get(sid)['validation_attempts'])==1
    assert not e.get(sid)['validation_attempts'][0]['passed']

def test_display_order_empty_stream_and_identity_guards(tmp_path):
    e,x,d,v,sid=prepared(tmp_path);v.start(sid)
    with pytest.raises(LabError):v.point(sid,CalibrationPoint(index=1,viewport=VIEW,presented_at=0))
    with pytest.raises(LabError):v.point(sid,CalibrationPoint(index=0,viewport={**VIEW,'fullscreen':False},presented_at=0))
    d.count=0
    for i in range(5):v.point(sid,CalibrationPoint(index=i,viewport=VIEW,presented_at=i))
    assert not e.get(sid)['validation']['passed']
    d.serial='different'
    with pytest.raises(LabError):v.start(sid)

def test_recording_requires_current_validation_and_same_device(tmp_path):
    e,x,d,v,sid=prepared(tmp_path);validate(e,d,v,sid)
    e.answers(sid,'pre',{'department':'QA','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
    e.metadata(sid,{'viewport':VIEW,'synchronization':[]})
    d.serial='different'
    with pytest.raises(LabError):x.start(sid,'r',CHECKS)
    d.serial='TEST-FAKE';e.clock_segment_id='restart'
    with pytest.raises(LabError):x.start(sid,'r',CHECKS)

def test_missing_device_does_not_allocate_and_mode_is_immutable(tmp_path):
    e=Engine(tmp_path,tmp_path/'configuration.json');e.config['protocol']['approved']=True
    d=FakeTobii();d.connected=False;e.devices['hardware']=d;x=External(e)
    with pytest.raises(LabError):x.quick_start('T01','hardware')
    assert not e.participants and not e.sessions
    x.quick_start('T01')
    with pytest.raises(LabError):x.quick_start('T01','hardware')

def test_invalid_gaze_is_never_a_validation_pass():
    data=[{'left_gaze_point_on_display_area':[float('nan'),.5],'right_gaze_point_on_display_area':[.5,.5], 'left_gaze_point_validity':1,'right_gaze_point_validity':0}]*30
    assert not point_metrics(data,(.5,.5),DEFAULT_LIMITS)['passed']


def test_native_mouse_queue_is_scoped_to_trial_and_exported(tmp_path):
    e,x,d,v,sid=prepared(tmp_path);validate(e,d,v,sid)
    e.answers(sid,'pre',{'department':'QA','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
    e.metadata(sid,{'viewport':VIEW,'synchronization':[]})
    class FakeMouse:
        overflow=False
        def __init__(self):self.stopped=False;self.rows=[]
        def start(self):
            self.rows=[dict(event_type='button',backend_us=now_us(),screen_x=100,screen_y=200,button='left',pressed=True,scroll_dx='',scroll_dy='',foreground_title='TEST Figma',coordinate_space='test_pixels',source='test',page_url='unavailable',target_element_id='unavailable')]
        def stop(self):self.stopped=True
        def healthy(self):return not self.stopped
        def drain(self, limit=240):
            data,self.rows=self.rows,[]
            return iter(data)
    e.mouse_factory=FakeMouse;e.get(sid)['native_mouse']=True
    x.start(sid,'r',CHECKS);listener=e.mouse;e.drain();x.end(sid,'r')
    assert listener.stopped and e.mouse is None
    z=zipfile.ZipFile(io.BytesIO(export_sessions(e,[sid])))
    data=z.read(next(n for n in z.namelist() if n.endswith('/mouse.csv'))).decode('utf-8-sig')
    assert 'TEST Figma' in data and e.get(sid)['trials'][-1]['trial_id'] in data

def test_recalibration_and_stop_invalidate_validation(tmp_path):
    e,x,d,v,sid=prepared(tmp_path);validate(e,d,v,sid)
    e.stop(sid)
    assert e.get(sid)['state']=='calibration' and not e.get(sid)['validation']['passed']
    e.calibration_start(sid)
    assert 'validation' not in e.get(sid)


def test_mock_allocation_does_not_consume_hardware_track(tmp_path):
 e=Engine(tmp_path,tmp_path/'configuration.json');e.config['protocol']['approved']=True
 e.devices['hardware']=FakeTobii();x=External(e)
 mock=x.quick_start('T01');hardware=x.quick_start('T01','hardware')
 assert mock['session_id']!=hardware['session_id']
 assert len(x.catalog('mock')['tracks'][0]['allocations'])==1
 assert len(x.catalog('hardware')['tracks'][0]['allocations'])==1


def test_missing_gaze_stops_hardware_trial_incomplete(tmp_path):
 e,x,d,v,sid=prepared(tmp_path);validate(e,d,v,sid)
 e.answers(sid,'pre',{'department':'QA','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
 e.metadata(sid,{'viewport':VIEW,'synchronization':[]})
 x.start(sid,'r',CHECKS);e.drain();e.last_gaze_us=now_us()-4000000;e.tick()
 assert e.active is None and e.get(sid)['state']=='interrupted'
 assert e.get(sid)['trials'][-1]['reason']=='gaze_stream_lost'
 assert e.get(sid)['trials'][-1]['gaze_count']==30
