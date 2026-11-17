# ใช้งาน Tobii Pro Spark บนเครื่องเก็บข้อมูล

ปรับปรุง 17 พฤศจิกายน 2026 — โค้ดพร้อมสำหรับการตรวจรับที่เครื่องอุปกรณ์ **ยังไม่ผ่านการตรวจรับฮาร์ดแวร์จริงจากโน้ตบุ๊กที่พัฒนา**

## ติดตั้งและเปิด

1. Windows + Node.js 22 + Python 3.10 x64 พร้อม Python Launcher + Tobii Pro Eye Tracker Manager
2. เปิด Setup-Windows.cmd ครั้งแรก ถ้ามี Python 3.10 อยู่พาธอื่นใช้ scripts/setup-hardware.ps1 -Python310 "พาธเต็ม python.exe"
3. เสียบ Tobii ตั้ง active display ใน Manager ให้ตรงกับจอทดลอง ใช้จอเดียวสำหรับตรวจรับครั้งแรก ปิดโปรแกรมอื่นที่จับ Tobii อยู่
4. เปิด eyetrack-lab.code-workspace และ F5; ระบบเลือก .venv-hardware อัตโนมัติ Device Service อยู่ใน FastAPI
5. เข้าหน้าควบคุม เลือก Tobii จริง จะต้องเห็นรุ่นและ Serial ไม่มีการ fallback เป็น Mock
6. ถ้าพบหลายอุปกรณ์ ให้ตั้ง EYETRACK_TOBII_SERIAL ก่อน Run

Check-Tobii.cmd เป็น diagnostic ของผู้ดูแล รับ gaze 5 วินาทีโดยเจตนา ไม่ใช่การทดลองของผู้เข้าร่วม ไม่เก็บ gaze ดิบ และไม่พิสูจน์ Calibration เก็บรายงานใน work/hardware-check.json ซึ่งไม่ขึ้น GitHub

## ก่อนผู้เข้าร่วม

- ตรวจแบบสอบถาม/consent/retention และยืนยัน protocol ใน Questionnaires → Research protocol → Save version
- เปิด Prototype Manager ตรวจ 4 ลิงก์ของ Track และยืนยันหน้าตั้งต้นก่อนสร้าง session ข้อมูลเดิมมี snapshot ไม่เปลี่ยนภายหลัง
- กำหนดเกณฑ์ Validation ตามงานวิจัยก่อนกดการ์ดรายคน ค่าเริ่มต้น max mean normalized error 0.04, valid fraction 0.7 และอย่างน้อย 20 ตัวอย่างต่อจุด เป็นค่าเริ่มต้นตรวจระบบ ไม่ใช่เกณฑ์วิจัยที่ผ่านการรับรอง
- Mock และ Hardware มีการจอง Track แยกกัน เปลี่ยนโหมดของ session ที่สร้างแล้วไม่ได้

## Calibration และ Validation

หลังยินยอม เว็บแสดง Calibration เต็มจอ 5 จุด รอให้มอง 1.2 วินาทีก่อนสั่ง SDK collect_data แต่ละจุด แล้ว compute_and_apply เก็บผล SDK และข้อมูล calibration samples จริงใน session.json

Hardware ต้องผ่าน independent validation อีก 5 จุดที่ (0.2,0.2), (0.8,0.2), (0.2,0.8), (0.8,0.8), (0.5,0.5) แต่ละจุดรอ 1.2 วินาทีแล้วรับ gaze 1.2 วินาที เก็บ raw แยกจาก task gaze ใน validation.json ทั้งสองตาต้องมีจำนวน/valid fraction/mean radial error ผ่านทุกจุด

หน่วย error เป็นระยะใน normalized display coordinates ไม่ใช่องศา และไม่อ้าง spatial accuracy ของรุ่นอุปกรณ์ ระบบตรวจ Fullscreen และขนาด viewport ตรง screen แต่ไม่รู้ว่า Figma อีกหน้าต่างอยู่จอใด นักวิจัยต้องตรวจจอจริงก่อนทุกงาน

ถ้าไม่ผ่าน: ปรับท่านั่ง แสง/แว่น และตรวจจอ แล้ว Calibration ใหม่ ประวัติเดิมเก็บไว้ ถ้าเริ่ม backend ใหม่หรือเปลี่ยน Serial ต้อง Calibration/Validation ใหม่

ถ้า web calibration ใช้ไม่ได้ ให้หยุดและบันทึกข้อผิดพลาด ยังไม่มีปุ่มให้ใช้ผลจาก Eye Tracker Manager เพื่อข้าม gate เพราะไม่สามารถยืนยันว่าเป็นของผู้เข้าร่วมปัจจุบันและมีคุณภาพผ่านเกณฑ์ได้

## บันทึกงานจริง

