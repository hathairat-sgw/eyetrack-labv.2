const enc=new TextEncoder();
const csv=(fields,rows)=>'\uFEFF'+fields.join(',')+'\r\n'+rows.map(r=>fields.map(f=>'"'+String(r[f]??'').replaceAll('"','""')+'"').join(',')).join('\r\n');
const json=v=>JSON.stringify(v,null,2);
export function dataset(s){
 const id={participant_id:s.participant_id,session_id:s.session_id};
 const questionnaire=phase=>Object.entries(s.responses[phase]?.answers||{}).map(([question_id,response])=>({...id,question_id,response:JSON.stringify(response),timestamp:s.responses[phase].submitted_at,questionnaire_version:s.responses[phase].version}));
 const missing=s.track.rounds.filter(r=>!s.trials.some(t=>t.test_id===r.test_index&&t.status==='completed')).map(r=>r.test_index);
 return {
 'participants.csv':csv(['participant_id','session_id','track_id','group','mode','state','created_at','completed_at'],[{...s}]),
 'pre_test.csv':csv(['participant_id','session_id','question_id','response','timestamp','questionnaire_version'],questionnaire('pre')),
 'post_test.csv':csv(['participant_id','session_id','question_id','response','timestamp','questionnaire_version'],questionnaire('post')),
 'clicks.csv':csv(['participant_id','session_id','track_id','test_id','task_id','trial_id','timestamp','browser_timestamp_ms','time_origin_ms','event_type','x','y','coordinate_system','target_element_id','target_component','target_state','event_source','interaction_category','scroll_x','scroll_y','viewport_width','viewport_height'],s.clicks),
 'gaze.csv':csv(['participant_id','session_id','track_id','test_id','task_id','timestamp','gaze_x','gaze_y','coordinate_system'],[]),
 'trials.csv':csv(['participant_id','session_id','track_id','test_id','condition','task_id','trial_id','start_time','end_time','duration_ms','status','completion','recording_status','stimulus'],s.trials),
 'session.json':json(s),
 'quality_report.json':json({...id,mode:'web_demo',simulated:true,calibration_verified:false,gaze_sample_count:0,valid_gaze_percentage:null,click_count:s.clicks.filter(e=>e.event_type==='click').length,missing_tasks:missing,questionnaire_completion:{pre:!!s.responses.pre,post:!!s.responses.post},overall_quality_warnings:s.limitations,status:'DEMO_NOT_RESEARCH'}),
 'README.txt':`EyeTrack Lab ONLINE DEMO ONLY. No Tobii connection; no gaze samples generated. Native playground is not a validated reproduction of Figma conditions. All data stays in this browser until downloaded; never combine with real research datasets. Files join on participant_id/session_id; clicks/trials also share trial_id/task_id. Mouse x/y are viewport CSS pixels; scroll and viewport are captured. browser_timestamp_ms is performance.now and time_origin_ms is performance.timeOrigin; timestamp is UTC ISO-8601. Blank values mean missing/unavailable. Questionnaire response is JSON. Track and questionnaire snapshots are in session.json. Sessions can be exported incomplete. Research software and hardware setup: https://github.com/hathairat-sgw/eyetrack-lab .`
 };
}
function crc32(a){let crc=0xffffffff;for(const b of a){crc^=b;for(let k=0;k<8;k++)crc=crc>>>1^((crc&1)?0xedb88320:0)}return (crc^0xffffffff)>>>0}
export function zipFiles(files){
 const pieces=[],central=[];let offset=0,total=0;
 for(const [name,content] of Object.entries(files)){
  const n=enc.encode(name),data=enc.encode(content),crc=crc32(data),header=new Uint8Array(30+n.length),h=new DataView(header.buffer);
  h.setUint32(0,0x04034b50,true);h.setUint16(4,20,true);h.setUint16(6,0x800,true);h.setUint32(14,crc,true);h.setUint32(18,data.length,true);h.setUint32(22,data.length,true);h.setUint16(26,n.length,true);header.set(n,30);
  const directory=new Uint8Array(46+n.length),d=new DataView(directory.buffer);d.setUint32(0,0x02014b50,true);d.setUint16(4,20,true);d.setUint16(6,20,true);d.setUint16(8,0x800,true);d.setUint32(16,crc,true);d.setUint32(20,data.length,true);d.setUint32(24,data.length,true);d.setUint16(28,n.length,true);d.setUint32(42,offset,true);directory.set(n,46);
  pieces.push(header,data);central.push(directory);offset+=header.length+data.length;total+=directory.length;
 }
 const end=new Uint8Array(22),e=new DataView(end.buffer);e.setUint32(0,0x06054b50,true);e.setUint16(8,central.length,true);e.setUint16(10,central.length,true);e.setUint32(12,total,true);e.setUint32(16,offset,true);
 const out=new Uint8Array(offset+total+22);let at=0;for(const p of [...pieces,...central,end]){out.set(p,at);at+=p.length}return out;
}
export function exportDemo(sessions){const files={};for(const s of sessions)for(const [name,content] of Object.entries(dataset(s)))files[`web_demo/${s.participant_id}/${s.session_id}/${name}`]=content;return zipFiles(files)}
