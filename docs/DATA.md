# ข้อมูล เวลา และพิกัด

## Time domains

| Field | หน่วย / ต้นกำเนิด |
|---|---|
| clicks.timestamp | มิลลิวินาที จาก performance.now() ของ document นั้น |
| viewport.time_origin_ms | performance.timeOrigin; epoch milliseconds ของ browser |
| backend_received_us / trials.started_us / ended_us | microseconds จาก Python time.perf_counter_ns() // 1000 |
| gaze.device_timestamp | device_time_stamp จาก SDK; microseconds |
| gaze.system_timestamp | system_time_stamp จาก SDK; microseconds |
| created_at / submitted_at | UTC ISO 8601 เพื่ออ้างอิงเวลา ไม่ใช้วัด task duration |

ทุกครั้งก่อนเริ่ม trial frontend ส่งการเทียบเวลา 7 รอบ:
offset_us = backend_us - (browser_before_ms + browser_after_ms) × 500
uncertainty_us = (browser_after_ms - browser_before_ms) × 500

ใช้รอบที่ uncertainty ต่ำที่สุดจาก metadata ที่สัมพันธ์กับ trial:
browser event ใน backend clock ≈ timestamp × 1000 + offset_us
นี่เป็นการประมาณภายใต้ network scheduling ไม่ใช่หลักฐานว่าเทียบเวลาได้แม่นยำระดับ microsecond
ค่า RTT/uncertainty ถูกเก็บครบเพื่อประเมิน ไม่ปรับ timestamp ดิบ

Hardware adapter อ่าน SDK get_system_time_stamp ระหว่าง backend before/after
เพื่อเชื่อม SDK system clock กับ backend monotonic clock โดยเก็บ midpoint และ uncertainty
ไม่เทียบ device_timestamp กับ browser timestamp โดยตรง
ต้องทดสอบ clock drift และ latency จริงด้วย Tobii ก่อนใช้เป็นข้อมูลวิจัย

## Coordinates

- gaze ซ้าย/ขวาเก็บ normalized display coordinates ดิบ และ validity แยกกัน
- ไม่มีการเฉลี่ยตาทั้งสองหรือ clamp ค่าให้อยู่ใน 0–1
- ค่า NaN/Infinity ใน raw_json ใช้ string ตามค่าเดิม เพราะ JSON ไม่รองรับ non-finite numbers; CSV เก็บค่าดิบที่ serializer แสดง
- client_x/client_y เป็น CSS pixels ใน viewport
- screen_x/screen_y เป็น browser screen coordinates ซึ่งขึ้นกับ OS/DPI
- เก็บ screen dimensions, viewport, devicePixelRatio, browser screen position, scroll, fullscreen, timeOrigin และ visualViewport scale
- event page_url ของ fixture เป็น logical stimulus route และ view ที่แสดง ไม่เก็บค่าที่ผู้ใช้พิมพ์ค้นหา

ห้ามแปลง normalized gaze ด้วย innerWidth โดยไม่ตรวจว่าจอเต็มตรงกับ active display ของ Tobii
สำหรับ fullscreen บนจอที่ถูกต้องและ scale คงที่ จึงค่อยตรวจสมมติฐาน x_css = gaze_x × viewport_width
และ y_css = gaze_y × viewport_height กับตำแหน่งเป้าหมายจริง
หน้าไม่เต็มจอ/หลายจอ/Windows scaling ต้องวัด mapping โดยเฉพาะ
รุ่นนี้ยังไม่สร้าง heatmap เพราะยังไม่ผ่าน coordinate validation

## Integrity

- consent เป็นข้อกำหนดก่อน recording และ metadata
- session.json snapshot เก็บ protocol, questionnaire versions, tasks, actual sequence, seed, condition และ mode
- raw events ผูก participant_id / session_id / trial_id / task_id
- event_id ใช้ deduplicate batch ที่ retry ภายใน trial
- questionnaire answers เก็บ JSON ใน CSV เพื่อรักษาหลายตัวเลือก เครื่องหมาย comma และ newline
- trial ที่ crash ไม่ทราบ end time จะมีค่า null ใน JSON / ว่างใน CSV ไม่คำนวณ duration สมมติ
- exports คำนวณจำนวนจากไฟล์ดิบเพื่อคืนจำนวนที่ยังไม่ทัน checkpoint ก่อน crash
- invalid header หรือ incomplete CSV row ทำให้ export ล้มเหลวอย่างชัดเจน ไม่ซ่อม raw data เงียบ ๆ
- results เป็น descriptive summaries ไม่ใช่ผลวิเคราะห์ fixation, attention หรือ clinical measurement



## เพิ่มเติม 17 พฤศจิกายน 2026: Hardware External

- gaze.csv เป็น raw SDK แยกตาและ timestamps เดิม ตัวอย่าง Validation ไม่ปน task gaze
- validation.json เก็บ current/previous_attempts พร้อม targets, viewport, samples, metrics และเกณฑ์ snapshot
- quality_report.json คำนวณใหม่จาก gaze.csv เมื่อ export: จำนวน, validity, observed Hz จาก SDK timestamps, ลำดับ timestamp, serial/clock segment และ SDK clock alignment
- mouse.csv เป็น native Windows physical pixels เฉพาะ Figma/LEB2 title ระหว่าง Hardware trial มี participant/session/trial/task IDs; DOM และ URL ระบุ unavailable
- video/*.webm + video_manifest.json เก็บ chunk hashes และข้อมูลเวลา; incomplete เป็น .webm.part ไม่อ้างว่าเล่นได้
- ไม่ยอม Export ขณะกำลังอัดวิดีโอ ให้กดหยุดและรอเขียนสำเร็จก่อน
- gaze_features_exploratory.csv ใช้ screen dimensions จาก browser เป็น CSS pixel estimate มีป้าย coordinate_space และ device_pixel_ratio ห้ามเทียบกับ native physical pixels โดยตรง
- Mock และ Hardware แยกการจอง Track และโฟลเดอร์ตั้งแต่สร้าง session ไม่มีการย้าย/แปลง session เดิมเป็นข้อมูลจริง
