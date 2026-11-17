# Figma verification log

Source: https://www.figma.com/design/qr6rOEsr0AGFYxn8Q3mEUq/LEB2-Cheap-copy?node-id=888-23653

ตรวจ 9 พฤศจิกายน 2026 ผ่าน browser:
- เปิด canvas ได้
- Pages ที่พบ: Final version working on right now, back up, Pilot_test_1
- กลุ่ม BASE : MASTERWEB, Good + Good, Bad + Bad, Mixed Bad+ Good)
- Good + Good ที่เลือกจาก Layers มี node-id 888-61224
- Mixed ที่เลือกจาก Layers มี node-id 888-35253
- ตัวอย่าง label ที่อ่านได้: (Mixed)Menu+Button, (Mixed)Button+Menu, (Mixed)Status+Menu,
  (Mixed)Status+Button, (Mixed)Button + Status, (Mixed)Button + Search, (Mixed)Status+Search
- พบ section ระบุว่า UI ส่งงานทั้งหมด ไม่ได้เชื่อม flow และไม่ได้เพิ่มเข้าไปใน Mock up
- กด Present เพื่อเปิด prototype แล้วพบ Sign up for Figma จึงยังตรวจ flow ไม่ได้

รายการข้างต้นเป็นเพียง inventory ไม่ใช่หลักฐานการทำงานของปุ่ม
ยังไม่ได้ตรวจครบทุก frame/สี/ฟอนต์/interaction และยังไม่มีการอ้าง visual fidelity

ผู้ใช้เลือก:
- รองรับทุกชุดเปรียบเทียบ
- นักวิจัยเลือกหนึ่งชุดต่อ session
- จัดเก็บโปรเจกต์ใน Project/eyetrack-lab

งานที่ต้องดำเนินต่อเมื่อเข้าถึง prototype:
1. ระบุชุดย่อยทั้งหมดและ starting frame ที่แต่ละงานใช้
2. จับคู่หน้าจอ, state, navigation และ completion conditions จาก prototype จริง
3. เก็บ reference viewport, typography, spacing, assets และ stable target IDs
4. สร้าง React stimulus โดยแยก CSS จาก management UI
5. ตรวจ screenshot และ flow เทียบ reference ก่อนเปิด source_verified
6. ใส่ condition/subcondition mapping จริง แทน Demo fixture


## ตรวจต่อ 10 พฤศจิกายน 2026 หลังผู้ใช้ลงชื่อเข้าใช้

- เปิด prototype ได้แล้ว ไม่ติดหน้าลงชื่อเข้าใช้
- Console node 1108:173438 แสดง Baseline, LS+HS (9 ชุด), HS+HS (6 ชุด), LS+LS (3 ชุด)
- Baseline intro: 888:87148
- ยืนยัน Status(LS)+Search(HS) จากการกดปุ่มชื่อชุดใน console:
  intro 888:52553 → Start The Task → classes 888:49709 → MDT313 →
  syllabus 888:52250 → Assessment Activity 888:51745 → Functions Submit →
  detail 888:51995 → Submit → console 1108:173438
- การกด Quiz ไม่เปลี่ยนหน้า และแสดง hotspot ของปุ่มอื่น
- ผู้ใช้ยืนยันให้คงพฤติกรรมตาม Figma รวม Quiz ไม่เปลี่ยนหน้าและ Submit กลับ console
- ตารางพบ 7 แถว; Late Submitted 2 แถว (Arrays, Full-Stack); ยังไม่กำหนดคำตอบจำนวน Quiz จากการเดา
- Status Submitted และ Late Submitted ใช้สีเขียวเหมือนกันในชุดนี้
- วันครบกำหนด Functions ในตารางกับรายละเอียดไม่ตรงกันในต้นฉบับ จึงคงข้อความตามแต่ละหน้า
- Reference browser 1440×1000, fit width/height, frame rendered (48,80)–(1392,920)
- พบชื่อ font resources Prompt (Regular/Medium/SemiBold/Bold), Roboto variable; ยังไม่นำเข้าไฟล์
- ตัวส่งออก pageAssets ไม่รองรับภาพ/ฟอนต์ที่ Figma โหลดเป็นชนิด other จึงยังไม่มี asset ต้นฉบับในเว็บ

เพิ่ม `/stimuli/leb-preview` เป็น preview สำหรับตรวจการเดินหน้าเท่านั้น ไม่เชื่อม session/CSV
มี console + intro + classes + syllabus + assessment + detail; ส่วนที่ถอดไม่ครบมีป้ายระบุ
ภาพประกอบและลายภาพรายวิชายังไม่มี ไม่อ้างความตรงภาพ และ source_verified ยังคง false
เส้นทางนี้ยังถูก backend ปฏิเสธเมื่อใช้เป็นงานใน session ตาม guard เดิม
รายการชุดย่อยทั้งหมดเก็บใน config/stimuli.json; ยังไม่ถือว่าตรวจ flow ครบทั้ง 18 ชุด
