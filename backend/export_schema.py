"""Add analysis columns at export without rewriting historical raw CSV files."""
import json, math
EXTRA={
'participants':['track_id','group','study_status','calibration_status','start_time','end_time','completion_status','practice_completed'],
'pre_test':['response','timestamp','questionnaire_version'],
'post_test':['response','timestamp','questionnaire_version'],
'gaze':['track_id','test_id','condition','received_timestamp','left_gaze_validity','right_gaze_validity','gaze_x','gaze_y','coordinate_system','screen_width','screen_height','sampling_frequency','left_pupil_diameter','right_pupil_diameter'],
'clicks':['track_id','test_id','condition','x','y','coordinate_system','target_component','target_state','event_source','interaction_category'],
 'trials':['track_id','test_id','condition','start_time','end_time','completion','error_count','recording_status']}

def number(v):
    try:
        n=float(v)
        return n if math.isfinite(n) else None
    except (ValueError,TypeError):return None

def enrich(name,rows,s):
    trials={t['trial_id']:t for t in s['trials']}
    for raw in rows:
        r=dict(raw);t=trials.get(r.get('trial_id'),{});ext=s.get('external',{})
        index=t.get('test_index');rounds=ext.get('rounds',[])
        condition=rounds[index]['family'] if isinstance(index,int) and index<len(rounds) else s.get('condition')
        base={'track_id':ext.get('track_id'),'test_id':index,'condition':condition}
        if name=='participants':
            r.update(condition='baseline_GB_GG_BB' if ext else s.get('condition'),track_id=ext.get('track_id'),group=ext.get('group'),study_status=s['state'],calibration_status='verified' if s.get('validation',{}).get('passed') else 'demo_completed' if s['mode']=='mock' and (s.get('calibration') or {}).get('success') else 'not_verified',start_time=s['created_at'],end_time=s.get('completed_at') or s.get('withdrawn_at'),completion_status='completed' if s['state']=='completed' else 'incomplete',practice_completed=s.get('practice_completed'))
        elif name in ('pre_test','post_test'):r.update(response=r.get('answer'),timestamp=r.get('submitted_at'),questionnaire_version=r.get('version'))
        elif name=='gaze':
            r.update(base);r['received_timestamp']=r.get('backend_received_us')
            for eye in ('left','right'):r[eye+'_gaze_validity']=r.get(eye+'_validity')
            points=[]
            for eye in ('left','right'):
                xy=[number(r.get(eye+'_gaze_'+a)) for a in ('x','y')]
                if str(r.get(eye+'_validity')) in ('1','True') and all(v is not None for v in xy):points.append(xy)
            r.update(gaze_x=sum(p[0] for p in points)/len(points) if points else None,gaze_y=sum(p[1] for p in points)/len(points) if points else None,coordinate_system='normalized_display')
            metadata=s.get('metadata',[]);mi=t.get('metadata_index')
            view=metadata[mi].get('viewport',{}) if isinstance(mi,int) and 0<=mi<len(metadata) else {}
            r.update(screen_width=view.get('screen_width'),screen_height=view.get('screen_height'),sampling_frequency=(t.get('device') or {}).get('configured_hz',60 if s['mode']=='mock' else None))
            sdk=json.loads(r.get('raw_json') or '{}')
            for eye in ('left','right'):
                r[eye+'_pupil_diameter']=number(sdk.get(eye+'_pupil_diameter')) if sdk.get(eye+'_pupil_validity')==1 else None
        elif name=='clicks':
            r.update(base);r.update(x=r.get('client_x'),y=r.get('client_y'),coordinate_system='viewport_css_pixels',target_component=None,target_state=None,event_source='native_web_dom',interaction_category='prototype_interaction')
        elif name=='trials':
            r.update(base);r.update(start_time=t.get('started_at'),end_time=t.get('ended_at'),completion=t.get('status')=='completed',error_count=t.get('decision_error'),recording_status=t.get('status'))
        yield r

