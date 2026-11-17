export function validParticipantPath(path,sid){
 if(typeof path!=='string'||typeof sid!=='string'||!/^S[a-zA-Z0-9]+$/.test(sid))return false;
 if(!path.startsWith('/participant/'+sid+'#'))return false;
 const fragment=new URLSearchParams(path.slice(path.indexOf('#')+1));
 const token=fragment.get('access');
 return !!token && !['undefined','null'].includes(token);
}
export async function resolveParticipantPath(session,fetchLink){
 const sid=session?.session_id;
 if(typeof sid!=='string'||!/^S[a-zA-Z0-9]+$/.test(sid))throw new Error('ข้อมูล session ไม่ครบ กรุณาโหลดหน้าควบคุมใหม่');
 if(validParticipantPath(session.participant_path,sid))return session.participant_path;
 // Compatible with an already-running backend which predates participant_path.
 const link=await fetchLink();
 if(validParticipantPath(link?.path,sid))return link.path;
 throw new Error('สร้างลิงก์ผู้เข้าร่วมไม่สำเร็จ กรุณาหยุด Backend เดิมแล้วกด F5 เปิดระบบใหม่');
}
