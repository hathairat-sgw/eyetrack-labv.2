# EyeTrack Lab

ระบบเก็บการทดลอง LEB2 บน localhost สำหรับ Windows: React/Vite + FastAPI + Tobii Pro SDK เก็บ JSON/CSV/วิดีโอไว้ในเครื่อง ไม่มีฐานข้อมูลหรือ cloud storage

## เริ่มใช้งานบนคอมพิวเตอร์ที่ต่อ Tobii

1. ติดตั้ง **Node.js 22**, **Python 3.10 x64 พร้อม Python Launcher** และ **Tobii Pro Eye Tracker Manager**
2. ดาวน์โหลด/clone repository ลงเครื่องนั้น ไม่ต้องย้าย `.venv` หรือ `node_modules` จากเครื่องอื่น
3. เปิด `Setup-Windows.cmd` ครั้งแรก รอการติดตั้งจบ
4. เสียบ Tobii และกำหนด active display ให้ตรงกับจอทดลองใน Eye Tracker Manager
5. เปิด `eyetrack-lab.code-workspace` ใน VS Code กด **F5 → EyeTrack Lab: Run all** หรือเปิด `Run-EyeTrack.cmd`
6. เว็บเปิดอัตโนมัติ ใช้รหัสนักวิจัยจาก Terminal

ถ้าเปิดระบบเวอร์ชันเดิมอยู่ ให้หยุดการทดลองและ Stop ใน VS Code ก่อนกด F5 ใหม่ ห้ามปิดกลางการเก็บจริงเพื่ออัปเดต

## เก็บข้อมูลหนึ่งคน

- เข้าหน้า **Figma External · Control** เลือก **Tobii · สายตาจริง** และตรวจอุปกรณ์
- ตรวจข้อความวิจัย ความยินยอม และการเก็บข้อมูลที่ **Questionnaires → Research protocol** แล้วบันทึกฉบับที่นักวิจัยตรวจแล้ว
- เปิด Prototype Manager ตรวจลิงก์ Figma ที่จะใช้ก่อนสร้าง session ระบบเก็บ snapshot ไม่เปลี่ยนตามการแก้ลิงก์ภายหลัง
- กดการ์ดผู้เข้าร่วมหนึ่งครั้ง เพื่อสร้าง/เปิด session เดิมและหน้าผู้เข้าร่วม
- ผู้เข้าร่วม: **ยินยอม → Calibration 5 จุด → ตรวจพิกัด 5 จุด → Pre-test → งาน 4 รอบ → Post-test ครั้งเดียว → จบ**
- นักวิจัย: เปิด Figma หน้าตั้งต้น ตรวจจอ/Fullscreen/ปิด hints แล้วกด **เริ่มบันทึกรอบ** เมื่อพร้อม กด **จบรอบ / หยุดบันทึก** เมื่อทำเสร็จ แล้วกรอก Late/Quiz
- ตัวนับข้อมูล อัตรารับจริง อายุข้อมูลล่าสุด และ validity แยกสองตาอยู่หน้าควบคุม ไม่มี gaze overlay บนหน้าทดลอง
- เลือกอัดหน้าจอได้หลัง Pre-test เลือกหน้าต่าง/จอทดลองเอง วิดีโอไม่อัดเสียงและรวมใน Export หลังหยุดบันทึกคลิปสำเร็จ
- Export ZIP หลังจบหรือหยุดรอบและวิดีโอแล้ว เก็บต้นฉบับบนเครื่องไว้ด้วย

การเปิด Figma ไม่เริ่มบันทึก และ Submit ใน Figma ไม่หยุดเอง เวลาเริ่ม–จบเป็นการกดโดยนักวิจัย

## สถานะที่ตรวจแล้ว

- Mock workflow และ Hardware workflow contracts ผ่าน automated tests โดย Hardware contracts ใช้ adapter จำลองที่ระบุชัด
- Chrome smoke test: เลือกโหมด แสดงตัวนับ Mock เริ่ม/หยุดรอบ และอัด/เขียน/เปิดอ่าน WebM จาก canvas จำลอง
- SDK 2.1.0.1 import ได้บน Python 3.10 x64 แต่โน้ตบุ๊กที่พัฒนานี้ **ไม่มี Tobii ต่ออยู่**
- ยังไม่อ้างว่าผ่านการตรวจ Tobii จริง: detection, calibration, validation, gaze, native mouse กับ Figma, ถอดสาย และ synchronization ต้องตรวจบนเครื่องที่ต่ออุปกรณ์
- Hardware ผ่าน Figma External ได้เมื่อพบอุปกรณ์ มี protocol พร้อม Calibration และ independent validation ผ่าน ระบบไม่เปลี่ยนเป็น Mock เมื่ออุปกรณ์หาย
- ค่าเกณฑ์ตรวจพิกัดเริ่มต้นเป็นค่าตรวจระบบ ปรับตาม protocol ก่อนสร้าง session ไม่ใช่การรับรองความแม่นยำของงานวิจัย

## ไฟล์และข้อมูล

`data/mock` กับ `data/hardware` แยกกัน และแยกการจอง Track ต่อโหมด ข้อมูลฝึกเดิมไม่ขวางการเก็บจริง

ZIP ต่อ session: `participants.csv`, `pre_test.csv`, `post_test.csv`, `gaze.csv`, `clicks.csv`, `trials.csv`, `rounds.csv`, `session.json`, `quality_report.json`, `README.txt` และไฟล์เสริมตามการใช้งาน:

- `validation.json`: ตัวอย่างดิบและผลตรวจพิกัดทุกครั้ง
- `mouse.csv`: เมาส์ Windows เฉพาะช่วงบันทึก บนหน้าต่างชื่อ Figma/LEB2 ไม่ทราบ DOM หรือปุ่มจริง
- `video/*.webm` และ `video_manifest.json`: วิดีโอที่เขียนสำเร็จ; `.webm.part` คือคลิปไม่สมบูรณ์
- `gaze_features_exploratory.csv`: ข้อมูลอนุพันธ์เพื่อสำรวจ ไม่ใช่ fixation classifier ที่ validate แล้ว

ห้ามอัปโหลด `data`, `.env`, วิดีโอผู้เข้าร่วม หรือรหัสผ่านไป GitHub `.gitignore` ยกเว้นไฟล์เหล่านี้ไว้แล้ว

## ตรวจอุปกรณ์และทดสอบ

`Check-Tobii.cmd` ทดสอบสัญญาณสายตาผู้ดูแล 5 วินาที เก็บรายงาน `work/hardware-check.json` ใช้ตรวจระบบ ไม่ใช่ข้อมูลผู้เข้าร่วม และไม่ใช่การตรวจ Calibration

```powershell
.\.venv-hardware\Scripts\python.exe -m pytest -q
node --test tests/test_participant_link.mjs tests/test_launcher.mjs
node scripts/ui-smoke.mjs
cd frontend
npm.cmd run build
```

UI smoke ใช้ Chrome ที่ติดตั้งอยู่ พอร์ตและข้อมูลชั่วคราว ไม่หยุดระบบที่ผู้ใช้เปิดอยู่

คู่มือเพิ่มเติม: [เริ่มเก็บข้อมูลจริง](docs/HARDWARE.md), [ข้อมูล](docs/DATA.md), [Checklist](docs/DEVELOPMENT_CHECKLIST.md), [QA](docs/QA_REPORT.md)