DESCRIPTIONS={'participant_id': 'Pseudonymous participant identifier P001-P030; legacy identifiers are preserved', 'session_id': 'Immutable session identifier; join all files using participant_id and session_id', 'mode': 'mock means synthetic test data; hardware means SDK collection', 'condition': 'Experimental condition for this trial; participant summary uses baseline_GB_GG_BB for external tracks', 'created_at': 'Session creation UTC ISO-8601 timestamp', 'version': 'Original questionnaire version alias', 'question_id': 'Question identifier in session snapshot', 'answer': 'Original JSON-encoded submitted response', 'submitted_at': 'Original questionnaire submission UTC ISO-8601 timestamp', 'response': 'JSON-encoded response; alias of answer', 'timestamp': 'Questionnaire submission UTC ISO-8601 or original browser performance.now event milliseconds, depending on file', 'questionnaire_version': 'Version of the immutable questionnaire snapshot', 'trial_id': 'Immutable attempt identifier; retries retain separate identifiers', 'task_id': 'Task identifier; external-0 through external-3 for external workflow', 'device_timestamp': 'Original Tobii device clock microseconds; mock uses synthetic monotonic timestamps', 'system_timestamp': 'Original Tobii SDK system clock microseconds; mock uses backend monotonic clock', 'backend_received_us': 'Backend perf_counter receipt time in microseconds; scoped to trial clock_segment_id', 'received_timestamp': 'Alias of backend_received_us, not UTC wall clock', 'left_gaze_x': 'Original left-eye normalized display x; check validity before use', 'left_gaze_y': 'Original left-eye normalized display y; check validity before use', 'right_gaze_x': 'Original right-eye normalized display x; check validity before use', 'right_gaze_y': 'Original right-eye normalized display y; check validity before use', 'left_validity': 'Original left-eye SDK validity value; 1 valid, 0 invalid', 'right_validity': 'Original right-eye SDK validity value; 1 valid, 0 invalid', 'left_gaze_validity': 'Alias of left_validity', 'right_gaze_validity': 'Alias of right_validity', 'raw_json': 'Original SDK sample serialized as JSON; nonfinite raw values preserved as strings', 'gaze_x': 'Mean x of finite valid eyes; one eye uses that eye; no valid eye is blank', 'gaze_y': 'Mean y of finite valid eyes; one eye uses that eye; no valid eye is blank', 'coordinate_system': 'normalized_display for gaze or viewport_css_pixels for browser events', 'screen_width': 'Browser screen.width CSS pixels from the trial metadata snapshot; blank if unavailable', 'screen_height': 'Browser screen.height CSS pixels from the trial metadata snapshot; blank if unavailable', 'sampling_frequency': 'Configured device sampling frequency in Hz; mock requests 60 Hz; actual rate is in quality report', 'left_pupil_diameter': 'Left pupil diameter mm only when SDK pupil validity is 1; otherwise blank', 'right_pupil_diameter': 'Right pupil diameter mm only when SDK pupil validity is 1; otherwise blank', 'event_id': 'Browser event deduplication identifier', 'event_type': 'Actual browser event type; external Figma DOM events are unavailable', 'client_x': 'Original browser clientX CSS pixels', 'client_y': 'Original browser clientY CSS pixels', 'screen_x': 'Original browser screenX CSS pixels; not native mouse physical pixels', 'screen_y': 'Original browser screenY CSS pixels; not native mouse physical pixels', 'scroll_x': 'Browser horizontal document scroll offset in CSS pixels', 'scroll_y': 'Browser vertical document scroll offset in CSS pixels', 'page_url': 'Browser page URL reported by instrumented native web stimulus', 'target_element_id': 'Actual DOM target identifier; no inferred Figma target labels', 'viewport_json': 'Original browser viewport, scroll, DPI and layout metadata as JSON', 'x': 'Alias of client_x for browser events', 'y': 'Alias of client_y for browser events', 'target_component': 'Blank unless a component is established by instrumentation; no inference', 'target_state': 'Blank unless a component state is established by instrumentation; no inference', 'event_source': 'native_web_dom for browser-instrumented events; Windows events are in mouse.csv', 'interaction_category': 'prototype_interaction for instrumented stimulus events; experiment controls are excluded', 'started_us': 'Backend perf_counter start microseconds in the trial clock segment', 'ended_us': 'Backend perf_counter end microseconds; blank after interrupted unknown end', 'duration_ms': 'Measured trial duration milliseconds; blank when end is unknown', 'status': 'Persisted trial status: completed, incomplete, recording, failed, or awaiting_answers', 'reason': 'Recorded reason for interruption or failure; blank when none recorded', 'click_count': 'Count of persisted click events in instrumented native web stimulus; not Figma DOM clicks', 'gaze_count': 'Count of persisted gaze samples reconciled from raw CSV on export', 'native_mouse_count': 'Count of Windows mouse events recorded in mouse.csv, if enabled', 'native_click_count': 'Count of Windows mouse button press events, not DOM-verified clicks', 'track_id': 'Assigned immutable T01-T30 track identifier', 'test_id': 'External test index: 0 baseline, 1 GB, 2 GG, 3 BB', 'group': 'Track group A, B, or C', 'study_status': 'Current persisted session state', 'calibration_status': 'verified only for passed independent hardware validation; demo_completed never certifies hardware', 'start_time': 'UTC ISO-8601 session creation or externally recorded trial start timestamp', 'end_time': 'UTC ISO-8601 session completion/withdrawal or externally recorded trial end; blank if unknown', 'completion_status': 'completed or incomplete based on persisted session state', 'practice_completed': 'Whether the new workflow completed all four separate practice activities; blank for legacy sessions', 'completion': 'Whether this trial has completed status', 'error_count': 'Recorded Decision Error (0 or 1) from the round answers; blank if unavailable; not general UI error count', 'recording_status': 'Persisted trial recording/completion status'}

