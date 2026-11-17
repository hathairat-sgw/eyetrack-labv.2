# ผลตรวจระบบ — 9 พฤศจิกายน 2026

## ตรวจผ่านแล้ว

- npm build: ผ่าน (React 19 / Vite 6.4.5; Node 22.19.0)
- backend pytest: 19 tests ผ่านบน Python 3.14.2
- ชุดทดสอบ 19 กรณีผ่านบน Python 3.10.10 + Tobii SDK 2.1.0
- HTTP frontend 5173 และ backend health 8000 ตอบ 200
- Browser UI: สร้าง P001/session → ยินยอม Demo → pre-test → calibration จำลอง 5 จุด → 2 งาน → post-test → completed → export
- Browser session: Sc12f651ac2c34669
- ZIP ที่ดาวน์โหลดจาก API จริง: participants 1 แถว, pre_test 2, post_test 2, gaze 581, clicks 8, trials 2
- ตรวจ participant/session IDs ทุก CSV และเก็บข้อความไทย/JSON answers ได้
- เปิดผลลัพธ์เดิมได้หลัง restart backend
- SDK import/discovery จริงสำเร็จ แต่ผล discovery ไม่พบอุปกรณ์

## Tests ที่ครอบคลุม

Consent gate, required/typed answers, one active recording, duplicate start,
duplicate event IDs, wrong client, duplicate participant window, disconnect,
resume with a new trial, withdrawal, heartbeat timeout, task time limit,
seed reproducibility, immutable configuration snapshots, CSV corruption,
disk full fail-closed, calibration failure/exception, unknown stimulus route,
trial/task IDs ใน export, startup file lock, clock-segment metadata,
HTTP validation, CORS origin rejection และ WebSocket lifecycle

## ยังไม่ตรวจรับ

- เว็บไซต์ stimulus ตาม Figma: ยังมีเฉพาะ inventory; Present ขอ sign-in
- Good / Bad / Mixed ใช้เพียง metadata ขณะนี้ ไม่ใช่หน้าจอเปรียบเทียบจริง
- ฮาร์ดแวร์ Tobii: ไม่มีอุปกรณ์ที่ SDK ตรวจพบ จึงยังไม่วัด gaze/calibration/disconnect จริง
- coordinate mapping, timing drift และ calibration quality บนจอจริง
- questionnaire/protocol ฉบับใช้วิจัยจริงและนโยบาย retention ของโครงการ
- การทดสอบ stress ระยะยาวและการกู้คืนไฟล์จาก power loss ทางกายภาพ

## ข้อจำกัดที่ทราบ

- คำเตือนจาก Starlette TestClient แนะนำเปลี่ยนจาก httpx ไป httpx2; tests ยังผ่าน ไม่มีผลกับ runtime Uvicorn
- ข้อมูล Demo ที่สร้างระหว่าง browser QA เก็บแยกใน data/mock และไม่ถูกลบอัตโนมัติ
- ตัวนับ sample ของ Mock อาจต่างจาก 60 Hz ตามการ scheduling ของ Windows; ใช้ timestamps จริงที่สร้าง ไม่เติม sample ให้ครบตามจำนวนคาดหมาย
- หน้าต่างผู้เข้าร่วมถูกซ่อน/เปลี่ยนขนาดจะหยุด trial แทนการบันทึกต่อในสภาพที่ stimulus เปลี่ยนไป


## 2026-11-10 — Figma flow preview
- npm run build: ผ่าน (Vite 6.4.5)
- Browser smoke test: console → Status(LS)+Search(HS) → Start The Task → MDT313 → Syllabus → Assessment Activity → Quiz (คงตาราง) → Submit → detail → Submit → console ผ่าน
- ตรวจ DOM ตาราง: 7 แถว, Late Submitted 2 รายการ
- Browser console error: ไม่พบในรอบทดสอบนี้
- หน้า Preview ไม่มี API recording และยังไม่ได้เปิดใช้เป็น task ใน session
- ยังไม่ผ่าน visual comparison: ภาพ ฟอนต์ Syllabus ส่วนล่าง Submission panel และ Rubric ยังไม่ครบ
- การทดสอบนี้ไม่ใช่การรับรองชุดอื่นหรือ Tobii hardware และไม่ได้รันทดสอบ backend ซ้ำเพราะรอบนี้ไม่เปลี่ยน backend

