# System QA report

Data isolation: temporary data root, ports 8001/5174. Existing research data and OceanX not edited.

## Fixed findings
1. High: external end_trial previously committed an advanced task index before committing awaiting_answers. A crash between commits could bypass required round answers. It now persists external_answers and unchanged task_index in the first commit. Regression checks every save.
2. Medium: prototype validation happened after creating a bootstrap session, leaving orphan sessions if links were missing. Validate all links and bootstrap config before allocating.
3. Medium: Start after four rounds indexed past the rounds array, causing an internal error. Explicit state/index guard now returns conflict.
4. Medium: changing a prototype URL/node retained the old node ID in the session snapshot. Snapshot now takes node ID from the same prototype as the URL; regression added.
5. Usability: Start button was enabled before the readiness checks/link verification, then rejected by API. Button now stays disabled until all four checks and verified link are present. Server guard remains.

## Actual validation
- Automated suite: 43 passed; 1 existing Starlette TestClient deprecation warning.
- Production build: passed.
- Browser: researcher login, Test 0 through Test 3 manual start/end/answers, Post-test 24 ratings + one optional text answer, Finish, refresh completed, ZIP download.
- Prepared fixture supplied mock consent/calibration/pre-test and verified-link states; these were test setup, not real hardware or all-link verification.
- Baseline Figma opened in a separate tab while Mock recording continued; after returning, manual stop and scoring succeeded. This is a short background-tab test, not long-duration browser-throttling certification.
- Downloaded ZIP: four rounds, 623 mock gaze rows, 5 pre rows, 25 post rows (24 ratings + one answered optional question), all participant/session IDs consistent; decisions [0,0,0,0]. Optional blank text questions have no response row.

## Remaining limitations
- Session reserves prototype URL/status snapshot; editing Manager later does not update an existing reservation. Verify links before creating a new session.
- Cannot record Figma DOM clicks/scroll/navigation or exact Submit time. Native mouse capture still not implemented.
- Hardware lock remains; Tobii, display mapping, calibration accuracy and timing require physical testing.
- F5 actual VS Code UI and extended background/sleep/disconnect scenarios not verified in this browser run; restart/controller-loss cases covered by automated tests.
- Fullscreen readiness check is researcher attestation; localhost cannot inspect the external Figma window.
- Researcher token timeout requires logging out/in; UI does not yet automatically redirect on expiry.
- Practice opens links only; it does not simulate a full recorded practice session.


## 17 November 2026 — Hardware External update
59 Python tests, 4 Node tests and production build passed. pip check passed. Chrome smoke passed with MOCK gaze and synthetic canvas WebM (125 samples, 56962 bytes, decoded 640x360). Physical Tobii is on another computer: actual detection/calibration/validation/gaze, native mouse DPI, screen picker and cable-disconnect acceptance remain pending. See HARDWARE.md.
