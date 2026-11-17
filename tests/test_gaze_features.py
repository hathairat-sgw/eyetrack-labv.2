import json
from backend.gaze_features import derive_gaze

def test_features_respect_validity_gaps_trial_and_raw():
 s={'trials':[{'trial_id':'t','metadata_index':0}],'metadata':[{'viewport':{'screen_width':1920,'screen_height':1080}}]}
 raw={'left_gaze_point_on_display_area':[.5,.5],'left_gaze_point_validity':1,'right_gaze_point_on_display_area':[.9,.9],'right_gaze_point_validity':0,'left_pupil_diameter':3.25,'left_pupil_validity':1}
 def row(ts,data):return dict(participant_id='P001',session_id='S1',trial_id='t',task_id='external-0',mode='hardware',backend_received_us=str(ts),raw_json=json.dumps(data))
 rows=[row(1000,raw),row(11000,raw),row(21000,{}),row(31000,raw)]
 before=json.dumps(rows);f=derive_gaze(rows,s)
 assert f[0]['gaze_x_px']==960 and f[0]['left_pupil_mm']==3.25
 assert f[1]['stationary_candidate_ms']==10
 assert f[2]['gaze_x_px']=='' and f[3]['stationary_candidate_ms']==0
 assert not f[0]['display_mapping_verified'] and json.dumps(rows)==before
