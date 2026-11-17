import React,{useState} from 'react';
import {api} from './api';
export default function ResearcherLogin({children}){
 const [ready,setReady]=useState(!!sessionStorage.getItem('researcher-access')),[password,setPassword]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 if(ready)return <><div className="spread" style={{padding:'8px 24px',background:'#eaf3f4'}}>Researcher · ข้อมูลส่วนบุคคล<button onClick={()=>{sessionStorage.removeItem('researcher-access');setReady(false)}}>ออกจากระบบ / เปลี่ยนรหัสเข้าใช้</button></div>{children}</>;
 return <main className="panel padded" style={{maxWidth:520,margin:'80px auto'}}><h1>EyeTrack Lab</h1><h2>เข้าสู่ระบบนักวิจัย</h2><p>ใช้รหัสที่แสดงใน Terminal เมื่อเปิดระบบ หรือรหัสที่กำหนดผ่าน EYETRACK_RESEARCHER_PASSWORD</p><form onSubmit={async e=>{e.preventDefault();setBusy(true);try{const r=await api('/auth/login',{password});sessionStorage.setItem('researcher-access',r.token);setPassword('');setReady(true)}catch(e){setError(e.message)}finally{setBusy(false)}}}><label>รหัสนักวิจัย<input type="password" required value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></label>{error&&<p role="alert">{error}</p>}<button className="primary" disabled={busy}>เข้าสู่ระบบ</button></form></main>
}