## 2026-11-12 — Phase 1 audit / One-Click Run
- Regression: 19 passed (Python .venv); 1 warning Starlette TestClient deprecation
- Frontend production build: ผ่าน
- Launcher default Python 3.10 environment: /api/health ผ่าน proxy, frontend พร้อม, Uvicorn graceful shutdown ผ่าน
- Launcher --mock environment: startup และ shutdown ผ่าน
- Both smoke runs use fresh temp data, not project/data
- Occupied port integration test: 1 passed; exit 1 without stopping port owner
- Tobii discovery: Python 3.10.10; connected=false, simulated=false, recording_started=false
- ไม่ได้ยืนยัน calibration/gaze จริง ไม่ได้เปลี่ยน hardware collection lock
- VS Code launch config เพิ่มแล้ว; ยังไม่ได้ตรวจ F5 และ browser auto-open ผ่าน UI จริง
- Backend state machine, raw CSV/export schema และข้อมูลเดิมไม่ได้แก้

## 2026-11-12 — Word questionnaires and role access
- Final automated suite: 23 passed; 1 existing Starlette TestClient deprecation warning
- Production frontend build: passed
- Tests include source structure (4×6 + 3), duplicates preserved, draft/restart/revision conflict, required fields/age validation, duplicate submission, CSV/JSON and timestamp/IDs, full Mock with IRB forms, unauthenticated and cross-session role denial, authorized WebSocket
- Browser (isolated ports 5174/8001, temp data): researcher login, create session, participant scoped link, pre form fill/save/reload/submit/confirmation passed
- Post browser preview: 4 sections with 6 ratings each + open questions, Previous/Next retains values; completed preview (not persisted research answers)
- Post persisted answers/export verified by automated tests, not by a completed browser experiment
- Fullscreen calibration denied by test browser (not granted); no real hardware validation claimed
- Current production ports 5173/8000 were already occupied and were not stopped or restarted
- Waiting for revised Word source path/file; current template is for review only, no existing session/configuration migrated


## 2026-11-15 — ตรวจและเชื่อม LEB Mock ในโปรเจกต์เดิม
- ใช้โค้ดและ launcher เดิม ไม่สร้างโปรเจกต์ซ้ำ ไม่แก้ OceanX
- Task Manager เพิ่ม Status(LS)+Search(HS) ลงแบบร่างได้ กด Save tasks แล้วเลือกเฉพาะงานนี้ใน session ใหม่ด้วย Mixed + Mock
- Route /stimuli/leb-status-search ผูกกับ participant runner; /stimuli/leb-preview ยังเป็น preview อิสระ
- บันทึก navigation/click/scroll/viewport และ gaze จำลอง; Quiz คงตาราง; Submit ในรายละเอียดกลับ console และจบ trial ก่อนกดไป post-test
- บังคับ Mixed, target leb-submit และ target_click; ปฏิเสธ Good/Bad, random targets และ hardware สำหรับ flow นี้ เพราะยังไม่มีหลักฐานรองรับ variant อื่น
- source_verified ยังคง false; session.stimulus_status = figma_flow_mock_visual_unverified
- ไม่มีปุ่มถอนตัวลอยทับระหว่าง recording; แจ้ง Escape หยุดก่อนเริ่มงาน นักวิจัยหยุดจาก Runner ได้เสมอ
- เพิ่ม calibration แบบหน้าต่างสำหรับ Mock โดยเลือกชัดเจน ไม่เปลี่ยนข้อกำหนด Hardware
- Launcher รองรับ EYETRACK_BACKEND_PORT/EYETRACK_FRONTEND_PORT และ --isolated เพื่อทดสอบโดยไม่ใช้ data เดิม

