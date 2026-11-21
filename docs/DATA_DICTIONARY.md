# Export data dictionary
Schema version 3. Historical raw CSV files are unchanged; extra columns are added at export.
Required CSV/JSON/text files are under mode/participant_id/session_id/. Optional rounds/video/validation/mouse files retain existing evidence.

## participants.csv

| Column | Meaning |
|---|---|
| `participant_id` | Pseudonymous participant identifier P001-P030; legacy identifiers are preserved |
| `session_id` | Immutable session identifier; join all files using participant_id and session_id |
| `mode` | mock means synthetic test data; hardware means SDK collection |
| `condition` | Experimental condition for this trial; participant summary uses baseline_GB_GG_BB for external tracks |
| `created_at` | Session creation UTC ISO-8601 timestamp |
| `track_id` | Assigned immutable T01-T30 track identifier |
| `group` | Track group A, B, or C |
| `study_status` | Current persisted session state |
| `calibration_status` | verified only for passed independent hardware validation; demo_completed never certifies hardware |
| `start_time` | UTC ISO-8601 session creation or externally recorded trial start timestamp |
| `end_time` | UTC ISO-8601 session completion/withdrawal or externally recorded trial end; blank if unknown |
| `completion_status` | completed or incomplete based on persisted session state |
| `practice_completed` | Whether the new workflow completed all four separate practice activities; blank for legacy sessions |

## pre_test.csv

| Column | Meaning |
|---|---|
| `participant_id` | Pseudonymous participant identifier P001-P030; legacy identifiers are preserved |
| `session_id` | Immutable session identifier; join all files using participant_id and session_id |
| `version` | Original questionnaire version alias |
| `question_id` | Question identifier in session snapshot |
| `answer` | Original JSON-encoded submitted response |
| `submitted_at` | Original questionnaire submission UTC ISO-8601 timestamp |
| `response` | JSON-encoded response; alias of answer |
| `timestamp` | Questionnaire submission UTC ISO-8601 or original browser performance.now event milliseconds, depending on file |
| `questionnaire_version` | Version of the immutable questionnaire snapshot |

## post_test.csv

| Column | Meaning |
|---|---|
| `participant_id` | Pseudonymous participant identifier P001-P030; legacy identifiers are preserved |
| `session_id` | Immutable session identifier; join all files using participant_id and session_id |
| `version` | Original questionnaire version alias |
| `question_id` | Question identifier in session snapshot |
| `answer` | Original JSON-encoded submitted response |
| `submitted_at` | Original questionnaire submission UTC ISO-8601 timestamp |
| `response` | JSON-encoded response; alias of answer |
| `timestamp` | Questionnaire submission UTC ISO-8601 or original browser performance.now event milliseconds, depending on file |
| `questionnaire_version` | Version of the immutable questionnaire snapshot |

## gaze.csv

| Column | Meaning |
|---|---|
| `participant_id` | Pseudonymous participant identifier P001-P030; legacy identifiers are preserved |
| `session_id` | Immutable session identifier; join all files using participant_id and session_id |
| `trial_id` | Immutable attempt identifier; retries retain separate identifiers |
| `task_id` | Task identifier; external-0 through external-3 for external workflow |
| `mode` | mock means synthetic test data; hardware means SDK collection |
| `device_timestamp` | Original Tobii device clock microseconds; mock uses synthetic monotonic timestamps |
| `system_timestamp` | Original Tobii SDK system clock microseconds; mock uses backend monotonic clock |
| `backend_received_us` | Backend perf_counter receipt time in microseconds; scoped to trial clock_segment_id |
| `left_gaze_x` | Original left-eye normalized display x; check validity before use |
| `left_gaze_y` | Original left-eye normalized display y; check validity before use |
| `left_validity` | Original left-eye SDK validity value; 1 valid, 0 invalid |
| `right_gaze_x` | Original right-eye normalized display x; check validity before use |
| `right_gaze_y` | Original right-eye normalized display y; check validity before use |
| `right_validity` | Original right-eye SDK validity value; 1 valid, 0 invalid |
| `raw_json` | Original SDK sample serialized as JSON; nonfinite raw values preserved as strings |
| `track_id` | Assigned immutable T01-T30 track identifier |
| `test_id` | External test index: 0 baseline, 1 GB, 2 GG, 3 BB |
| `condition` | Experimental condition for this trial; participant summary uses baseline_GB_GG_BB for external tracks |
| `received_timestamp` | Alias of backend_received_us, not UTC wall clock |
| `left_gaze_validity` | Alias of left_validity |
| `right_gaze_validity` | Alias of right_validity |
| `gaze_x` | Mean x of finite valid eyes; one eye uses that eye; no valid eye is blank |
| `gaze_y` | Mean y of finite valid eyes; one eye uses that eye; no valid eye is blank |
| `coordinate_system` | normalized_display for gaze or viewport_css_pixels for browser events |
| `screen_width` | Browser screen.width CSS pixels from the trial metadata snapshot; blank if unavailable |
| `screen_height` | Browser screen.height CSS pixels from the trial metadata snapshot; blank if unavailable |
| `sampling_frequency` | Configured device sampling frequency in Hz; mock requests 60 Hz; actual rate is in quality report |
| `left_pupil_diameter` | Left pupil diameter mm only when SDK pupil validity is 1; otherwise blank |
| `right_pupil_diameter` | Right pupil diameter mm only when SDK pupil validity is 1; otherwise blank |

