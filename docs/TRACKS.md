# Track implementation status

30 IDs T01–T30, groups A/B/C, 10 per group. Four fixed rounds are represented in config/tracks.json.
T10 copies T01, T20 copies T11, T30 copies T21; IDs remain distinct.
All ready flags are false. No variant/course or answer-key mapping has been invented.
Researcher-only GET /api/tracks reports the missing fields using existing role authorization.

Missing evidence: the five referenced images were not present in this attachment directory; exact per-track mapping, per-variant frame IDs and course/Quiz answer keys require source verification.
Current protocol in Participant.jsx remains consent → pre-test → calibration. User reference says calibration before pre-test; do not change until confirmed.
Figma web fetch failed on 2026-11-17; visual inventory remains incomplete.


## ภาพอ้างอิงที่ได้รับ 17 พฤศจิกายน 2026
ภาพ 1–3 เป็นคู่มือ console; ภาพ 4–5 เป็นภาพรวมชุด Mixed/Bad/Good
- HS = High-Salience; LS = Low-Salience
- Test 0: MDT310 Eyes Tracking; Late 1, Quiz ค้าง 2
- Test 1: MDT313 Web Programming; Late 2, Quiz ค้าง 1
- Test 2: MDT312 UX/UI Designs; Late 1, Quiz ค้าง 2
- Test 3: MDT311 Confirmation Bias; Late 2, Quiz ค้าง 1
- Decision Error 0 เมื่อ Late และ Quiz ตรงทั้งคู่ มิฉะนั้น 1
- คู่มือระบุ 7 รายการ: ยังไม่ส่ง 1, ส่งแล้วปกติ 3, ส่งล่าช้า+ควิซค้างรวม 3
- ยืนยันชื่อกลุ่ม Good+Good, Bad+Bad, Mixed จากภาพรวม แต่ภาพไม่ได้ระบุ HS/LS mapping ราย Track ครบถ้วน
- ภาพระบุ consent → calibration 5 จุด → pre-test; ยังรอผู้ใช้ยืนยันเปลี่ยน protocol เดิม
เฉลยอยู่ใน config/backend นักวิจัยเท่านั้น ไม่เพิ่มใน participant bundle
Track ทุกตัวยังคง ready=false; ภาพรวมไม่ละเอียดพอสำหรับถอดข้อความและ interaction ราย frame

## Track mapping supplied by user
Mapping now complete in config/tracks.json: baseline + 9 GB + 6 GG + 3 BB variants.
Good/Bad labels retained exactly as supplied; HS/LS source labels must be matched during frame verification.
All 30 tracks remain not runnable until component routes and four-round runner are validated.
Post-test: once after all four rounds, as confirmed by user. Questionnaire text supplied in chat is final, including repeated items and 4.6 wording.
