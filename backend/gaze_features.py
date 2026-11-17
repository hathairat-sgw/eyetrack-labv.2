"""Derived gaze features adapted from user's collect_data.py; raw CSV is unchanged.
The <30px movement rule is exploratory, not a validated fixation classifier.
"""
import math,json

def derive_gaze(rows,session,threshold_px=30):
    trials={t['trial_id']:t for t in session['trials']}
    previous={};result=[]
    for row in rows:
        t=trials[row['trial_id']]
        metadata=session['metadata'][t.get('metadata_index',0)] if session['metadata'] else {}
        viewport=metadata.get('viewport',{})
        width,height=viewport.get('screen_width'),viewport.get('screen_height')
        raw=json.loads(row['raw_json']);points=[]
        for eye in ['left','right']:
            point=raw.get(eye+'_gaze_point_on_display_area')
            if raw.get(eye+'_gaze_point_validity')==1 and isinstance(point,(list,tuple)) and len(point)==2 and all(type(v) in (int,float) and math.isfinite(v) for v in point):points.append(point)
        value={k:row[k] for k in ['participant_id','session_id','trial_id','task_id','mode','backend_received_us']}
        value.update(gaze_x_px='',gaze_y_px='',step_distance_px='',stationary_candidate_ms='',left_pupil_mm='',right_pupil_mm='',method='exploratory_step_under_30px_v1',threshold_px=threshold_px,display_mapping_verified=False,coordinate_space='browser_screen_css_pixels_estimate',device_pixel_ratio=viewport.get('device_pixel_ratio',''),mapping_note='Not directly interchangeable with native mouse physical pixels')
        for eye in ['left','right']:
            pupil=raw.get(eye+'_pupil_diameter')
            if raw.get(eye+'_pupil_validity')==1 and type(pupil) in (int,float) and math.isfinite(pupil):value[eye+'_pupil_mm']=pupil
        if points and type(width) in (int,float) and type(height) in (int,float) and width>0 and height>0:
            x=sum(p[0] for p in points)/len(points)*width;y=sum(p[1] for p in points)/len(points)*height;now=int(row['backend_received_us'])
            last=previous.get(row['trial_id']);distance=math.hypot(x-last[0],y-last[1]) if last else None
            since=last[2] if last and distance<threshold_px else now
            value.update(gaze_x_px=x,gaze_y_px=y,step_distance_px=distance if distance is not None else '',stationary_candidate_ms=(now-since)/1000)
            previous[row['trial_id']]=(x,y,since)
        else:previous.pop(row['trial_id'],None)
        result.append(value)
    return result