## clicks.csv

| Column | Meaning |
|---|---|
| `participant_id` | Pseudonymous participant identifier P001-P030; legacy identifiers are preserved |
| `session_id` | Immutable session identifier; join all files using participant_id and session_id |
| `trial_id` | Immutable attempt identifier; retries retain separate identifiers |
| `task_id` | Task identifier; external-0 through external-3 for external workflow |
| `event_id` | Browser event deduplication identifier |
| `event_type` | Actual browser event type; external Figma DOM events are unavailable |
| `timestamp` | Questionnaire submission UTC ISO-8601 or original browser performance.now event milliseconds, depending on file |
| `backend_received_us` | Backend perf_counter receipt time in microseconds; scoped to trial clock_segment_id |
| `client_x` | Original browser clientX CSS pixels |
| `client_y` | Original browser clientY CSS pixels |
| `screen_x` | Original browser screenX CSS pixels; not native mouse physical pixels |
| `screen_y` | Original browser screenY CSS pixels; not native mouse physical pixels |
| `scroll_x` | Browser horizontal document scroll offset in CSS pixels |
| `scroll_y` | Browser vertical document scroll offset in CSS pixels |
| `page_url` | Browser page URL reported by instrumented native web stimulus |
| `target_element_id` | Actual DOM target identifier; no inferred Figma target labels |
| `viewport_json` | Original browser viewport, scroll, DPI and layout metadata as JSON |
| `track_id` | Assigned immutable T01-T30 track identifier |
| `test_id` | External test index: 0 baseline, 1 GB, 2 GG, 3 BB |
| `condition` | Experimental condition for this trial; participant summary uses baseline_GB_GG_BB for external tracks |
| `x` | Alias of client_x for browser events |
| `y` | Alias of client_y for browser events |
| `coordinate_system` | normalized_display for gaze or viewport_css_pixels for browser events |
| `target_component` | Blank unless a component is established by instrumentation; no inference |
| `target_state` | Blank unless a component state is established by instrumentation; no inference |
| `event_source` | native_web_dom for browser-instrumented events; Windows events are in mouse.csv |
| `interaction_category` | prototype_interaction for instrumented stimulus events; experiment controls are excluded |

## trials.csv

| Column | Meaning |
|---|---|
| `participant_id` | Pseudonymous participant identifier P001-P030; legacy identifiers are preserved |
| `session_id` | Immutable session identifier; join all files using participant_id and session_id |
| `trial_id` | Immutable attempt identifier; retries retain separate identifiers |
| `task_id` | Task identifier; external-0 through external-3 for external workflow |
| `started_us` | Backend perf_counter start microseconds in the trial clock segment |
| `ended_us` | Backend perf_counter end microseconds; blank after interrupted unknown end |
| `duration_ms` | Measured trial duration milliseconds; blank when end is unknown |
| `status` | Persisted trial status: completed, incomplete, recording, failed, or awaiting_answers |
| `reason` | Recorded reason for interruption or failure; blank when none recorded |
| `click_count` | Count of persisted click events in instrumented native web stimulus; not Figma DOM clicks |
| `gaze_count` | Count of persisted gaze samples reconciled from raw CSV on export |
| `native_mouse_count` | Count of Windows mouse events recorded in mouse.csv, if enabled |
| `native_click_count` | Count of Windows mouse button press events, not DOM-verified clicks |
| `track_id` | Assigned immutable T01-T30 track identifier |
| `test_id` | External test index: 0 baseline, 1 GB, 2 GG, 3 BB |
| `condition` | Experimental condition for this trial; participant summary uses baseline_GB_GG_BB for external tracks |
| `start_time` | UTC ISO-8601 session creation or externally recorded trial start timestamp |
| `end_time` | UTC ISO-8601 session completion/withdrawal or externally recorded trial end; blank if unknown |
| `completion` | Whether this trial has completed status |
| `error_count` | Recorded Decision Error (0 or 1) from the round answers; blank if unavailable; not general UI error count |
| `recording_status` | Persisted trial recording/completion status |

## JSON and text files

`session.json` contains immutable snapshots, assignment/seed, device, calibration/validation, viewport, clock mappings, responses, trials, practice and audit.
`quality_report.json` contains actual sample counts, valid percentage, missing/expected samples, duration, timestamp monotonicity, stream interruptions, missing tasks, questionnaire completion and warnings.
`README.txt` embeds file definitions and the CSV dictionary.
Machine-readable schema: `config/export-schema.json`. Blank CSV values mean unavailable/missing; do not replace them with zero.