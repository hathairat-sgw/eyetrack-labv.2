# Development Checklist

ตรวจโค้ด 2026-11-12 (ยังไม่ใช่ผลรันทดสอบรอบใหม่)

## Phase 1 — ตรวจระบบเดิม
- [x] ตรวจ frontend, backend, config, scripts, dependencies และรายชื่อ tests
- [x] Dashboard/Participants/Questionnaires/Runner/Results/Export: frontend/src/Researcher.jsx และ Editors.jsx มี UI และเรียก REST API
- [x] Consent/pre/calibration/tasks/post: frontend/src/Participant.jsx และ backend/engine.py มี state machine
- [x] Random task: Engine.create ใช้ random.Random(seed), shuffle และ snapshot
- [x] Mock: backend/devices.py สร้าง gaze จำลอง; Stimulus.jsx เป็น demo fixture
- [x] Tobii: devices.py มี discovery/calibration/subscribe แต่ Engine.create ยังล็อก hardware session; ไม่ถือว่าผ่านอุปกรณ์จริง
- [x] Figma: LebPreview.jsx แสดง Status(LS)+Search(HS); config/stimuli.json ระบุ visual_verified=false และ recording_enabled=false
- [x] Session storage/export: backend/storage.py, exporting.py; tests/test_research.py มี 19 tests รวม integrity/restart/disk failure
- [x] VS Code เดิมมี tasks แยก backend/frontend แต่ไม่มี launch.json หรือ launcher รวม
- [x] Regression tests 19 ผ่าน; frontend production build ผ่าน (2026-11-12)

## Phase 2 — One-Click Run
- [x] สร้าง launcher เริ่ม backend/frontend และสั่งเปิด browser หลัง readiness check
- [x] เพิ่ม VS Code launch.json สำหรับ F5 / Run และ scripts/start-all.ps1
- [ ] ตรวจการกด F5 จริงในหน้าต่าง VS Code และเปิด browser อัตโนมัติด้วยสายตา
- [x] Test พอร์ตชนผ่าน: ออก code 1 และไม่หยุด process ที่ครองพอร์ต
- [x] Launcher ส่งคำสั่ง shutdown ผ่าน stdin ไป Uvicorn และหยุดเฉพาะ child processes ของตน
- [x] Smoke startup/shutdown ผ่านทั้ง .venv และ .venv-hardware ใช้ temp data

## Phase 3 — Figma และ Runner
- [ ] ตรวจและสร้าง Baseline กับ 18 ชุดย่อยให้ครบ
- [ ] นำ assets/font ต้นฉบับและรายละเอียดหน้าที่ขาดมาใช้
- [ ] ตรวจ navigation/interactions และภาพที่ viewport เดียวกัน
- [ ] เชื่อม task registry/condition/subcondition กับ Runner และ random seed
- [ ] ตรวจ IDs, timestamps, click events และผลลัพธ์ใน export

## Phase 4 — Hardware และส่งมอบ
- [x] Discovery ผ่าน Python 3.10.10: connected=false, simulated=false, ไม่พบ Tobii; ไม่เริ่ม gaze/calibration
- [ ] ทดสอบ calibration/gaze/ถอดสายกับ Tobii จริง
- [ ] ตรวจพิกัดและ synchronization จริง
- [ ] ทดสอบ end-to-end และปรับคู่มือ

ไม่ลบหรือแก้ข้อมูลการทดลองเดิม และไม่แก้ OceanX_

## Questionnaires integration — 2026-11-12
- [x] อ่าน Word 2 ฉบับจาก IRB-Hathairat-final และบันทึกชื่อ/SHA256 ใน QUESTIONNAIRE_SOURCE.md
- [x] Pre-test 5 ฟิลด์ รวม Number อายุ; Post-test 24 ratings + 3 open questions ตามฉบับที่พบ
- [x] ฟอร์มแบ่งหมวด Progress/Previous/Next/Submit; backend validation และกัน submit ซ้ำ
- [x] Draft บน server พร้อม revision กันการเขียนทับจากหน้าต่างอื่น; โหลดหลัง refresh/restart
- [x] แสดงข้อมูล Pre-test ใน Post-test ไม่บังคับกรอกซ้ำ
- [x] คำตอบเชื่อม session/participant, timestamp; CSV/JSON export เดิม
- [x] รหัสนักวิจัย + signed participant link จำกัด session; ป้องกัน REST และ WebSocket
- [x] Browser: login, create session, pre draft/reload/submit, post preview ทั้ง 5 ส่วน/ย้อนกลับ
- [ ] Browser full workflow: fullscreen calibration ถูกปฏิเสธในเบราว์เซอร์ทดสอบ (not granted)
- [ ] รับ Word ฉบับแก้ไขเพิ่มเติม ผู้ใช้แจ้งว่ามีฉบับใหม่แล้ว รอพาธ/ไฟล์
- [ ] ยืนยันข้อความฉบับสุดท้ายและเลือกใช้กับ session ใหม่

