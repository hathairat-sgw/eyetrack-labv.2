import pytest
from backend.engine import Engine,LabError
from backend.models import CreateSession,CalibrationPoint

def test_new_workflow_calibration_then_pre(tmp_path):
    e=Engine(tmp_path,tmp_path/'config.json')
    sid=e.create(CreateSession(participant_id=e.add_participant()['participant_id'],task_ids=['demo-find']))['session_id']
    e.step(sid,'information');e.step(sid,'consent')
    assert e.get(sid)['state']=='calibration'
    with pytest.raises(LabError):e.answers(sid,'pre',{'department':'ข้อมูลทดสอบ','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
    e.calibration_start(sid)
    for i in range(5):e.calibration_point(sid,CalibrationPoint(index=i,viewport={'fullscreen':True},presented_at=i))
    assert e.get(sid)['state']=='pre'
    e.answers(sid,'pre',{'department':'ข้อมูลทดสอบ','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
    assert e.get(sid)['state']=='instructions'
    assert Engine(tmp_path,tmp_path/'config.json').get(sid)['workflow_version']=='calibration-before-pre-v1'
