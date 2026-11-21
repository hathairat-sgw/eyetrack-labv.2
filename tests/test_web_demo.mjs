import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createDemo} from '../frontend/web-demo/engine.mjs';
import {dataset,exportDemo} from '../frontend/web-demo/export.mjs';
const registry=JSON.parse(readFileSync(new URL('../config/tracks.json',import.meta.url)));
const questions=JSON.parse(readFileSync(new URL('../config/questionnaires-irb.json',import.meta.url)));
const store=()=>{const m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)}};
const answers=phase=>Object.fromEntries(questions[phase].questions.filter(q=>q.required).map(q=>[q.id,q.type==='likert'?4:q.type==='number'?22:q.type==='single'?q.options[0]:q.type==='multiple'?[q.options[0]]:'DEMO ONLY']));
function ready(e,n){let s=e.open(n),sid=s.session_id;e.act(sid,'information');e.act(sid,'consent',true);e.act(sid,'calibrate');for(const action of ['button','menu','search','status','practice_complete'])e.act(sid,action);e.act(sid,'pre',answers('pre'));return sid}
test('guards prevent skipping consent, practice, questionnaires and task submission',()=>{
 const e=createDemo(registry,questions,store()),s=e.open(1),sid=s.session_id;
 assert.throws(()=>e.act(sid,'start'));e.act(sid,'information');assert.throws(()=>e.act(sid,'consent',false));e.act(sid,'consent',true);e.act(sid,'calibrate');assert.throws(()=>e.act(sid,'practice_complete'));
 for(const action of ['button','menu','search','status','practice_complete'])e.act(sid,action);
 assert.throws(()=>e.act(sid,'pre',{}));e.act(sid,'pre',answers('pre'));e.act(sid,'start');assert.throws(()=>e.act(sid,'finish'));
});
test('all thirty browser-local participants finish four rounds without fabricated gaze',()=>{
 const storage=store(),e=createDemo(registry,questions,storage);
 for(let n=1;n<=30;n++){
  const sid=ready(e,n);
  for(let r=0;r<4;r++){e.act(sid,'start');e.event(sid,{event_type:'click',x:120,y:80,target_element_id:'fixture-submit',target_component:'Button',browser_timestamp_ms:performance.now(),time_origin_ms:performance.timeOrigin});e.act(sid,'finish')}
  const s=e.act(sid,'post',answers('post'));assert.equal(s.state,'completed');assert.equal(s.gaze.length,0);assert.equal(s.trials.length,4);assert.equal(e.open(n).session_id,sid);
  const files=dataset(s);assert.equal(Object.keys(files).length,9);assert.equal(files['gaze.csv'].trim().split('\n').length,1);assert.equal(JSON.parse(files['quality_report.json']).gaze_sample_count,0);
 }
 assert.equal(createDemo(registry,questions,storage).all().length,30);
 const zip=exportDemo(e.all());assert.equal(new DataView(zip.buffer).getUint32(0,true),0x04034b50);assert.equal(new DataView(zip.buffer).getUint16(zip.length-12,true),270);
});
test('draft revision survives reload and rejects stale writers',()=>{
 const storage=store(),e=createDemo(registry,questions,storage);let s=e.open(1);e.act(s.session_id,'information');e.act(s.session_id,'consent',true);e.act(s.session_id,'calibrate');for(const a of ['button','menu','search','status','practice_complete'])e.act(s.session_id,a);
 e.draft(s.session_id,'pre',{department:'DEMO'},0);assert.equal(createDemo(registry,questions,storage).get(s.session_id).drafts.pre.revision,1);assert.throws(()=>e.draft(s.session_id,'pre',{},0));
});