ไม่เปลี่ยน configuration ของข้อมูลเดิมอัตโนมัติ; template ที่พบเปิดทบทวนได้จาก Questionnaire Manager

## 2026-11-17 — Track structure
- [x] ตรวจพบ Status(LS)+Search(HS) เชื่อม Mock Runner แล้วตาม tests/test_leb.py
- [x] สำรองไฟล์ที่แก้ใน work/backups ก่อนแก้
- [x] เพิ่ม registry 30 Tracks A/B/C และ 4 รอบคงที่; ทุก Track ready=false จนตรวจ mapping
- [x] เพิ่ม researcher-only GET /api/tracks รายงานช่องที่ขาด
- [ ] ตาราง mapping ราย Track/ภาพ 5 ภาพ: ไม่พบใน attachment ครั้งนี้
- [ ] Figma frame inventory ทุก variant และเฉลย Quiz: ยังตรวจไม่ครบ
- [ ] ยืนยัน protocol conflict: โค้ด pre ก่อน calibration, ภาพอ้าง calibration ก่อน pre
- [ ] F5 จริง/4-round Mock: ยังไม่ทดสอบเพราะไม่มี Track ที่ mapping ครบ

## ภาพอ้างอิง 2026-11-17
- [x] ได้รับภาพ 5 ภาพและถอด course/answer reference ทั้ง 4 รอบ
- [x] บันทึกนิยาม HS/LS และ Decision Error จากคู่มือ console
- [ ] ยังขาด mapping variant ของ Track 1–30 และการตรวจ frame/interaction
- [ ] Protocol calibration ก่อน pre-test รอยืนยันก่อนเปลี่ยนโค้ด

## Protocol confirmation 2026-11-17
- [x] ผู้ใช้ยืนยัน Consent → Calibration → Pre-test
- [x] Session ใหม่บันทึก workflow_version=calibration-before-pre-v1; session เก่าใช้ลำดับเดิม
- [x] Calibration สำเร็จไป Pre-test; ส่ง Pre-test ไป instructions; เริ่ม trial ต้องมี pre response
- [ ] Mapping Track: ผู้ใช้ยังไม่ทราบแหล่งข้อมูล คง ready=false

## User table received
- [x] บันทึก mapping ครบ 30 Tracks ตามตารางผู้ใช้ พร้อมชื่อ Good/Bad เดิม
- [x] Track 10/20/30 ใช้ชุดเหมือน 1/11/21 แต่มี ID แยก
- [x] ยืนยันข้อความแบบสอบถามเป็นฉบับสุดท้าย และ Post-test ครั้งเดียวหลังครบ 4 รอบ
- [ ] ตรวจจับคู่ชื่อ Good/Bad กับ frame HS/LS และสร้าง variants ครบ
- [ ] เปิดใช้ Track หลังตรวจ Runner ครบ 4 รอบ; ขณะนี้ ready=false ทั้งหมด

