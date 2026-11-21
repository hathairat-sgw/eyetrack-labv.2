# Master prompt implementation report — 2026-11-21

## Scope and preservation

Actual workspace found from the open VS Code window: `C:/Users/Hathairat Srighiwong/Desktop/Aea/KMUTT/Project/eyetrack-lab`.
Existing React/Vite, FastAPI, SDK adapter and CSV/JSON architecture retained. OceanX was not edited. No research data was deleted, overwritten, migrated, or used as a test fixture. Source/config backup: `work/backups/master-audit-25691121-122734`.

## Features implemented in this pass

- Exact `Run All - EyeTrack Lab` task, PowerShell run wrapper, Python import preflight, deterministic npm ci setup, localhost readiness and owned-service shutdown tests.
- P001-P030 capacity, stable default participant/track identity, reproducible mode-isolated seed assignment without replacement, immutable assignment after allocation, resume existing sessions, withdrawal reservation protection.
- Independent validation retained; new external sessions require four real practice UI actions before Pre-test. Practice evidence persists separately in session metadata and never enters research samples/trials. Researcher can repeat before trial 1.
- Server and participant UI support conditional questionnaire equality rules, reject forward references, strip hidden answers. Original questionnaire texts and legacy session snapshots retained.
- Approved table validation: 30 tracks, 10/group, exact GB/GG/BB table, no repeated component-state, shared baseline, intentional duplicates and 27 unique configurations. Invalid registry blocks hardware creation and start.
- Researcher Pause/Resume/Abort with audit; pause flushes and preserves incomplete trial, resume requires calibration and creates a separate attempt. No invented continuous timing across interruptions.
- Export All excludes demo by default; explicit demo checkbox, content-addressed export history without duplicate history records, dataset validation, required nine files per session plus existing optional evidence.
- Additive export columns preserve historical raw CSV schemas. Valid-eye mean gaze and single-eye fallback; missing combined gaze stays blank. No conversion between normalized display and CSS/native physical pixels is invented.
- Measured quality report: actual counts, valid fraction/percentage, expected samples when frequency/duration are known, missing estimates, monotonicity, interruptions, missing tasks/questionnaires, click availability and warnings.
- Participant responses no longer expose device serial/address through nested calibration, validation or trial objects.
- Explicit CSV dictionary and machine-readable export schema. README embedded in exports now describes joins, units, missing values, clocks, assignment, versions and limitations.

## Tests actually executed

- `.venv-hardware/Scripts/python.exe -m pytest -q -p no:cacheprovider -o faulthandler_timeout=30`: **68 passed**, one pre-existing Starlette/httpx deprecation warning. Includes synthetic 30-participant × four-round completion and nine-file export readability/identifier checks, practice, resume, conditional answers, assignments, validity, privacy, pause and export history.
- `node --test tests/test_participant_link.mjs tests/test_launcher.mjs`: **5 passed**. Actual isolated backend/frontend startup reaches READY; both service ports are free after shutdown; existing occupied port owner is preserved.
- `npm.cmd run build`: **passed**.
- `node scripts/ui-smoke.mjs`: **passed**, isolated Chrome, new participant information/consent → mock calibration → practice → Pre-test → four researcher-controlled rounds → Post-test → completion → reload. Synthetic canvas WebM saved and decoded at 640×360; final run 108 mock gaze samples and 48,569 video bytes. This is test data, not hardware evidence.
- `.venv-hardware/Scripts/python.exe -m pip check`: **passed**, no broken requirements.
- Actual read-only device discovery: **connected=false, simulated=false**, no Tobii found. No gaze was recorded by this check.
- The initial sandboxed pytest runs stalled on test networking; those owned test processes were stopped. All reported passing results are normal-permission runs against temporary directories.

## Definition of Done status

| Requirement | Status / evidence |
|---|---|
| One-click launcher, services and health/shutdown | PASS automated; exact task configured. Actual F5 click/browser auto-open UI remains NOT VERIFIED this pass. |
| Device status truthful | PASS discovery reports disconnected; no hardware was found. |
| SDK calibration/independent validation | IMPLEMENTED / NOT VERIFIED on physical Tobii Pro Spark. |
| Practice and questionnaires | PASS automated + complete browser flow. |
| 30-track table and allocation | PASS validation + all-30 synthetic integration. |
| Figma mapping config/URL restrictions | IMPLEMENTED; original 19 mappings retained, not promoted to verified. |
| Correct visual frame and interactions for every variant | NOT VERIFIED. |
| Real gaze and disconnect recovery | SDK implementation and fake-adapter contracts PASS; physical acceptance NOT VERIFIED. |
| Mouse collection | Instrumented native demo and native Windows adapter exist; actual Figma DOM component/state coverage NOT VERIFIED/UNAVAILABLE. |
| Dashboard, progress, export and nine required files | PASS software checks. |
| Atomic recovery/data preservation | Existing contracts plus practice/assignment/restart tests PASS. Full power-loss and long-duration physical sessions NOT VERIFIED. |
| README, schema and dictionary | DONE. |

