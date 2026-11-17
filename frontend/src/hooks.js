import {useCallback,useEffect,useState} from 'react';
import {api,clientId,accessToken} from './api';
export function useSession(sid,participant=false){
 const [session,setSessionRaw]=useState(null),[error,setError]=useState(''),[connected,setConnected]=useState(false);
 const setSession=useCallback(incoming=>setSessionRaw(previous=>!previous||incoming.session_id!==previous.session_id||(incoming.revision??0)>=(previous.revision??0)?incoming:previous),[]);
 useEffect(()=>{
   let alive=true;
   api('/sessions/'+sid).then(s=>alive&&setSession(s)).catch(e=>alive&&setError(e.message));
   const ws=new WebSocket((location.protocol==='https:'?'wss:':'ws:')+'//'+location.host+'/ws/sessions/'+sid+'?role='+(participant?'participant':'observer')+'&client='+clientId,['eyetrack',accessToken()]);
   ws.onopen=()=>{if(alive)setConnected(true)};
   ws.onmessage=e=>{const d=JSON.parse(e.data);if(!alive)return;if(d.session)setSession(d.session);if(d.error)setError(d.error)};
   ws.onerror=()=>alive&&setError('เชื่อมต่อ backend ไม่สำเร็จ');
   ws.onclose=()=>{if(alive){setConnected(false);setError(e=>e||'การเชื่อมต่อสิ้นสุด กรุณาโหลดหน้าใหม่เพื่อเชื่อมต่ออีกครั้ง')}};
   const timer=setInterval(()=>{if(ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:'heartbeat'}))},1000);
   return()=>{alive=false;clearInterval(timer);ws.close()};
 },[sid,participant]);
 return {session,setSession,error,setError,connected};
}

