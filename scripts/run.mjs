import {spawn} from 'node:child_process';
import {existsSync,mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import net from 'node:net';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const args=new Set(process.argv.slice(2));
const backendPort=Number(process.env.EYETRACK_BACKEND_PORT||8000);
const frontendPort=Number(process.env.EYETRACK_FRONTEND_PORT||5173);
const url=`http://127.0.0.1:${frontendPort}/researcher`;
const children=[];
let stopping=false;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function occupied(port){return new Promise(resolve=>{const s=net.connect({host:'127.0.0.1',port});s.once('connect',()=>{s.destroy();resolve(true)});s.once('error',()=>resolve(false));s.setTimeout(800,()=>{s.destroy();resolve(false)});});}
async function get(url){const r=await fetch(url,{signal:AbortSignal.timeout(1500)});if(!r.ok)throw Error(`HTTP ${r.status}`);return r;}
const alive=child=>child.exitCode===null&&child.signalCode===null;
async function shutdown(code=0){
 if(stopping)return;stopping=true;
 for(const {name,child} of children){if(!alive(child))continue;if(name==='Backend'){child.stdin.on('error',()=>{});child.stdin.end('stop\n')}else child.kill();}
 const until=Date.now()+10000;
 while(children.some(({child})=>alive(child))&&Date.now()<until)await sleep(100);
 for(const {child} of children)if(alive(child))child.kill();
 process.exit(code);
}
function start(name,exe,argv,cwd,env){
 const child=spawn(exe,argv,{cwd,env,windowsHide:true,stdio:['pipe','inherit','inherit']});
 children.push({name,child});
 child.on('error',e=>{console.error(`${name}: ${e.message}`);shutdown(1)});
 child.on('exit',code=>{if(!stopping){console.error(`${name} exited (${code}).`);shutdown(code||1)}});
}
process.on('SIGINT',()=>shutdown());process.on('SIGTERM',()=>shutdown());
process.on('exit',()=>{for(const {child} of children)if(alive(child))child.kill()});
async function main(){
 if(![backendPort,frontendPort].every(p=>Number.isInteger(p)&&p>=1024&&p<=65535)||backendPort===frontendPort)throw Error('Invalid or duplicate ports');
 const hardware=path.join(root,'.venv-hardware','Scripts','python.exe');
 const python=!args.has('--mock')&&existsSync(hardware)?hardware:path.join(root,'.venv','Scripts','python.exe');
 const vite=path.join(root,'frontend','node_modules','vite','bin','vite.js');
 if(!existsSync(python)||!existsSync(vite))throw Error('Dependencies missing. Run scripts/setup.ps1 first. See README.');
 const ports=await Promise.all([occupied(backendPort),occupied(frontendPort)]);
 if(ports.some(Boolean))throw Error(`Port ${ports.map((v,i)=>v?[backendPort,frontendPort][i]:null).filter(Boolean).join(', ')} is in use. Stop the previous run first. No existing process was stopped.`);
 const env={...process.env,PYTHONUTF8:'1',PYTHONPATH:root,EYETRACK_BACKEND_PORT:String(backendPort),EYETRACK_FRONTEND_PORT:String(frontendPort),EYETRACK_BACKEND_URL:`http://127.0.0.1:${backendPort}`};
 if(args.has('--smoke')||args.has('--isolated'))env.EYETRACK_DATA_DIR=mkdtempSync(path.join(tmpdir(),'eyetrack-launch-'));
 console.log(`EyeTrack Lab\nProject: ${root}\nPython: ${python}\nData: ${env.EYETRACK_DATA_DIR||path.join(root,'data')}`);
 start('Backend',python,[path.join(root,'scripts','serve.py')],root,env);
 start('Frontend',process.execPath,[vite,'--host','127.0.0.1','--port',String(frontendPort),'--strictPort'],path.join(root,'frontend'),env);
 let ready=false;
 const until=Date.now()+30000;
 while(Date.now()<until&&!stopping){try{
  await get(`http://127.0.0.1:${backendPort}/api/health`);
  const health=await (await get(`http://127.0.0.1:${frontendPort}/api/health`)).json();
  if(!health.ok)throw Error(health.error||'Backend unhealthy');
  if(!(await (await get(url)).text()).includes('<title>EyeTrack Lab'))throw Error('Wrong frontend');
  ready=true;break;
 }catch{await sleep(400)}}
 if(stopping)return;
 if(!ready)throw Error('Startup timed out. Check errors above. Browser was not opened.');
 console.log(`READY ${url}\nDevice service runs inside FastAPI. Detection is not proof of calibration or recording.\nCtrl+C stops this run. Stop an active experiment from the website before closing.`);
 if(args.has('--smoke')){await shutdown();return;}
 process.stdin.setEncoding('utf8');
 process.stdin.on('data',data=>{if(data.trim()==='stop')shutdown()});
 if(!args.has('--no-open')){
  const opener=spawn('powershell.exe',['-NoProfile','-Command',`Start-Process '${url}'`],{windowsHide:true,stdio:'ignore'});
  opener.on('error',e=>console.error(`Open ${url} manually: ${e.message}`));
  opener.on('exit',code=>{if(code)console.error(`Browser launch failed. Open ${url} manually.`)});
 }
}
main().catch(async e=>{console.error(`START FAILED: ${e.message}`);await shutdown(1)});