## Remaining issues and blockers

1. **BLOCKED — physical research acceptance:** connect Tobii Pro Spark on the computer running this backend. Verify frequency, display mapping, calibration, independent validation, real gaze/pupil, disconnect/reconnect and clock offsets before enrolling participants. No simulated fallback is used for hardware sessions.
2. **NOT VERIFIED — Figma:** read the open prototype's actual flow inventory (Baseline, six Good, three Bad, nine Mixed). The web fetch could not open the supplied URL; native reading worked, but interaction input failed with `coordinate input geometry is unavailable`. No starting-node/interaction was falsely marked verified. The currently open reference starts at `1108-173438`, while existing mappings use older nodes; researcher must verify each intended starting frame before new sessions. Embed API event coverage remains untested; external mode intentionally uses manual start/end.
3. **BLOCKED — complete native replacement:** only existing demo/Status-Search stimulus implementations are present. A faithful 19-variant native reproduction has not been completed or visually accepted. Full Figma DOM clicks/component/state labels cannot be claimed. Optional mouse.csv is Windows screen telemetry, not DOM labels.
4. **BLOCKED — research protocol content:** default protocol remains an explicitly labelled Demo draft with approved=false. Questionnaire originals were previously integrated from IRB source files with provenance; do not invent consent or mark protocol approved. Review/activate the actual information, consent and retention policy in the existing editor.
5. No real participant sessions were created for verification. Existing running app was left running; backend changes require a safe restart. Legacy sessions keep their original sequence; create a new session for the new practice workflow.
6. Fixed Baseline→GB→GG→BB order is preserved. A validated counterbalancing editor and full laboratory-duration acceptance remain future work; no automatic order change was introduced.
7. Export dictionaries describe known metadata only. Missing component labels, unavailable screen dimensions and unknown end times remain blank. Aggregate data-quality warnings are screening aids, not research acceptance certification.

## Exact Windows run steps

1. Open `eyetrack-lab.code-workspace` from this EyeTrack Lab folder.
2. For a new machine, install Node.js 22 and Python 3.10 x64 with Python Launcher, then run `Setup-Windows.cmd` once. This machine already has working dependencies.
3. If the old application is running, finish/stop recording and video first; stop that run in VS Code. Do not stop during a participant trial.
4. Run **Terminal → Run Task → Run All - EyeTrack Lab**, or **F5 → EyeTrack Lab: Run all**. Alternative: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run.ps1`.
5. Wait for READY and the browser. Sign in with the researcher password printed by the backend. Use DEMO for software rehearsal. Configure assignment before creating the first session of the selected mode.
6. Hardware sessions additionally require actual device detection, approved research protocol, verified prototype links, successful calibration and independent validation. Complete Practice, Pre-test, four trials, Post-test and Completion.
7. Validate and export. Export All defaults to hardware only; demo inclusion requires an explicit checkbox. Keep raw data and a separate secure backup.
8. Stop active recording/video in the UI before Ctrl+C / Stop in VS Code.

## Files created

- `backend/assignment.py`
- `backend/export_history.py`
- `backend/export_schema.py`
- `backend/practice.py`
- `backend/tracks.py`
- `config/export-schema.json`
- `docs/DATA_DICTIONARY.md`
- `docs/MASTER_PROMPT_REPORT.md`
- `frontend/src/Practice.jsx`
- `scripts/run.ps1`
- `tests/test_master_requirements.py`

## Files modified

- `docs/DEVELOPMENT_CHECKLIST.md`
- `.vscode/tasks.json`
- `README.md`
- `backend/engine.py`
- `backend/exporting.py`
- `backend/external.py`
- `backend/main.py`
- `backend/models.py`
- `backend/quality.py`
- `backend/validation.py`
- `frontend/src/ExternalControl.jsx`
- `frontend/src/Participant.jsx`
- `frontend/src/QuestionnaireForm.jsx`
- `frontend/src/Researcher.jsx`
- `scripts/run.mjs`
- `scripts/setup.ps1`
- `scripts/ui-smoke.mjs`
- `tests/test_external.py`
- `tests/test_hardware_workflow.py`
- `tests/test_launcher.mjs`
