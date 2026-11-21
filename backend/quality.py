"""Measured quality only; normalized distances are not visual-angle accuracy."""
import math
from statistics import mean

VALIDATION_POINTS = [(0.2,0.2),(0.8,0.2),(0.2,0.8),(0.8,0.8),(0.5,0.5)]
DEFAULT_LIMITS = {"max_mean_error_norm": 0.04, "min_valid_fraction": 0.7, "min_samples": 20}

def valid_point(sample, eye):
    point = sample.get(eye + "_gaze_point_on_display_area", [])
    return (sample.get(eye + "_gaze_point_validity") == 1 and len(point) == 2
            and all(isinstance(v,(int,float)) and math.isfinite(v) for v in point))

def check_display(view):
    return (view.get("fullscreen") is True and view.get("width",0)>0 and view.get("height",0)>0
            and abs(view.get("width",0)-view.get("screen_width",-999)) <= 2
            and abs(view.get("height",0)-view.get("screen_height",-999)) <= 2
            and view.get("scale",1) == 1)

def point_metrics(samples, target, limits):
    result = {"sample_count":len(samples), "target":list(target)}
    for eye in ("left","right"):
        points=[s[eye+"_gaze_point_on_display_area"] for s in samples if valid_point(s,eye)]
        fraction=len(points)/len(samples) if samples else 0
        error=mean(math.hypot(x-target[0],y-target[1]) for x,y in points) if points else None
        result[eye]={"valid_count":len(points),"valid_fraction":fraction,"mean_error_norm":error,
                     "mean_gaze": [mean(p[i] for p in points) for i in (0,1)] if points else None}
    result["passed"] = (len(samples)>=limits["min_samples"] and all(
        result[e]["valid_fraction"]>=limits["min_valid_fraction"] and result[e]["mean_error_norm"] is not None
        and result[e]["mean_error_norm"]<=limits["max_mean_error_norm"] for e in ("left","right")))
    return result

def quality_report(session, rows):
    trials=[]
    for trial in session["trials"]:
        data=[r for r in rows if r["trial_id"]==trial["trial_id"]]
        times=[float(r["system_timestamp"]) for r in data if r.get("system_timestamp") not in (None,"")]
        counts={e:sum(str(r.get(e+"_validity")) in ("1","True") and all(_finite(r.get(e+"_gaze_"+axis)) for axis in ("x","y")) for r in data) for e in ("left","right")}
        trials.append({"trial_id":trial["trial_id"],"sample_count":len(data),"first_sdk_system_us":times[0] if times else None,
          "last_sdk_system_us":times[-1] if times else None,"timestamps_monotonic":all(b>a for a,b in zip(times,times[1:])),
          "observed_hz":(len(times)-1)*1e6/(times[-1]-times[0]) if len(times)>1 and times[-1]>times[0] else None,
          "valid_fraction":{e:counts[e]/len(data) if data else 0 for e in counts},"status":trial["status"],
          "device":trial.get("device"),"clock_segment_id":trial.get("clock_segment_id")})
    warnings=[]
    if not session.get('validation',{}).get('passed'):warnings.append('calibration_not_independently_verified')
    if session.get('mode')!='hardware':warnings.append('DEMO_DATA_NOT_RESEARCH')
    if session['state']!='completed':warnings.append('session_incomplete')
    missing_tasks=[t['id'] for t in session['tasks'] if not any(r['task_id']==t['id'] and r['status']=='completed' for r in session['trials'])]
    if missing_tasks:warnings.append('missing_or_incomplete_tasks')
    if any(not t['timestamps_monotonic'] for t in trials):warnings.append('nonmonotonic_sdk_timestamps')
    if not rows:warnings.append('no_gaze_samples')
    if session.get('task_mode')=='figma_external':warnings.append('figma_dom_interaction_capture_unavailable')
    for phase in ('pre','post'):
        if phase not in session['responses']:warnings.append(phase+'_questionnaire_missing')
    for detail,trial in zip(trials,session['trials']):
        hz=(trial.get('device') or {}).get('configured_hz',60 if session['mode']=='mock' else None)
        duration=trial.get('duration_ms')
        expected=hz*duration/1000 if hz and duration is not None else None
        detail.update(duration_ms=duration,configured_hz=hz,expected_samples=expected,missing_sample_estimate=max(0,expected-detail['sample_count']) if expected is not None else None)
        if expected and detail['sample_count']<expected*.8:warnings.append('low_sample_count:'+trial['trial_id'])
    disconnects=[{'trial_id':t['trial_id'],'reason':t.get('reason')} for t in session['trials'] if any(word in t.get('reason','') for word in ('disconnect','gaze_timeout','device'))]
    if disconnects:warnings.append('device_or_stream_interruption')
    valid_samples=sum(any(str(r.get(e+'_validity')) in ('1','True') and all(_finite(r.get(e+'_gaze_'+a)) for a in ('x','y')) for e in ('left','right')) for r in rows)
    return {"valid_gaze_percentage":100*valid_samples/len(rows) if rows else None,
      "missing_data":{'invalid_gaze_samples':len(rows)-valid_samples,'empty_trials':[t['trial_id'] for t in trials if not t['sample_count']]},
      "recording_duration_ms":sum(t.get('duration_ms') or 0 for t in session['trials']),
      "timestamp_consistency":all(t['timestamps_monotonic'] for t in trials),
      "calibration_status":'verified' if session.get('validation',{}).get('passed') else 'not_verified',
      "gaze_sample_count":len(rows),"missing_tasks":missing_tasks,"questionnaire_completion":{p:p in session['responses'] for p in ('pre','post')},
      "device_disconnect_events":disconnects,"click_capture_availability":'figma_dom_unavailable_optional_native_mouse' if session.get('task_mode')=='figma_external' else 'native_web_dom',
      "overall_quality_warnings":list(dict.fromkeys(warnings)),"status":'warnings' if warnings else 'no_automatic_warnings',
      "participant_id":session["participant_id"],"session_id":session["session_id"],"mode":session["mode"],
      "simulated":session["mode"]!="hardware","validation_passed":session.get("validation",{}).get("passed",False),
      "sdk_clock_samples":session.get("sdk_clock_samples",[]),
      "timing":"manual researcher start/end; Figma events unavailable", "trials":trials}

def _finite(value):
    try:return math.isfinite(float(value))
    except (TypeError,ValueError):return False
