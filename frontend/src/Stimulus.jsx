import React,{useEffect,useRef,useState} from 'react';
import {api,viewport} from './api';
import './stimulus.css';
import LebPreview from './LebPreview';

// Deliberately separate engineering fixture. No claims of Figma fidelity.
export default function Stimulus({session,onFinish,onError,preview=false}){
 const [query,setQuery]=useState(''),[view,setView]=useState('courses'),[reached,setReached]=useState(false),[busy,setBusy]=useState(false);
 const host=useRef(null),pending=useRef([]),chain=useRef(Promise.resolve()),failed=useRef(false);
 const trial=session?.trials.at(-1);
 const isLeb=session?.tasks[session.task_index]?.route==='/stimuli/leb-status-search';
 const flush=()=>{
   chain.current=chain.current.then(async()=>{
     if(!pending.current.length||preview||failed.current)return;
     const batch=pending.current.splice(0,500);
     try { const result=await api('/sessions/'+session.session_id+'/events',{events:batch}); if(result.target_reached)setReached(true);}
     catch(e){failed.current=true;onError?.('บันทึกเหตุการณ์ไม่สำเร็จ: '+e.message);try{await api('/sessions/'+session.session_id+'/stop',{})}catch{}throw e}
   });
   return chain.current;
 };
 useEffect(()=>{
   if(preview)return;
   const element=host.current;
   const add=(type,event={})=>{
     const target=event.target?.closest?.('[data-track-id]');
     pending.current.push({event_id:crypto.randomUUID(),trial_id:trial.trial_id,event_type:type,timestamp:performance.now(),
       client_x:event.clientX??null,client_y:event.clientY??null,screen_x:event.screenX??null,screen_y:event.screenY??null,
       scroll_x:scrollX,scroll_y:scrollY,page_url:location.origin+(isLeb?'/stimuli/leb-status-search':'/stimuli/demo')+'?view='+view,
       target_element_id:target?.dataset.trackId||event.target?.closest?.('button')?.textContent?.trim().slice(0,100)||'',viewport:viewport()});
   };
   const click=e=>add('click',e);let last=0;
   const scroll=()=>{if(performance.now()-last>100){last=performance.now();add('scroll')}};
   const resize=()=>{add("viewport");api("/sessions/"+session.session_id+"/stop",{}).catch(()=>{})};
   const visibility=()=>{if(document.hidden)api("/sessions/"+session.session_id+"/stop",{}).catch(()=>{})};
   element.addEventListener('click',click,true);window.addEventListener('scroll',scroll,true);window.addEventListener('resize',resize);document.addEventListener('visibilitychange',visibility);
   add('navigation');
   const timer=setInterval(()=>flush().catch(()=>{}),250);
   return()=>{element.removeEventListener('click',click,true);window.removeEventListener('scroll',scroll,true);window.removeEventListener('resize',resize);document.removeEventListener('visibilitychange',visibility);clearInterval(timer);flush().catch(()=>{})};
 },[trial?.trial_id,view,preview]);
 async function finish(){setBusy(true);try{await flush();if(failed.current)return;while(pending.current.length)await flush();await onFinish()}catch(e){onError?.(e.message)}finally{setBusy(false)}}
 if(isLeb)return <div ref={host}><LebPreview experiment onNavigate={setView} onSubmit={finish}/></div>;
 return <div className="demo-stimulus">
   {preview&&<div className="demo-disclaimer">DEMO FIXTURE · ทดสอบการบันทึกเท่านั้น · ไม่ใช่เว็บไซต์ Figma และไม่ใช้เปรียบเทียบ Good / Bad / Mixed</div>}
   <div ref={host} className="demo-site"><header><strong>Learning workspace</strong><span>Engineering test fixture</span></header>
   <nav><button data-track-id="nav-courses" onClick={()=>setView('courses')}>Courses</button><button data-track-id="nav-resources" onClick={()=>setView('resources')}>Resources</button></nav>
   <main><p className="demo-overline">YOUR LEARNING SPACE</p><h1>{view==='courses'?'Course library':view==='detail'?'Research Methods':'Resources'}</h1>
   {view==='courses'?<><label>Search courses<input data-track-id="course-search" placeholder="Search by course name…" value={query} onChange={e=>setQuery(e.target.value)}/></label><div className="demo-courses">{['Research Methods','Interaction Design','Data Visualization'].filter(n=>n.toLowerCase().includes(query.toLowerCase())).map((name,i)=><button key={name} data-track-id={name==='Research Methods'?'course-research':'course-'+i} onClick={()=>setView('detail')}><span>COURSE</span><h2>{name}</h2><p>Open course →</p></button>)}</div></>:<><button data-track-id="back-courses" onClick={()=>setView('courses')}>← All courses</button><h2>Course materials</h2><button className="demo-resource" data-track-id="resource-guide" onClick={()=>setView('guide')}>Study guide <span>Open →</span></button>{view==='guide'&&<article><h2>Study guide</h2><p>This document is a local recording test fixture.</p></article>}</>}
   </main></div>
   {!preview&&<footer className="demo-controls"><span>● ข้อมูลจำลอง · {reached?'พบเป้าหมายแล้ว':'ทำงานตามคำชี้แจง'}</span><button disabled={busy||(!reached&&session.tasks[session.task_index]?.completion!=='manual')} onClick={finish}>เสร็จสิ้นงาน →</button></footer>}
 </div>
}