หลัง Pre-test ครบ เปิด Figma → ตรวจหน้าตั้งต้น/จอ/Fullscreen/hints → เริ่มบันทึกรอบ → ผู้เข้าร่วมทำงาน → จบรอบ/หยุดบันทึก → บันทึกคำตอบ Late/Quiz ทำครบ 4 รอบแล้ว Post-test ครั้งเดียว

กดเริ่มคือบันทึกเวลา researcher_manual แล้ว subscribe_to SDK ตัวอย่างแรกอาจช้ากว่าเวลาที่กดเริ่ม ห้ามตีความว่า timestamp นั้นคือเฟรมแรกของ Figma หรือเวลาคลิกจริง ปุ่ม Submit ใน Figma ยังไม่เชื่อมกับการจบรอบอัตโนมัติ

หน้าควบคุมแสดงจำนวน gaze ที่เขียนลงไฟล์แล้ว อัตรารับจริงจาก backend และอายุข้อมูลล่าสุด แยก validity สองตา อัตรานี้ต่างจาก configured_hz ของอุปกรณ์ได้ ตรวจ quality_report.json หลัง Export ด้วย

เก็บ raw timestamps ของ SDK และ backend แยกหน่วย มี SDK/backend clock samples ก่อน subscribe และหลัง unsubscribe รวม browser 7 รอบพร้อม offset/uncertainty ใน metadata ไม่รับรอง synchronization ระดับเฟรมจนกว่าจะวัดกับระบบจริง

ไม่มี gaze เกิน 3 วินาที / queue overflow / controller หลุด / เขียนไฟล์ผิดพลาด จะหยุดรอบเป็น incomplete ทำใหม่สร้าง Trial ใหม่ ข้อมูลเดิมไม่ถูกเขียนทับ

## เมาส์และวิดีโอ

Native mouse เป็นตัวเลือกใน Hardware ใช้ pynput เฉพาะช่วงบันทึกงาน ไม่จับ keyboard ฟิลเตอร์ชื่อหน้าต่าง Figma/LEB2 เป็น heuristic ไม่ใช่การยืนยัน URL เก็บ physical pixels บน virtual desktop ใน mouse.csv; ไม่ใช่ DOM click, ไม่ทราบ element หรือ scroll offset หน้าเว็บ ห้ามปนกับพิกัด CSS จาก browser โดยไม่ตรวจ DPI/mapping

วิดีโอเป็นตัวเลือก กดเริ่มอัดหน้าจอหลัง Pre-test แล้วเลือกจอ/หน้าต่าง Figma ไม่มีเสียง เก็บ ordered chunks ลงเครื่อง รวมใน ZIP หลังหยุดสำเร็จ กรณีขาดการเชื่อมต่อมี .part และสถานะ incomplete ไม่อ้างคลิปสำเร็จ มี clock estimates ใน video_manifest.json แต่ยังไม่ใช่ frame-accurate synchronization ห้ามปิดเว็บก่อนขึ้นบันทึกคลิปแล้ว และทดสอบภาระการอัดจริงก่อนเก็บงานวิจัย

## ตรวจรับครั้งแรกที่เครื่อง Tobii

1. Check-Tobii: พบ Serial ถูกต้อง มี sample_count > 0 และตรวจ validity/rate
2. ทำ session ทดสอบที่ผู้ดูแลยินยอม Calibration และ Validation ผ่าน ตรวจว่าคลาดเคลื่อนเหมาะกับขนาดเป้าหมายงานจริง
3. บันทึก 4 รอบ ดู counter เพิ่มและไม่หยุดเมื่อไปแท็บ Figma ตรวจวิดีโอและเมาส์ว่าตรงตำแหน่งบนจอ
4. ถอดสายกลางรอบ ต้องหยุดภายในประมาณ 3 วินาทีของตัวอย่างสุดท้ายและ trial incomplete; ต่อสายแล้วทำใหม่ไม่ทับ Trial เดิม
5. ตรวจควบคุมหลุด ปิด backend กลางงาน เปิดใหม่ และข้อมูลดิบ/ไฟล์ส่งออกยังอ่านได้
6. วัด spatial error, timing uncertainty/drift และ missing-data rate ตาม protocol บันทึกรายงานการตรวจรับแยกจากผล Mock

เกณฑ์ผ่านทางซอฟต์แวร์ไม่ใช่การรับรองคุณภาพงานวิจัย ต้องบันทึกผลจริงของทั้งหกข้อก่อนเก็บข้อมูลผู้เข้าร่วมจริง

แหล่งอ้างอิง: [Tobii SDK Python](https://developer.tobiipro.com/python/python-step-by-step-guide.html), [Calibration และ validation](https://www.developer.tobiipro.com/commonconcepts/calibration.html), [Native mouse](https://pynput.readthedocs.io/en/latest/mouse.html), [Screen capture](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Capture_API/Using_Screen_Capture)
