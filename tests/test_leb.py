import copy
import io
import json
import zipfile
import pytest
from test_research import lab, ready, event
from backend.models import Config, CreateSession
from backend.engine import LabError, Engine
from backend.exporting import export_sessions

def make(lab, **changes):
    config = copy.deepcopy(lab.config)
    config['tasks'].append(dict(id='leb-status-search',name='Status(LS)+Search(HS)',instruction='Mock flow',route='/stimuli/leb-status-search',target='leb-submit',completion='target_click',targets=[],enabled=True,source_verified=False))
    lab.update_config(Config.model_validate(config))
    request=dict(participant_id=lab.add_participant()['participant_id'],task_ids=['leb-status-search'],condition='mixed')
    request.update(changes)
    created=lab.create(CreateSession(**request));created.pop('workflow_version',None);lab.commit(created)
    return created['session_id']

def test_leb_mock_submit_export_restart(lab):
    sid=make(lab,seed=17)
    ready(lab,sid)
    lab.start_trial(sid,'client')
    lab.events(sid,'client',[event(lab,sid,target='leb-quiz',event_id='quiz')])
    with pytest.raises(LabError): lab.complete_trial(sid,'client')
    lab.events(sid,'client',[event(lab,sid,target='leb-submit',event_id='submit')])
    lab.complete_trial(sid,'client')
    lab.answers(sid,'post',{'ease':4,'feedback':'Mock LEB'})
    lab.step(sid,'finish')
    archive=zipfile.ZipFile(io.BytesIO(export_sessions(lab,[sid])))
    saved=json.loads(archive.read(next(n for n in archive.namelist() if n.endswith('/session.json'))))
    assert saved['stimulus_status']=='figma_flow_mock_visual_unverified'
    assert saved['condition']=='mixed' and saved['mode']=='mock' and saved['seed']==17
    assert not saved['tasks'][0]['source_verified']
    assert Engine(lab.storage.root,lab.config_path).get(sid)['state']=='completed'

@pytest.mark.parametrize('changes',[{'condition':'good'},{'condition':'bad'},{'random_targets':True},{'mode':'hardware'}])
def test_leb_rejects_misleading_conditions(lab,changes):
    with pytest.raises(LabError): make(lab,**changes)
