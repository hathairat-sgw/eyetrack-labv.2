import React,{useEffect,useRef,useState} from 'react';
export default function QuestionnaireForm({definition,onSubmit,button='ส่งแบบสอบถาม',disabled=false,initialDraft,onSaveDraft}){
 const [answers,setAnswers]=useState(initialDraft?.answers||{}),[page,setPage]=useState(0),[saving,setSaving]=useState(''),[error,setError]=useState(''),[sending,setSending]=useState(false),[done,setDone]=useState(false);
 const revision=useRef(initialDraft?.revision||0),queue=useRef(Promise.resolve()),latest=useRef(answers),dirty=useRef(false),locked=useRef(false);
 const pages=[];
 const visible=q=>!q.show_if||answers[q.show_if.question_id]===q.show_if.equals;
 for(const q of definition.questions.filter(visible)){let group=pages.at(-1);if(!group||group.section!==q.section||(!q.section&&group.questions.length===5)){group={section:q.section||'',questions:[]};pages.push(group)}group.questions.push(q)}
 if(!pages.length)pages.push({section:'',questions:[]});
 const current=pages[Math.min(page,pages.length-1)];
 const save=()=>{if(!onSaveDraft)return Promise.resolve();const snapshot=structuredClone(latest.current);queue.current=queue.current.catch(()=>{}).then(async()=>{setSaving('กำลังบันทึกแบบร่าง…');try{const d=await onSaveDraft(snapshot,revision.current);revision.current=d.revision;setSaving('บันทึกแบบร่างแล้ว');setError('')}catch(e){setSaving('ยังไม่บันทึก');setError(e.message);throw e}});return queue.current};
 useEffect(()=>{if(!dirty.current||locked.current)return;const timer=setTimeout(()=>save().catch(()=>{}),700);return()=>clearTimeout(timer)},[answers]);
 const change=(id,value)=>{const next={...latest.current,[id]:value};latest.current=next;dirty.current=true;setAnswers(next)};
 const valid=q=>{const v=latest.current[q.id];return !q.required||(Array.isArray(v)?v.length>0:typeof v==='number'?Number.isFinite(v):typeof v==='string'&&v.trim().length>0)};
 async function submit(e){e.preventDefault();if(locked.current)return;setError('');if(current.questions.some(q=>!valid(q))){setError('กรุณาตอบคำถามที่จำเป็นให้ครบ');return}
 if(page<pages.length-1){setPage(page+1);return}
 const bad=pages.findIndex(g=>g.questions.some(q=>!valid(q)));if(bad>=0){setPage(bad);setError('กรุณาตอบคำถามที่จำเป็นให้ครบ');return}
 locked.current=true;setSending(true);try{await save();await onSubmit(Object.fromEntries(Object.entries(latest.current).filter(([id])=>definition.questions.some(q=>q.id===id&&visible(q)))));setDone(true)}catch(e){setError(e.message)}finally{locked.current=false;setSending(false)}
 }
 if(done)return <div className="success-box" role="status">{onSaveDraft?'บันทึกแบบสอบถามสำเร็จแล้ว':'ตรวจคำตอบครบแล้ว (โหมดตัวอย่าง ไม่บันทึก)'}</div>;
 return <form onSubmit={submit}><div className="spread"><strong>ส่วน {page+1} / {pages.length}</strong><span role="status">{saving}</span></div><progress value={page+1} max={pages.length} style={{width:'100%'}}/>{current.section&&<h2>{current.section}</h2>}
 {definition.scale_labels?.length>0&&current.questions.some(q=>q.type==='likert')&&<div className="notice"><div>{definition.scale_labels.map(label=><p key={label}>{label}</p>)}</div></div>}
 {error&&<div className="error" role="alert">{error}</div>}
 {current.questions.map(q=><fieldset key={q.id} className="question" disabled={disabled||sending}><legend>{q.label} {q.required&&<em>*</em>}</legend>
 {q.type==='single'&&q.options.map(o=><label className="choice" key={o}><input type="radio" name={q.id} required={q.required} checked={answers[q.id]===o} onChange={()=>change(q.id,o)}/>{o}</label>)}
 {q.type==='multiple'&&q.options.map(o=><label className="choice" key={o}><input type="checkbox" checked={(answers[q.id]||[]).includes(o)} onChange={e=>change(q.id,e.target.checked?[...(answers[q.id]||[]),o]:(answers[q.id]||[]).filter(v=>v!==o))}/>{o}</label>)}
 {q.type==='likert'&&<div className="likert">{[5,4,3,2,1].map(n=><label key={n}><input type="radio" name={q.id} required={q.required} checked={answers[q.id]===n} onChange={()=>change(q.id,n)}/><span>{n}</span></label>)}</div>}
 {['short','number'].includes(q.type)&&<input aria-label={q.label} type={q.type==='number'?'number':'text'} min={q.type==='number'?0:undefined} max={q.type==='number'?120:undefined} step={q.type==='number'?1:undefined} required={q.required} maxLength={1000} value={answers[q.id]??''} onChange={e=>change(q.id,q.type==='number'&&e.target.value!==''?Number(e.target.value):e.target.value)}/>}
 {q.type==='long'&&<textarea aria-label={q.label} rows={4} required={q.required} maxLength={10000} value={answers[q.id]||''} onChange={e=>change(q.id,e.target.value)}/>}
 </fieldset>)}
 <div className="button-row">{page>0&&<button type="button" className="secondary" disabled={sending} onClick={()=>setPage(page-1)}>ย้อนกลับ</button>}{onSaveDraft&&<button type="button" className="secondary" disabled={disabled||sending} onClick={()=>save().catch(()=>{})}>บันทึกแบบร่าง</button>}<button className="primary" disabled={disabled||sending}>{sending?'กำลังส่ง…':page<pages.length-1?'ถัดไป':button}</button></div>{onSaveDraft&&<p className="muted">รอข้อความ “บันทึกแบบร่างแล้ว” ก่อนปิดหรือโหลดหน้าใหม่</p>}</form>
}
