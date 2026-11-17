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
 await page.getByRole('button',{name:'ยืนยันคำตอบและจบรอบ',exact:true}).waitFor();
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
