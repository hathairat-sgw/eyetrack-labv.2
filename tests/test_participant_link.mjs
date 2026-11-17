import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveParticipantPath,validParticipantPath} from '../frontend/src/participantLink.js';
test('new backend link opens without extra request',async()=>{
 assert.equal(await resolveParticipantPath({session_id:'S123',participant_path:'/participant/S123#access=token'},()=>{throw Error('not needed')}),'/participant/S123#access=token');
});
test('old backend missing path uses participant-link endpoint for same session',async()=>{
 let calls=0;
 assert.equal(await resolveParticipantPath({session_id:'S123'},async()=>{calls++;return {path:'/participant/S123#access=token'}}),'/participant/S123#access=token');
 assert.equal(calls,1);
});
test('missing invalid or cross-session links never become undefined navigation',async()=>{
 for(const path of [undefined,'undefined','/researcher/undefined','https://evil.test/participant/S123#access=x','/participant/S999#access=x','/participant/S123#access=undefined','/participant/S123#access=']){
  assert.equal(validParticipantPath(path,'S123'),false);
  await assert.rejects(resolveParticipantPath({session_id:'S123',participant_path:path},async()=>({path})),/สร้างลิงก์/);
 }
});
