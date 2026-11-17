import test from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import {spawn} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
test('occupied backend port fails without stopping its owner',async()=>{
 const server=net.createServer(socket=>socket.end());
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
 const port=server.address().port;
 try{
  const result=await new Promise((resolve,reject)=>{
   const child=spawn(process.execPath,['scripts/run.mjs','--smoke'],{cwd:root,windowsHide:true,env:{...process.env,EYETRACK_BACKEND_PORT:String(port)}});let output='';
   child.stdout.on('data',d=>output+=d);child.stderr.on('data',d=>output+=d);child.on('error',reject);
   child.on('exit',code=>resolve({code,output}));
  });
  assert.equal(result.code,1);assert.ok(result.output.includes(String(port))&&result.output.includes("is in use"));assert.equal(server.listening,true);
 }finally{await new Promise(resolve=>server.close(resolve))}
});