ผลตรวจรอบนี้:
- Python 3.14: pytest 28 passed, 1 Starlette deprecation warning (ไม่ใช่ test failure)
- Frontend production build ผ่าน
- Launcher smoke ผ่าน Python 3.14 และ Python 3.10, readiness ผ่าน API proxy และ graceful shutdown ผ่าน ใช้ข้อมูลชั่วคราว
- กด F5 ใน VS Code workspace เดิม แล้วพบหน้า EyeTrack Lab เปิดใน Edge; หน้าศูนย์ควบคุมต้องใช้รหัสนักวิจัยที่พิมพ์ใน terminal ของรอบนั้น
- Browser end-to-end บนพอร์ตแยก 5175/8002: login → add task → P001/session → consent → pre → Mock calibration 5 จุด → task → Quiz → Submit → console → post → completed
- Browser session Sd7ab92b8ff864f32, seed 1511, trial completed 15.55 s, 502 mock gaze samples, 21 events, 6 clicks
- การดาวน์โหลดผ่าน browser tool ไม่สำเร็จเพราะ browser session หลุด; ตรวจ export ผ่าน API แยกแทน ไม่อ้างว่าปุ่มดาวน์โหลดผ่านครบ
- คำสั่ง pytest ในสภาพแวดล้อมจำกัดค้างที่ Python socketpair ก่อนเข้าแอป; รันภายนอกข้อจำกัดแล้วผ่าน ไม่มีการแก้โค้ดแอปเพื่อหลบการทดสอบ

ยังไม่ตรวจรับ:
- Tobii SDK discovery: connected=false, simulated=false, recording_started=false; ไม่ได้ตรวจ calibration/gaze/ถอดสาย/พิกัด/timing จริง Hardware collection lock ยังคงอยู่ ไม่เปลี่ยนเป็น Mock โดยเงียบ
- Figma canvas เปิดได้และพบ BASE/Good+Good/Bad+Bad/Mixed; ยังไม่ตรวจทุก frame และ prototype interaction ในรอบนี้
- Baseline และอีก 17 variant ยังไม่ implement; assets/font, Syllabus ส่วนล่าง, Submission panel และ Rubric ยังไม่ครบ ไม่ใช้เก็บข้อมูลเปรียบเทียบจริง
- แบบสอบถาม IRB ฉบับแก้ไขเพิ่มเติมยังไม่มีไฟล์ที่ยืนยัน งานนี้ไม่เปลี่ยนแบบสอบถามหรือ session เดิม

ผลยืนยันเพิ่มเติม 2026-11-15:
- Python 3.10 + Tobii SDK environment: 28 tests passed (ไม่ได้เชื่อมอุปกรณ์จริง)
- Occupied-port launcher test: 1 passed ไม่หยุดเจ้าของพอร์ต
- Final production build passed หลังปรับ console ให้ไม่มีลิงก์ Dashboard ในหน้าผู้เข้าร่วม
- API ZIP export ตรวจแล้ว: participants 1, pre_test 2, post_test 2, gaze 502, clicks 21, trials 1; ทุก CSV มี session_id ถูกต้อง และพบ leb-quiz/leb-submit/navigation route

## Figma External implementation
Automated: 37 passed, 1 Starlette TestClient deprecation warning. Existing regression cases preserved.
New tests cover four rounds with manual triggers, empty answers, scoring, duplicate start/end, track reservation, researcher/participant permission, redacted HTTP/WebSocket, URL restriction, controller watchdog, reset audit, retry attempt, backend restart and rounds.csv export.
Launcher collision integration: 1 passed. Production build passed.
These are isolated Mock/API/engine tests, not a real Figma interaction or hardware validation.
Live background-window/Figma navigation, F5 UI and 19 Present links not tested in this phase.

External UI follow-up: isolated localhost 5174/8001 browser login, Prototype Manager, Track reservation and round control screen verified. Baseline external Figma link loaded the prototype intro successfully. Recording was not started during this browser smoke check. Controller remained connected and console had no errors. This does not validate background throttling during an active recording or all 19 links. Added reopening allocated sessions and answer amendment with reason and prior values in audit; automated amendment test passed.
Windows transient PermissionError during atomic replace was observed once in regression; bounded retry added (five attempts), then full 37-test suite passed. Persistent file error still propagates.
