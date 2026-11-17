import React,{useEffect,useRef,useState} from 'react';
import {api,accessToken,syncClocks} from './api';
export default function ScreenRecorder({session}){
 const rec=useRef(null),[state,setState]=useState('idle'),[error,setError]=useState('');
 const sid=session?.session_id;
 function stop(){if(rec.current&&rec.current.state!=='inactive')rec.current.stop()}
 useEffect(()=>()=>stop(),[sid]);
 useEffect(()=>{if(['post','thankyou','completed','withdrawn','interrupted'].includes(session?.state))stop()},[session?.state]);
 async function start(){
  if(state==='recording'||state==='starting'||state==='saving')return;
  setState('starting');setError('');let stream;
  try{
   if(!navigator.mediaDevices?.getDisplayMedia||!window.MediaRecorder)throw Error('ใช้ Chrome หรือ Edge ที่รองรับการอัดหน้าจอ');
   stream=await navigator.mediaDevices.getDisplayMedia({video:{frameRate:15},audio:false});
   const synchronization=await syncClocks();
   const mime=['video/webm;codecs=vp8','video/webm'].find(t=>MediaRecorder.isTypeSupported(t));
   if(!mime)throw Error('เบราว์เซอร์นี้ไม่รองรับ WebM');
   const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:2000000});
   rec.current=recorder;let capture,sequence=0,pending=0,failed=false;
   let chain=Promise.resolve();
   recorder.onstart=()=>{
    chain=api('/sessions/'+sid+'/video/start',{browser_started_ms:performance.now(),browser_time_origin_ms:performance.timeOrigin,synchronization,settings:stream.getVideoTracks()[0].getSettings(),mime_type:mime}).then(v=>{capture=v.capture_id});
    chain.catch(e=>{failed=true;setError(e.message);stop()});setState('recording');
   };
   recorder.ondataavailable=e=>{
    if(!e.data.size)return;
    pending+=e.data.size;
    if(pending>32*1024*1024){failed=true;setError('ส่งวิดีโอไม่ทัน ระบบหยุดคลิปเพื่อป้องกันข้อมูลสูญหาย');stop()}
    chain=chain.then(async()=>{
     const response=await fetch('/api/sessions/'+sid+'/video/'+capture+'/'+sequence,{method:'PUT',headers:{'Authorization':'Bearer '+accessToken(),'Content-Type':'application/octet-stream'},body:e.data});
     if(!response.ok){let info;try{info=await response.json()}catch{}throw Error(info?.detail||'เขียนวิดีโอไม่สำเร็จ')}
     sequence++;pending-=e.data.size;
    });
    chain.catch(e=>{failed=true;setError(e.message);stop()});
   };
   recorder.onerror=()=>{failed=true;setError('MediaRecorder พบข้อผิดพลาด');stop()};
   recorder.onstop=async()=>{
    const ended=performance.now();stream.getTracks().forEach(t=>t.stop());setState('saving');
    try{await chain}catch(e){failed=true;setError(e.message)}
    try{
     if(capture){const result=await api('/sessions/'+sid+'/video/'+capture+'/finish',{complete:!failed,browser_ended_ms:ended,browser_time_origin_ms:performance.timeOrigin});setState(result.status==='completed'?'saved':'incomplete')}
     else setState('incomplete');
    }catch(e){setError(e.message);setState('incomplete')}
    rec.current=null;
   };
   stream.getVideoTracks()[0].onended=stop;
   recorder.start(1000);
  }catch(e){stream?.getTracks().forEach(t=>t.stop());setError(e.message);setState('idle')}
 }
 return <section className="panel padded"><h2>วิดีโอหน้าจอ (เลือกใช้)</h2><p>เลือกจอหรือหน้าต่าง Figma ของผู้เข้าร่วม ไม่มีเสียงและไม่มี gaze overlay วิดีโอจะเก็บในเครื่องและรวมใน Export</p><button className="secondary" disabled={!['instructions','recording'].includes(session?.state)||!session?.consent||['starting','saving','recording'].includes(state)} onClick={start}>เริ่มอัดหน้าจอ</button> <button className="secondary" disabled={state!=='recording'} onClick={stop}>หยุดและบันทึกคลิป</button><p role="status">{({idle:'ยังไม่อัด',starting:'กำลังเตรียม',recording:'● กำลังอัดหน้าจอ',saving:'กำลังเขียนไฟล์ กรุณารอ',saved:'บันทึกคลิปแล้ว · รวมใน Export',incomplete:'คลิปไม่สมบูรณ์ ตรวจข้อผิดพลาดก่อนเก็บจริง'})[state]}</p>{error&&<p role="alert">{error}</p>}</section>
}
