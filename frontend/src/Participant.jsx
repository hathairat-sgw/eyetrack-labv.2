import React,{useEffect,useRef,useState} from 'react';
import {useParams} from 'react-router-dom';
import {ArrowRight,CheckCircle2,Maximize,Square,Eye} from 'lucide-react';
import {api,syncClocks,viewport} from './api';
import {useSession} from './hooks';
import {Brand,Badge,ErrorBox,Loading,QuestionForm} from './components';
import Stimulus from './Stimulus';
import LebPreview from './LebPreview';

const calibrationPoints=[[.1,.1],[.9,.1],[.5,.5],[.1,.9],[.9,.9]],validationPoints=[[.2,.2],[.8,.2],[.2,.8],[.8,.8],[.5,.5]];
export default function Participant(){
 const {sid}=useParams(), {session,setSession,error,setError,connected}=useSession(sid,true);
 const [confirmation,setConfirmation]=useState('');
 const [busy,setBusy]=useState(false),[consent,setConsent]=useState(false),[point,setPoint]=useState(null),[syncReady,setSyncReady]=useState(false);
 const running=useRef(false);
 const [showConsole,setShowConsole]=useState(false),[checking,setChecking]=useState(false);
 const points=checking?validationPoints:calibrationPoints;
 useEffect(()=>{const stop=e=>{if(e.key==='Escape'&&session?.state==='recording')api('/sessions/'+sid+'/stop',{}).then(setSession).catch(e=>setError(e.message))};window.addEventListener('keydown',stop);return()=>window.removeEventListener('keydown',stop)},[sid,session?.state]);
 const act=async(path,body={})=>{setBusy(true);setError('');try{const s=await api('/sessions/'+sid+path,body);setSession(s);return s}catch(e){setError(e.message);throw e}finally{setBusy(false)}};
 useEffect(()=>{
   if(!session?.consent||syncReady)return;
   let alive=true;
   syncClocks().then(synchronization=>api('/sessions/'+sid+'/metadata',{viewport:viewport(),synchronization})).then(()=>alive&&setSyncReady(true)).catch(e=>alive&&setError(e.message));
   return()=>{alive=false};
 },[sid,!!session?.consent,syncReady]);
 useEffect(()=>()=>{running.current=false},[]);
 useEffect(()=>{
  const guard=()=>{if(running.current&&!document.fullscreenElement){running.current=false;setPoint(null);api("/sessions/"+sid+"/stop",{}).then(setSession).catch(e=>setError(e.message))}};
  document.addEventListener("fullscreenchange",guard);return()=>document.removeEventListener("fullscreenchange",guard);
 },[sid]);
 async function calibrate(windowed=false,validation=false){
   setChecking(validation);
   if(running.current)return;
   running.current=true;setBusy(true);setError('');
   try{
     if(!windowed&&!document.fullscreenElement)await document.documentElement.requestFullscreen();
     const stage=validation?'validation':'calibration';
     await api('/sessions/'+sid+'/'+stage+'/start',{});
     for(let i=0;i<5&&running.current;i++){
       setPoint(i);
       await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
       const presented_at=performance.now();
       await new Promise(resolve=>setTimeout(resolve,1200));
       if(!running.current)break;
       const s=await api('/sessions/'+sid+'/'+stage+'/point',{index:i,presented_at,viewport:viewport()});
       setSession(s);
       if(s.state==='calibration')break;
     }
   }catch(e){setError(e.message);try{setSession(await api('/sessions/'+sid+'/stop',{}))}catch{}}
   finally{running.current=false;setPoint(null);setBusy(false)}
 }
 async function startTrial(){
   setBusy(true);setError("");
   try{const synchronization=await syncClocks();await api("/sessions/"+sid+"/metadata",{viewport:viewport(),synchronization});setSession(await api("/sessions/"+sid+"/trials/start",{}))}
   catch(e){setError(e.message)}finally{setBusy(false)}
 }
 async function withdraw(){
   if(!window.confirm('ต้องการถอนตัวและหยุดการบันทึกหรือไม่? ข้อมูลเดิมจะเก็บไว้ตามนโยบายที่แสดง'))return;
   running.current=false;setPoint(null);await act('/withdraw').catch(()=>{});
 }
 if(!session)return <><ErrorBox error={error}/><Loading/></>;
 if(session.task_mode!=='figma_external'&&showConsole)return <><div className="participant-card"><p>หยุดบันทึกงานแล้ว · กลับ console ตาม flow ต้นฉบับ</p><button className="primary" onClick={()=>setShowConsole(false)}>ดำเนินการต่อหลังงาน</button></div><LebPreview experiment lockedConsole/></>;
 const state=session.state;
 const progressState=({validation:'calibration',calibrating:'calibration',external_answers:'recording'})[state]||state;
 const stepIndex=(session.workflow_version==='calibration-before-pre-v1'?['information','consent','calibration','pre','instructions','recording','post','thankyou','completed']:['information','consent','pre','calibration','instructions','recording','post','thankyou','completed']).indexOf(progressState);
 return <div className="participant">
 {point!==null?<div className="calibration-screen"><div className="calibration-label">{session.mode==='hardware'?(checking?'ตรวจพิกัด':'Calibration'):'DEMO CALIBRATION'} · มองจุดที่ปรากฏ ({point+1}/5)</div><div className="calibration-target" style={{left:points[point][0]*100+'%',top:points[point][1]*100+'%'}}/><button onClick={withdraw} className="calibration-stop">หยุด / ถอนตัว</button><ErrorBox error={error}/></div>:<>
 {state!=='recording'&&<header className="participant-header"><Brand/><Badge kind="warning">{session.mode==='hardware'?'Tobii · ข้อมูลจริง':'DEMO · ข้อมูลจำลอง'}</Badge></header>}
 {session.task_mode!=='figma_external'&&state==='recording'?<><ErrorBox error={error}/><Stimulus key={session.trials.at(-1).trial_id} session={session} onError={setError} onFinish={async()=>{const leb=session.tasks[session.task_index]?.route==='/stimuli/leb-status-search';await act('/trials/complete');if(leb)setShowConsole(true)}}/></>:
 <main className="participant-content"><div className="step-line">{(session.workflow_version==='calibration-before-pre-v1'?['ข้อมูลและยินยอม','Calibration','แบบสอบถามก่อน','งานทดลอง','แบบสอบถามหลัง']:['ข้อมูลและยินยอม','แบบสอบถามก่อน','Calibration','งานทดลอง','แบบสอบถามหลัง']).map((text,i)=><span key={text} className={stepIndex>=([0,2,3,4,6][i])?'done':''}>{i+1}<small>{text}</small></span>)}</div>
 <div className="participant-card"><ErrorBox error={error}/>{!connected&&<p className="warning-text">กำลังเชื่อมต่อหน้าผู้เข้าร่วม…</p>}
 {state==='information'&&<><p className="eyebrow">WELCOME TO THE STUDY</p><h1>ขอบคุณที่ร่วมการทดลอง</h1><p className="prose">{session.snapshot.protocol.information}</p><div className="soft-panel"><h3>การเก็บและถอนข้อมูล</h3><p>{session.snapshot.protocol.retention}</p></div><button className="primary" disabled={busy||!connected} onClick={()=>act('/step/information').catch(()=>{})}>อ่านและดำเนินการต่อ <ArrowRight size={18}/></button></>}
 {state==='consent'&&<><h1>ความยินยอมเข้าร่วม</h1><p className="prose">{session.snapshot.protocol.consent}</p><label className="choice"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>ฉันได้อ่านและยินยอมเข้าร่วม</label><button className="primary" disabled={!consent||busy||!connected} onClick={()=>act('/step/consent').catch(()=>{})}>ยืนยันความยินยอม <ArrowRight size={18}/></button></>}
 {confirmation&&state!=='post'&&<div className="success-box" role="status">{confirmation}</div>}
 {(state==='pre'||state==='post')&&<><p className="eyebrow">{state==='pre'?'BEFORE THE SESSION':'AFTER THE SESSION'}</p><h1>แบบสอบถาม{state==='pre'?'ก่อน':'หลัง'}การทดลอง</h1><p className="muted">ฉบับ {session.snapshot[state].version} · {session.snapshot[state].source||'แบบสอบถามของ session นี้'}</p>{state==='post'&&session.responses.pre&&<details open><summary>ข้อมูลทั่วไปจาก Pre-test (ไม่ต้องกรอกซ้ำ)</summary>{session.snapshot.pre.questions.map(q=><p key={q.id}><strong>{q.label}:</strong> {String(session.responses.pre.answers[q.id]??'—')}</p>)}</details>}<QuestionForm key={state} initialDraft={session.drafts?.[state]} onSaveDraft={(answers,revision)=>api('/sessions/'+sid+'/drafts/'+state,{answers,revision},'PUT')} definition={session.snapshot[state]} disabled={busy||!connected} onSubmit={async answers=>{await act('/answers/'+state,{answers});setConfirmation('บันทึกแบบสอบถาม'+(state==='pre'?'ก่อน':'หลัง')+'การทดลองสำเร็จแล้ว')}}/></>}
 {(state==='calibration'||state==='calibrating')&&<><div className="round-icon"><Eye size={34}/></div><h1>เตรียมพร้อมก่อนเริ่ม</h1><p>มองตามจุดบนหน้าจอทั้งหมด 5 จุด {session.mode==='mock'?'ขั้นตอนนี้เป็นการจำลอง':'จากนั้นจะตรวจพิกัดอีก 5 จุดก่อนเริ่มงาน'}</p><div className="soft-panel">นั่งในท่าที่สบาย และคงตำแหน่งหน้าจอไว้ตลอดการทดลอง</div><button className="primary" disabled={busy||!connected||!syncReady} onClick={()=>calibrate(false)}><Maximize size={18}/> เริ่ม Calibration เต็มจอ</button>{session.mode==='mock'&&<button className="secondary" disabled={busy||!connected||!syncReady} onClick={()=>calibrate(true)}>จำลอง Calibration ในหน้าต่าง (Mock เท่านั้น)</button>}</>}
 {state==='validation'&&<><h1>ตรวจความตรงของตำแหน่งสายตา</h1><p>มองตามจุดทดสอบ 5 จุด ระบบรับข้อมูลจาก Tobii จริง ทั้งสองตาต้องผ่านเกณฑ์ก่อนเริ่มงาน</p>{session.validation&&<div className="soft-panel"><p>ตรวจแล้ว {session.validation.points.length}/5 จุด · {session.validation.passed?'ผ่าน':'ยังไม่ผ่าน'}</p>{session.validation.points.map((p,i)=><p key={i}>จุด {i+1}: {p.metrics.passed?'ผ่าน':'ไม่ผ่าน'} · ซ้าย {p.metrics.left.mean_error_norm?.toFixed(4)??'ไม่มีข้อมูล'} / ขวา {p.metrics.right.mean_error_norm?.toFixed(4)??'ไม่มีข้อมูล'} · {p.metrics.sample_count} ตัวอย่าง</p>)}</div>}<button className="primary" disabled={busy||!connected} onClick={()=>calibrate(false,true)}>ตรวจพิกัดเต็มจอ</button><button className="secondary" disabled={busy||!connected} onClick={()=>calibrate(false)}>Calibration ใหม่</button></>}
 {session.task_mode==='figma_external'&&['instructions','recording','external_answers'].includes(state)&&<><h1>เปิดหน้าทดลอง Figma</h1><p>รอบที่ {(session.external_task?.test_index??0)+1} จาก 4 · วิชา {session.external_task?.course_id}</p>{session.external_task?.prototype_url&&<a className="primary" href={session.external_task.prototype_url} target="_blank" rel="noopener noreferrer">เปิด Figma สำหรับรอบนี้ ↗</a>}{session.mode==='hardware'&&state==='instructions'&&<button className="secondary" disabled={busy||!connected} onClick={()=>calibrate(false)}>Calibration / ตรวจพิกัดใหม่</button>}<p>รอผู้วิจัยแจ้งเริ่มก่อนทำภารกิจ การเปิดลิงก์ยังไม่เริ่มบันทึก หากต้องการหยุดให้แจ้งผู้วิจัย</p></>}
 {session.task_mode!=='figma_external'&&state==='instructions'&&<><p className="eyebrow">TASK {session.task_index+1} OF {session.tasks.length}</p><h1>{session.tasks[session.task_index]?.name}</h1><p className="prose">{session.tasks[session.task_index]?.instruction}</p><div className="soft-panel">กดเริ่มเมื่อพร้อม ระบบจะเริ่มบันทึกข้อมูลจำลองและการคลิกเฉพาะช่วงทำงาน · กด Escape เพื่อหยุดได้ทุกเมื่อ ไม่มีปุ่มควบคุมลอยทับเว็บไซต์</div><button className="primary" disabled={busy||!connected||!syncReady} onClick={startTrial}>เริ่มงาน <ArrowRight size={18}/></button></>}
 {state==='interrupted'&&<><h1>การทดลองถูกหยุดไว้</h1><p>งานล่าสุดถูกเก็บเป็น incomplete การทำต่อจะ calibration และเริ่ม trial ใหม่โดยไม่เขียนทับข้อมูลเดิม</p><p className="mono">{session.interruption}</p><button className="primary" disabled={busy||!connected} onClick={()=>act('/step/resume').catch(()=>{})}>กลับมาทำต่อ</button></>}
 {state==='thankyou'&&<><CheckCircle2 size={44} className="teal"/><h1>ขอบคุณสำหรับเวลาของคุณ</h1><p>คำตอบถูกบันทึกแล้ว กดจบการทดลองเพื่อปิด session</p><button className="primary" disabled={busy} onClick={()=>act('/step/finish').catch(()=>{})}>จบการทดลอง</button></>}
 {state==='completed'&&<><CheckCircle2 size={48} className="teal"/><h1>การทดลองเสร็จสมบูรณ์</h1><p>คุณสามารถปิดหน้าต่างนี้ได้</p></>}
 {state==='withdrawn'&&<><h1>หยุดการทดลองแล้ว</h1><p>ไม่มีการบันทึกเพิ่มเติม ข้อมูลเดิมถูกเก็บตามนโยบายที่แจ้งไว้</p></>}
 </div><footer className="participant-footer"><small>{session.participant_id} · {session.session_id.slice(0,9)}</small>{!['completed','withdrawn'].includes(state)&&<button className="text-button danger" onClick={withdraw}><Square size={13}/> หยุด / ถอนตัว</button>}</footer></main>}
 </>}
 </div>
}