## Phase Figma External
- [x] เพิ่ม task_mode figma_external ใช้ Engine/Storage/Consent/Questionnaires/Calibration เดิม
- [x] Prototype Manager ลิงก์ 19 รายการ HTTPS Figma proto เท่านั้น พร้อมสถานะ/วันที่ตรวจ
- [x] จัดสรร 30 Tracks พร้อม snapshot และ duplicate ID แยก; ป้องกันจองซ้ำ
- [x] Research Control UI เปิดลิงก์ ยืนยัน readiness เริ่ม/จบด้วยมือ แล้วตอบ Late/Quiz
- [x] Controller WebSocket watchdog แยกจาก participant heartbeat; ไม่ใช้ hidden-page guard ของ React stimulus
- [x] rounds.csv + session.json schema 2; legacy exports คงเดิม
- [x] API/WebSocket participant ลบ external keys/variant labels และเฉลย
- [x] ปล่อย reservation ก่อน consent และ reset รอบปัจจุบัน มีเหตุผล/audit
- [x] Mock 4 รอบผ่าน engine tests รวม Decision Error/export/restart/retry
- [x] 37 automated tests, launcher collision test และ production build ผ่าน
- [ ] UI/browser สลับไป Figma จริงและ background throttling ยังไม่ตรวจ
- [ ] F5 จริงใน VS Code ยังไม่ตรวจรอบนี้
- [ ] ยังไม่ตรวจลิงก์ prototype ทั้ง 19 ผ่าน Present จริง; เริ่ม unverified
- [ ] แก้คำตอบย้อนหลัง/Reset รอบก่อนหน้าที่ยืนยันแล้ว ยังไม่มี UI/API
- [ ] Hardware device/display/timing จริงยังไม่ผ่าน; lock คงอยู่
- [x] ตรวจ browser แยกข้อมูล: login/Prototype Manager/จอง Track/หน้าควบคุม และ Baseline Figma เปิดได้
- [x] เพิ่มแก้คำตอบรอบที่ยืนยันแล้วพร้อมเหตุผลและ audit ค่าเดิม (ไม่ reset ลำดับ)
- [ ] ยังไม่ทดสอบ active-recording background throttling กับ Figma จริง และ F5 ผ่าน VS Code

## Questionnaire activation
- [x] เปิดใช้ Pre-test 5 ข้อ และ Post-test 24 ratings + 3 open questions ใน config/default.json ตามข้อความที่ผู้ใช้ยืนยัน
- [x] แก้ข้อความ Questionnaire Manager จากรอฉบับแก้ไขเป็นฉบับยืนยันแล้ว
- [x] Session เก่าคง snapshot เดิม ต้อง restart server และสร้าง session ใหม่เพื่อใช้ฉบับใหม่
- [x] 37 tests และ production build ผ่านหลังเปิดใช้ฉบับจริง

## Simplified entry and Drive reference integration
- [x] ตรวจ session ในภาพเป็น legacy Demo 2 งาน ไม่ใช่ external Figma; รักษาข้อมูลเดิม
- [x] เพิ่มปุ่มคนที่ 1–30 สร้าง Participant อัตโนมัติและเปิด session เดิมเมื่อกดซ้ำ
- [x] เพิ่มฝึกซ้อมลิงก์ 19 แบบ เปิดซ้ำได้ ไม่จอง Track/ไม่บันทึกข้อมูล
- [x] หน้าผู้เข้าร่วม external มีลิงก์ Figma ของรอบปัจจุบันโดยไม่เปิดเผยเฉลย/ชื่อเงื่อนไข
- [x] อ่าน Drive collect_data.py/server.py/README_DEV และนำแนวทาง gaze/pupil มาใช้ใน exploratory export
- [x] Tests 39 passed; production build ผ่าน
- [ ] Native mouse capture และการตรวจไฟล์ RAR ทั้งชุดยังไม่รวมใน runtime
- [ ] Tobii จริง/display mapping/timing ยังต้องทดสอบ; Hardware lock คงอยู่

## QA audit
- [x] แก้ end-round atomic boundary, orphan session, start-after-finish และ stale node ID
- [x] Start button ต้องมี readiness checks และ verified link
- [x] Browser Mock 4 รอบ → Post-test → completed → refresh → Export
- [x] ตรวจ ZIP 4 rounds, 623 mock gaze, 5 pre, 25 post rows และ IDs
- [x] Automated suite 43 ผ่าน, build ผ่าน; รายละเอียด docs/QA_REPORT.md
- [ ] Hardware และ prolonged background timer/F5 UI ยังไม่ยืนยัน

## Research UI refresh
- [x] ปรับ Dashboard โทน lavender/pastel, sidebar, summary cards และ progress
- [x] การ์ดผู้เข้าร่วม 30 คนมีสถานะจริง, filter A/B/C และค้นหา
- [x] ฝึกซ้อมแยกการ์ดและแสดงลิงก์ 19 รูปแบบเมื่อเปิด
- [x] พับเก็บ Prototype Manager/Advanced setup ลดความซับซ้อนหน้าหลัก
- [x] เพิ่ม timeline 4 รอบในหน้าควบคุมรายคน และ scroll ขึ้นต้นเมื่อเปลี่ยน session
- [x] แก้ quick-start callback ผิด scope พบจาก browser test
- [x] Browser: filter B=10, search T15=1, practice=19, กดคนที่15เปิด session ได้จริง ใช้ข้อมูล temp
- [x] 43 tests และ production build ผ่าน; ไม่แก้ participant/stimulus layout

