import React,{useState} from 'react';
export default function Practice({session,act,busy}){
 const [query,setQuery]=useState(''),[menu,setMenu]=useState(false);
 const events=session.practice_attempts?.at(-1)?.events||[];
 const done=new Set(events.map(e=>e.action));
 const send=action=>act('/practice/'+action).catch(()=>{});
 return <><h1>ฝึกใช้งานก่อนทดลอง</h1><p>ภารกิจฝึกเท่านั้น ไม่ใช่งานวิจัย และไม่บันทึก gaze หรือ clicks ลงข้อมูลทดลองหลัก</p><p>ทำครบ 4 กิจกรรม แล้วดำเนินการต่อ</p>
 <div className="soft-panel"><button disabled={busy} onClick={()=>send('button')}>1. ลองคลิกปุ่ม {done.has('button')?'✓':''}</button>
 <button disabled={busy} onClick={()=>{setMenu(!menu);send('menu')}}>2. เปิดเมนู {done.has('menu')?'✓':''}</button>{menu&&<p>เมนูฝึก: หน้าหลัก · ข้อมูลตัวอย่าง</p>}
 <form onSubmit={e=>{e.preventDefault();if(query.trim())send('search')}}><label>3. ค้นหาคำว่า “ตัวอย่าง”<input value={query} onChange={e=>setQuery(e.target.value)} required/></label><button disabled={busy||query.trim()!=='ตัวอย่าง'}>ค้นหา {done.has('search')?'✓':''}</button></form>
 <p role="status">สถานะตัวอย่าง: พร้อมใช้งาน</p><button disabled={busy} onClick={()=>send('status')}>4. ฉันอ่านสถานะแล้ว {done.has('status')?'✓':''}</button></div>
 <button className="primary" disabled={busy||done.size<4} onClick={()=>send('complete')}>จบการฝึก → แบบสอบถามก่อนทดลอง</button></>;
}