UNITS={'device_timestamp':'SDK microseconds','system_timestamp':'SDK system microseconds','backend_received_us':'backend perf_counter microseconds','received_timestamp':'backend perf_counter microseconds','timestamp':'questionnaire ISO-8601 UTC; click browser performance.now milliseconds','started_us':'backend perf_counter microseconds','ended_us':'backend perf_counter microseconds','duration_ms':'milliseconds','sampling_frequency':'Hz','gaze_x':'normalized display fraction','gaze_y':'normalized display fraction','left_gaze_x':'normalized display fraction','left_gaze_y':'normalized display fraction','right_gaze_x':'normalized display fraction','right_gaze_y':'normalized display fraction','screen_width':'CSS pixels from browser screen.width','screen_height':'CSS pixels from browser screen.height','x':'CSS pixels','y':'CSS pixels','left_pupil_diameter':'millimeters','right_pupil_diameter':'millimeters'}
def readme(s,fields):
    text=['EyeTrack Lab dataset schema 3','Participant: '+s['participant_id'],'Session: '+s['session_id'],'Mode: '+s['mode'],'Collection start UTC: '+s['created_at'],
    'Files join on participant_id and session_id. Trial samples also join on trial_id/task_id.',
    'UTF-8 BOM CSV, comma delimiter, quoted JSON responses. Blank = missing/unavailable, never fabricated zero.',
    'Software: EyeTrack Lab 0.1.0; experiment snapshot and device/SDK version are in session.json.',
    'Original CSV columns retained. Added columns are computed from immutable session/trial metadata.',
    'gaze_x/y: arithmetic mean of valid finite eyes; one eye uses that eye; neither eye leaves blank.',
    'No degrees-of-visual-angle accuracy claim. Normalized gaze is NOT viewport pixels.',
    'Browser performance.now, backend perf_counter and SDK timestamps have separate origins. See metadata synchronization, sdk_clock_samples, and trial clock_segment_id. Do not compare across restart segments.',
    'Practice actions are only in session.json practice_attempts and excluded from gaze/clicks/trials.',
    'Figma external: manual start/end. No verified Figma Embed API events; DOM targets unavailable. Optional mouse.csv contains Windows screen events, not Figma DOM component labels.',
    'Native web demo is not a validated reconstruction of all Figma variants. Mock samples are simulated.',
    'Interrupted tasks retain incomplete status and unknown end time. Exports do not alter raw data.',
    'Track configuration, group, duplicate_of and assignment seed/method are in session.json.',
    'JSON: session.json = full session state, protocol/questionnaire snapshots, device, calibration, validation, viewport, clock mappings, trials, audit; quality_report.json = measured quality and warnings.',
    'CSV data dictionary (field: unit/type; names retain original meaning):']
    for name,columns in fields.items():
        text.append(name+'.csv')
        for col in columns:text.append('  '+col+': '+DESCRIPTIONS[col]+'; unit: '+UNITS.get(col,'text/category/boolean/JSON as described'))
    return chr(10).join(text)