## Single entry per participant
- [x] กดการ์ดรายคนครั้งเดียว: quick-start คืนลิงก์ participant เฉพาะ session และเปิดหน้าผู้เข้าร่วมอัตโนมัติ
- [x] สร้าง/เปิด session เดิม ครอบคลุม consent/calibration/pre/4 tasks/post/finish ไม่สร้าง session ใหม่ระหว่างขั้นตอน
- [x] Popup ถูกบล็อกมีลิงก์สำรอง คนที่ completed ไป Results
- [x] หน้าควบคุมแสดงคำแนะนำขั้นตอนปัจจุบัน และแสดง Task controls เฉพาะขั้นตอนงาน
- [x] ตัดข้อความซ้ำ/รหัสเทคนิคบนการ์ด พับประวัติการทดลอง
- [x] API test ตรวจ scoped link, participant permission, no duplicate allocation และ schema คำถามครบ
- [x] 44 tests ผ่าน และ production build ผ่าน
- [ ] การเปิด popup อัตโนมัติขึ้นกับการตั้งค่า browser; ยังไม่ได้ตรวจ UI live ในรอบแก้นี้

Task บน Figma ยังคงใช้ manual start/end ของนักวิจัย เพราะไม่สามารถอ่าน Submit ข้ามเว็บไซต์ ไม่ใช้เวลาจบอัตโนมัติที่คาดเดา

## Participant link regression fix
- [x] แก้ /researcher/undefined: ตรวจ participant_path ก่อนเปิด และ fallback ไป participant-link endpoint เมื่อ Backend เก่าไม่ส่ง field นี้
- [x] ป้องกัน URL ภายนอก/ข้าม session/token ว่าง ไม่เปิด undefined
- [x] Redirect /researcher/undefined กลับ Control Center
- [x] Node regression 3 tests ผ่าน และ production build ผ่าน
- [ ] ไม่ยืนยันการเปิด popup ผ่าน browser จริงในรอบแก้นี้


## Phase Hardware External integration — 17 พฤศจิกายน 2026
- [x] ตรวจ SDK บนโน้ตบุ๊ก: import ได้ ไม่พบ Tobii; ผู้ใช้ยืนยันอุปกรณ์อยู่อีกเครื่อง
- [x] เลือก Mock/Hardware ในหน้าการ์ด แยก allocation ไม่แก้ session เดิม
- [x] Hardware ต้องตรวจพบอุปกรณ์และมี protocol พร้อมก่อนสร้าง session
- [x] SDK Calibration 5 จุด เก็บผลจริง และ independent validation 5 จุด บันทึก raw/metrics/attempts
- [x] ป้องกันเริ่มงานก่อนผ่าน validation หรือ Serial/clock segment เปลี่ยน
- [x] ตัวนับข้อมูลที่เขียนแล้ว อัตรารับจริง อายุข้อมูลและ validity บนหน้าควบคุม
- [x] Optional native mouse เฉพาะช่วงงานและ optional screen video เก็บในเครื่อง/Export
- [x] Quality report, validation evidence, video integrity/recovery และไฟล์เดิม Export ร่วมกัน
- [x] Setup-Windows.cmd, Run-EyeTrack.cmd, Check-Tobii.cmd และคู่มือเครื่องเก็บข้อมูล
- [x] Chrome smoke: Mock gaze เพิ่ม, start/end และ WebM จาก canvas จำลองเขียน/ถอดรหัสได้
- [ ] ตรวจรับ Tobii จริง: discovery/calibration/validation/gaze/ถอดสาย/พิกัดและเวลา บนคอมพิวเตอร์อุปกรณ์
- [ ] ตรวจ native mouse กับ DPI/หลายจอ และวิดีโอ screen picker บนเครื่องเก็บข้อมูลจริง
- [ ] ตรวจคุณภาพและระยะเวลานานตามเกณฑ์ protocol ก่อนเก็บข้อมูลวิจัย

สถานะส่วนนี้แทนที่ข้อความ hardware lock และ native mouse not implemented ในบันทึกรุ่นเก่าด้านบน เฉพาะ Figma External workflow เท่านั้น legacy local stimuli ยังไม่เปิด Hardware

- [x] Final verification: 59 Python tests, 4 Node tests, production build and pip check passed.
- [ ] Physical Tobii acceptance on the desktop remains pending.
