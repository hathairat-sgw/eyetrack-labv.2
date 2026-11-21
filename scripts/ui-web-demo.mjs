import {chromium} from '../frontend/node_modules/playwright/index.mjs';
import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
const url=process.argv[2]||'http://127.0.0.1:5180';
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.getByRole('heading',{name:'ผู้ทดลอง Demo',exact:true}).waitFor();assert.equal(await page.locator('.web-person').count(),30);
 await page.getByRole('button',{name:'เริ่ม Demo คนที่ 1',exact:true}).click();await page.getByRole('button',{name:'อ่านและดำเนินการต่อ',exact:true}).click();await page.getByRole('checkbox').check();await page.getByRole('button',{name:'ยืนยัน Demo',exact:true}).click();await page.getByRole('button',{name:'เริ่มจำลอง Calibration 5 จุด',exact:true}).click();
 await page.getByRole('heading',{name:'ฝึกใช้งานก่อนทดลอง'}).waitFor();await page.getByRole('button',{name:/1. ลองคลิกปุ่ม/}).click();await page.getByRole('button',{name:/2. เปิดเมนู/}).click();await page.locator('input[required]').fill('ตัวอย่าง');await page.getByRole('button',{name:/^ค้นหา/}).click();await page.getByRole('button',{name:/4. ฉันอ่านสถานะแล้ว/}).click();await page.getByRole('button',{name:/จบการฝึก/}).click();
 async function answer(){for(let count=0;count<20;count++){const fields=page.locator('fieldset');await fields.first().waitFor();for(let i=0;i<await fields.count();i++){const f=fields.nth(i);if(await f.locator('input[type=radio]').count())await f.locator('input[type=radio]').first().check();else if(await f.locator('input[type=number]').count())await f.locator('input[type=number]').fill('22');else if(await f.locator('input[type=text]').count())await f.locator('input[type=text]').fill('DEMO TEST');else if(await f.locator('textarea').count())await f.locator('textarea').fill('DEMO TEST')}const next=page.getByRole('button',{name:'ถัดไป',exact:true});if(await next.count())await next.click();else{await page.getByRole('button',{name:'ส่งแบบสอบถาม',exact:true}).click();return}}throw Error('Questionnaire exceeded 20 pages')}
 await answer();
 for(let i=0;i<4;i++){await page.getByRole('button',{name:'เริ่มรอบ Demo',exact:true}).click();await page.getByLabel('ค้นหาวิชา',{exact:true}).fill('Demo Lab');await page.locator('#fixture-course').click();await page.locator('#fixture-submit').click();await page.getByRole('button',{name:'จบรอบ Demo',exact:true}).click()}
 await answer();await page.getByRole('heading',{name:'ทดลองครบแล้ว'}).waitFor();const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download Demo Dataset',exact:true}).click();const saved=path.join(mkdtempSync(path.join(tmpdir(),'eyetrack-web-')),'dataset.zip');await (await download).saveAs(saved);assert.equal(readFileSync(saved).subarray(0,4).toString('hex'),'504b0304');
 await page.reload();await page.getByRole('heading',{name:'ผู้ทดลอง Demo',exact:true}).waitFor();await page.locator('.web-person').first().click();await page.getByRole('heading',{name:'ทดลองครบแล้ว'}).waitFor();assert.deepEqual(errors,[]);
 await page.screenshot({path:path.resolve('work/web-demo-completed.png'),fullPage:true});
 const mobile=await browser.newContext({viewport:{width:390,height:844}}),mp=await mobile.newPage();await mp.goto(url);assert.ok(await mp.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await mobile.close();console.log(JSON.stringify({passed:true,url,flow:'consent/calibration/practice/pre/four tasks/post/export/reload',download:saved,mobile:true}));
}finally{await browser.close()}
