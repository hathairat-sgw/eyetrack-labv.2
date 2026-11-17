# วิธีเริ่มทดลองแบบสั้น

1. เปิด eyetrack-lab.code-workspace ใน VS Code
2. หยุด server รอบเดิมด้วย Ctrl+C ใน terminal ที่เปิดไว้ แล้ว F5: EyeTrack Lab: Run all
3. เข้า /researcher/external และใช้รหัสนักวิจัยจาก terminal
4. ครั้งแรก: Prototype Manager เปิดตรวจลิงก์ที่จะใช้ใน 4 รอบ แล้วกดยืนยันตรวจลิงก์แต่ละรายการ
5. สร้าง Participant → เลือก Track → ตรวจรายการ 4 รอบ → สร้าง Figma External Session
6. กดสร้างลิงก์ Consent / Calibration / Questionnaire → เปิดหน้าผู้เข้าร่วม
7. ผู้เข้าร่วมอ่านข้อมูล/ยินยอม → Calibration 5 จุด (Mock ใช้ปุ่มจำลองในหน้าต่างได้) → Pre-test 5 ข้อ
8. กลับหน้าควบคุม เปิด Figma ของ Test 0 ให้ผู้เข้าร่วมทำบนหน้าต่างแยก
9. ตรวจหน้าตั้งต้น จอ fullscreen และปิด hints ด้วยตนเอง แล้วติ๊ก 4 ช่อง → เริ่มบันทึกรอบ
10. เสร็จภารกิจ → จบรอบ / หยุดบันทึก → กรอก Late และ Quiz → ยืนยันคำตอบและจบรอบ
11. ทำซ้ำ Test 1,2,3 ตามลำดับ
12. กลับหน้าผู้เข้าร่วม ตอบ Post-test 4 หมวดรวม 24 คะแนน + ปลายเปิด 3 ข้อ ครั้งเดียว → จบการทดลอง
13. หน้าควบคุมกด Export

แบบสอบถามฉบับจริงมีผลกับ session ใหม่หลัง restart เท่านั้น session เก่าคงคำถามเดิมเพื่อรักษาข้อมูล
หากจอง session ก่อนตรวจลิงก์จะมี snapshot unverified; ถ้ายังไม่ consent ให้ปล่อย reservation พร้อมเหตุผลแล้วสร้างใหม่หลังตรวจลิงก์
โหมดนี้ยังเป็น Mock gaze; Hardware ยังล็อก ไม่มี Figma click/scroll telemetry

## ทางเข้าครั้งเดียวต่อคน
กดการ์ดรายคนใน Research Control Center ระบบจะเปิดหน้าผู้เข้าร่วมในแท็บใหม่ พร้อมคงหน้าควบคุมไว้
ผู้เข้าร่วมทำ consent → calibration → pre-test → 4 tasks → post-test → finish ด้วย session เดียว
ไม่ต้องสร้างลิงก์ด้วยตนเอง หากเบราว์เซอร์บล็อก popup ให้กดลิงก์สำรอง “เปิดหน้าผู้เข้าร่วม”
นักวิจัยยังต้องเริ่ม/จบ recording แต่ละรอบและกรอก Late/Quiz เพราะระบบไม่เห็น Submit ใน Figma
การกดคนที่ completed จะเปิด Results ไม่บันทึกซ้ำ หากต้องการลองซ้ำใช้พื้นที่ฝึกซ้อม
