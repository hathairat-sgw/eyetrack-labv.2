export const KEY='eyetrack-lab-online-demo-v1';
const now=()=>new Date().toISOString();
const copy=v=>JSON.parse(JSON.stringify(v));
const must=(c,m)=>{if(!c)throw Error(m)};
export function createDemo(registry,questionnaires,storage){
 const read=()=>{const raw=storage.getItem(KEY);return raw?JSON.parse(raw):{version:1,revision:0,sessions:{}}};
 const save=d=>{storage.setItem(KEY,JSON.stringify(d));return d};
 const mutate=(sid,fn)=>{const d=read(),s=d.sessions[sid];must(s,'ไม่พบ Session');fn(s);s.updated_at=now();d.revision++;save(d);return copy(s)};
 const check=(s,state)=>must(s.state===state,'ขั้นตอนนี้ยังไม่พร้อม กรุณาทำตามลำดับ');
 const answer=(s,phase,answers)=>{
  const qs=s.snapshot[phase].questions;const cleaned={};
  must(Object.keys(answers).every(id=>qs.some(q=>q.id===id)),'Unknown question');
  for(const q of qs){
   if(q.show_if&&answers[q.show_if.question_id]!==q.show_if.equals)continue;
   const v=answers[q.id],empty=v==null||v===''||Array.isArray(v)&&!v.length;
   must(!q.required||!empty,'กรุณาตอบ '+q.label);if(empty)continue;
   if(q.type==='likert')must(Number.isInteger(v)&&v>=1&&v<=5,'คะแนนต้องเป็น 1–5');
   else if(q.type==='number')must(Number.isInteger(v)&&v>=0&&v<=120,'อายุต้องอยู่ระหว่าง 0–120');
   else if(q.type==='single')must(q.options.includes(v),'ตัวเลือกไม่ถูกต้อง');
   else if(q.type==='multiple')must(Array.isArray(v)&&new Set(v).size===v.length&&v.every(x=>q.options.includes(x)),'ตัวเลือกไม่ถูกต้อง');
   else must(typeof v==='string'&&v.length<=(q.type==='short'?1000:10000),'ข้อความไม่ถูกต้อง');
   cleaned[q.id]=v;
  }
  s.responses[phase]={version:s.snapshot[phase].version,answers:cleaned,submitted_at:now()};delete s.drafts[phase];s.state=phase==='pre'?'instructions':'completed';if(phase==='post')s.completed_at=now();
 };
 return {
  all:()=>copy(Object.values(read().sessions)),
  get:sid=>copy(read().sessions[sid]||null),
  open(number){must(Number.isInteger(number)&&number>=1&&number<=30,'P001–P030 เท่านั้น');const d=read(),pid='P'+String(number).padStart(3,'0');const old=Object.values(d.sessions).find(s=>s.participant_id===pid);if(old)return copy(old);
   const track=registry.tracks[number-1],sid='D'+globalThis.crypto.randomUUID().replaceAll('-','').slice(0,16);
   const s={participant_id:pid,session_id:sid,mode:'web_demo',simulated:true,state:'information',created_at:now(),track_id:track.track_id,group:track.group,track:copy(track),snapshot:{pre:copy(questionnaires.pre),post:copy(questionnaires.post)},task_index:0,trials:[],clicks:[],gaze:[],responses:{},drafts:{},consent:null,calibration:null,practice_completed:false,practice_attempts:[],limitations:['DEMO_ONLY','NO_TOBII','NO_REAL_GAZE','NATIVE_FIXTURE_NOT_FIGMA_VARIANTS','BROWSER_LOCAL_STORAGE'],clock:{events:'performance.now milliseconds + time_origin_ms; UTC receipt also retained'}};
   d.sessions[sid]=s;d.revision++;save(d);return copy(s);
  },
  act(sid,action,value){return mutate(sid,s=>{
   if(action==='information'){check(s,'information');s.state='consent'}
   else if(action==='consent'){check(s,'consent');must(value===true,'ต้องยินยอมทดลอง Demo');s.consent={accepted_at:now(),scope:'online demo rehearsal only'};s.state='calibration'}
   else if(action==='calibrate'){check(s,'calibration');s.calibration={simulated:true,hardware_verified:false,finished_at:now()};s.state='practice';s.practice_attempts.push({started_at:now(),events:[]})}
   else if(['button','menu','search','status'].includes(action)){check(s,'practice');s.practice_attempts.at(-1).events.push({action,timestamp:now(),source:'native_practice_ui'})}
   else if(action==='practice_complete'){check(s,'practice');const done=new Set(s.practice_attempts.at(-1).events.map(v=>v.action));must(['button','menu','search','status'].every(v=>done.has(v)),'ทำกิจกรรมฝึกให้ครบ');s.practice_completed=true;s.state='pre'}
   else if(action==='pre'||action==='post'){check(s,action);must(s.practice_completed,'Practice is required');if(action==='post')must(s.trials.filter(t=>t.status==='completed').length===4,'ต้องครบ 4 รอบ');answer(s,action,value)}
   else if(action==='start'){check(s,'instructions');must(s.responses.pre&&s.practice_completed&&s.task_index<4,'ยังไม่พร้อม');const r=s.track.rounds[s.task_index];s.trials.push({participant_id:s.participant_id,session_id:sid,track_id:s.track_id,test_id:s.task_index,task_id:'demo-'+s.task_index,trial_id:globalThis.crypto.randomUUID(),condition:r.family,start_time:now(),start_epoch_ms:Date.now(),status:'recording',recording_status:'browser_mouse_only_no_gaze',completion:false,stimulus:'native_engineering_fixture_not_figma'});s.state='recording'}
   else if(action==='finish'){check(s,'recording');const t=s.trials.at(-1);must(s.clicks.some(e=>e.trial_id===t.trial_id&&e.target_element_id==='fixture-submit'&&e.event_type==='click'),'ทำภารกิจและกดส่งในหน้าฝึกก่อน');t.end_time=now();t.duration_ms=Date.now()-t.start_epoch_ms;t.status='completed';t.completion=true;s.task_index++;s.state=s.task_index===4?'post':'instructions'}
   else throw Error('Unknown action');
  })},
  event(sid,event){return mutate(sid,s=>{check(s,'recording');const t=s.trials.at(-1);must(['click','mouse_down','mouse_up'].includes(event.event_type),'Unknown event');must(Number.isFinite(event.x)&&Number.isFinite(event.y),'Invalid event coordinates');s.clicks.push({...event,participant_id:s.participant_id,session_id:sid,track_id:s.track_id,test_id:t.test_id,task_id:t.task_id,trial_id:t.trial_id,timestamp:now(),coordinate_system:'viewport_css_pixels',target_state:'demo_fixture_unverified',event_source:'browser_demo_dom',interaction_category:'prototype_interaction'})})},
  draft(sid,phase,answers,revision){let result;mutate(sid,s=>{check(s,phase);const current=s.drafts[phase];must((current?.revision||0)===revision,'แบบร่างถูกแก้จากอีกหน้าต่าง กรุณาโหลดใหม่');result={answers,revision:revision+1};s.drafts[phase]=result});return result},
  clear(){storage.removeItem(KEY)}
 };
}
