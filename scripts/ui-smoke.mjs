// Isolated browser test. Synthetic canvas video and MOCK gaze only.
import {chromium} from '../frontend/node_modules/playwright/index.mjs';
import {spawn,execFileSync} from 'node:child_process';
import {mkdtempSync,readFileSync,mkdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import net from 'node:net';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const free=()=>new Promise(resolve=>{const server=net.createServer();server.listen(0,'127.0.0.1',()=>{const port=server.address().port;server.close(()=>resolve(port))})});
const backend=await free(),frontend=await free(),data=mkdtempSync(path.join(tmpdir(),'eyetrack-ui-'));
const env={...process.env,PYTHONUTF8:'1',PYTHONPATH:root,EYETRACK_DATA_DIR:data,EYETRACK_RESEARCHER_PASSWORD:'isolated-ui-test',EYETRACK_BACKEND_PORT:String(backend),EYETRACK_FRONTEND_PORT:String(frontend)};
const python=path.join(root,'.venv-hardware','Scripts','python.exe');
const fixture=`from pathlib import Path
from backend.engine import Engine
from backend.external import External
from backend.models import CalibrationPoint
import os,json
p=Path(os.environ['EYETRACK_DATA_DIR']);e=Engine(p,p/'configuration.json');x=External(e)
for v in x.prototypes()['variants']:x.update(v['name'],v['url'],'verified')
s=x.quick_start('T01');sid=s['session_id'];e.attach(sid,'fixture');e.step(sid,'information');e.step(sid,'consent');e.calibration_start(sid)
for i in range(5):e.calibration_point(sid,CalibrationPoint(index=i,viewport={'fullscreen':True},presented_at=i))
from backend.practice import practice_action
for action in ('button','menu','search','status','complete'):practice_action(e,sid,action)
e.answers(sid,'pre',{'department':'UI TEST ONLY','age':22,'gender':'หญิง','year':'ปี 4','leb2_frequency':'บางครั้ง'})
e.metadata(sid,{'viewport':{'screen_width':1280,'screen_height':800},'synchronization':[]})
print(json.dumps({'sid':sid,'folder':str(e.storage.session_path(e.get(sid)))}))`;
const prepared=JSON.parse(execFileSync(python,['-c',fixture],{cwd:root,env,encoding:'utf8'}));
let logs='',browser;
const child=spawn(process.execPath,['scripts/run.mjs','--no-open'],{cwd:root,env,windowsHide:true,stdio:['pipe','pipe','pipe']});
child.stdout.on('data',v=>logs+=v);child.stderr.on('data',v=>logs+=v);
try{
 const until=Date.now()+35000;while(!logs.includes('READY ')&&Date.now()<until){if(child.exitCode!==null)throw Error(logs);await new Promise(r=>setTimeout(r,200))}
 assert.ok(logs.includes('READY '),'launcher did not become ready');
 browser=await chromium.launch({channel:'chrome',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:'+frontend+'/researcher/external');
 await page.getByLabel('รหัสนักวิจัย').fill('isolated-ui-test');await page.getByRole('button',{name:'เข้าสู่ระบบ',exact:true}).click();
 await page.getByLabel('รูปแบบการบันทึก').selectOption('hardware');
 await page.getByRole('button',{name:'ตรวจอุปกรณ์อีกครั้ง'}).waitFor();
 mkdirSync(path.join(root,'work'),{recursive:true});await page.screenshot({path:path.join(root,'work','ui-hardware-mode.png'),fullPage:true});
 await page.getByLabel('รูปแบบการบันทึก').selectOption('mock');
 // Full participant UI path in a separate TEST-ONLY browser context.
 const adminToken=await page.evaluate(()=>sessionStorage.getItem('researcher-access'));
 const created=await context.request.post('http://127.0.0.1:'+frontend+'/api/external/quick-start',{headers:{Authorization:'Bearer '+adminToken},data:{track_id:'T02',mode:'mock'}});
 assert.equal(created.status(),200);const flow=await created.json();
 const participantContext=await browser.newContext({viewport:{width:1440,height:1000}});
 const participantPage=await participantContext.newPage();participantPage.on('pageerror',e=>errors.push(e.message));
 await participantPage.goto('http://127.0.0.1:'+frontend+flow.participant_path);
 await participantPage.getByRole('button',{name:/อ่านและดำเนินการต่อ/}).click();
 await participantPage.getByRole('checkbox').check();
 await participantPage.getByRole('button',{name:/ยืนยันความยินยอม/}).click();
 await participantPage.getByRole('button',{name:'จำลอง Calibration ในหน้าต่าง (Mock เท่านั้น)'}).click();
 await participantPage.getByRole('heading',{name:'ฝึกใช้งานก่อนทดลอง'}).waitFor({timeout:20000});
 assert.equal(await participantPage.getByRole('button',{name:/จบการฝึก/}).isDisabled(),true);
 await participantPage.getByRole('button',{name:/1. ลองคลิกปุ่ม/}).click();
 await participantPage.getByRole('button',{name:/2. เปิดเมนู/}).click();
 await participantPage.locator('input[required]').fill('ตัวอย่าง');
 await participantPage.getByRole('button',{name:/^ค้นหา/}).click();
 await participantPage.getByRole('button',{name:/4. ฉันอ่านสถานะแล้ว/}).click();
 await participantPage.getByRole('button',{name:/จบการฝึก/}).click();
 async function completeQuestionnaire(definition){
  for(let count=0;count<20;count++){
   const fields=participantPage.locator('fieldset');await fields.first().waitFor();
   for(let i=0;i<await fields.count();i++){
    const field=fields.nth(i);
    if(await field.locator('input[type=radio]').count())await field.locator('input[type=radio]').first().check();
    else if(await field.locator('input[type=number]').count())await field.locator('input[type=number]').fill('22');
    else if(await field.locator('input[type=text]').count())await field.locator('input[type=text]').fill('UI TEST ONLY');
    else if(await field.locator('textarea').count())await field.locator('textarea').fill('UI TEST ONLY');
   }
   const next=participantPage.getByRole('button',{name:'ถัดไป',exact:true});
   if(await next.count())await next.click();
   else {await participantPage.getByRole('button',{name:'ส่งแบบสอบถาม',exact:true}).click();break}
  }
 }
 await completeQuestionnaire(flow.snapshot.pre);
 await participantPage.getByRole('heading',{name:'เปิดหน้าทดลอง Figma'}).waitFor();
 await page.goto('http://127.0.0.1:'+frontend+'/researcher/external/'+flow.session_id);
 for(let round=0;round<4;round++){
  await page.getByRole('heading',{name:new RegExp('^Test '+round+' ·')}).waitFor();
  console.log('UI test round '+round);
  for(const label of ['ยืนยันหน้าตั้งต้น','ยืนยันจอที่ใช้','เปิด fullscreen แล้ว','ปิด hotspot hints แล้ว'])await page.getByLabel(label,{exact:true}).check();
  await page.getByRole('button',{name:'เริ่มบันทึกรอบ',exact:true}).click();
  await page.getByRole('button',{name:'จบรอบ / หยุดบันทึก',exact:true}).waitFor({state:'visible'});
  await page.waitForTimeout(100);
  await page.getByRole('button',{name:'จบรอบ / หยุดบันทึก',exact:true}).click();
  await page.getByLabel('Late',{exact:true}).fill('0');await page.getByLabel('Quiz ค้าง',{exact:true}).fill('0');
  await page.getByRole('button',{name:/บันทึกคำตอบ →/}).click();
 }
 await participantPage.getByRole('heading',{name:'แบบสอบถามหลังการทดลอง'}).waitFor();
 await completeQuestionnaire(flow.snapshot.post);
 await participantPage.getByRole('button',{name:'จบการทดลอง',exact:true}).click();
 await participantPage.getByRole('heading',{name:'การทดลองเสร็จสมบูรณ์'}).waitFor();
 await participantPage.reload();await participantPage.getByRole('heading',{name:'การทดลองเสร็จสมบูรณ์'}).waitFor();
 const completedResponse=await context.request.get('http://127.0.0.1:'+frontend+'/api/sessions/'+flow.session_id,{headers:{Authorization:'Bearer '+adminToken}});
 const completed=await completedResponse.json();assert.equal(completed.state,'completed');assert.equal(completed.trials.length,4);assert.equal(completed.practice_completed,true);
 console.log('Full UI flow passed: consent, mock calibration, practice, pre-test, four rounds, post-test, completion, refresh');
 await participantContext.close();
 await page.goto('http://127.0.0.1:'+frontend+'/researcher/external/'+prepared.sid);
 await page.getByRole('heading',{name:'วิดีโอหน้าจอ (เลือกใช้)'}).waitFor();
 // Deliberate test double for the screen picker: encode a canvas, never the user's display.
 await page.evaluate(()=>{navigator.mediaDevices.getDisplayMedia=async()=>{const c=document.createElement('canvas');c.width=640;c.height=360;const ctx=c.getContext('2d');let i=0;const timer=setInterval(()=>{ctx.fillStyle='#eee8ff';ctx.fillRect(0,0,640,360);ctx.fillStyle='#262040';ctx.font='30px sans-serif';ctx.fillText('SYNTHETIC VIDEO '+i++,30,100)},66);const s=c.captureStream(15);s.getVideoTracks()[0].addEventListener('ended',()=>clearInterval(timer));return s}});
 await page.getByRole('button',{name:'เริ่มอัดหน้าจอ',exact:true}).click();
 await page.getByText('● กำลังอัดหน้าจอ',{exact:true}).waitFor();
 for(const label of ['ยืนยันหน้าตั้งต้น','ยืนยันจอที่ใช้','เปิด fullscreen แล้ว','ปิด hotspot hints แล้ว'])await page.getByLabel(label,{exact:true}).check();
 await page.getByRole('button',{name:'เริ่มบันทึกรอบ',exact:true}).click();
 await page.getByText('● มีข้อมูลเข้า',{exact:true}).waitFor();
 await page.waitForTimeout(2400);
 await page.getByRole('button',{name:'หยุดและบันทึกคลิป',exact:true}).click();
 await page.getByText('บันทึกคลิปแล้ว · รวมใน Export',{exact:true}).waitFor({timeout:20000});
 await page.getByRole('button',{name:'จบรอบ / หยุดบันทึก',exact:true}).click();
 await page.getByRole('button',{name:'บันทึกคำตอบ → ไปรอบ 2',exact:true}).waitFor();
 const session=JSON.parse(readFileSync(path.join(prepared.folder,'session.json'),'utf8'));
 assert.ok(session.trials[0].gaze_count>0);assert.equal(session.mode,'mock');assert.equal(session.videos[0].status,'completed');assert.ok(session.videos[0].bytes>1000);
 const video=readFileSync(path.join(prepared.folder,session.videos[0].filename));assert.equal(video.subarray(0,4).toString('hex'),'1a45dfa3');
 const dimensions=await page.evaluate(base64=>new Promise((resolve,reject)=>{const v=document.createElement('video');v.onloadeddata=()=>resolve([v.videoWidth,v.videoHeight]);v.onerror=()=>reject(Error('Cannot decode WebM'));v.src='data:video/webm;base64,'+base64;v.load()}),video.toString('base64'));
 assert.deepEqual(dimensions,[640,360]);assert.deepEqual(errors,[]);
 await page.screenshot({path:path.join(root,'work','ui-stream-video.png'),fullPage:true});
 console.log(JSON.stringify({passed:true,mode:'mock',synthetic_video:true,samples:session.trials[0].gaze_count,video_bytes:session.videos[0].bytes,decoded_dimensions:dimensions,data_directory:data}));
}finally{
 if(browser)await browser.close();
 child.stdin.end('stop\n');
 const until=Date.now()+12000;while(child.exitCode===null&&Date.now()<until)await new Promise(r=>setTimeout(r,100));
 if(child.exitCode===null)child.kill();
}
