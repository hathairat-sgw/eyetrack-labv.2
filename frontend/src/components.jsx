import React from 'react';
import {ArrowUpRight, CircleCheck, AlertCircle, Eye, LoaderCircle} from 'lucide-react';
export function Brand(){return <div className="brand"><span className="brand-icon"><Eye size={23}/></span><div>EyeTrack <b>Lab</b><small>USABILITY RESEARCH</small></div></div>}
export function Badge({children,kind=''}){return <span className={'badge '+kind}>{children}</span>}
export function Empty({title='ยังไม่มีข้อมูล',children}){return <div className="empty"><Eye size={30}/><h3>{title}</h3><p>{children}</p></div>}
export function ErrorBox({error}){return error ? <div className="error" role="alert"><AlertCircle size={18}/><span>{error}</span></div> : null}
export function Loading(){return <div className="loading"><LoaderCircle size={22} className="spin"/> กำลังโหลด…</div>}
export function PageHeader({eyebrow,title,children,action}){return <div className="page-heading"><div><div className="eyebrow">{eyebrow || 'RESEARCH WORKSPACE'}</div><h1>{title}</h1><p>{children}</p></div>{action}</div>}
export const stateNames={information:'ข้อมูลวิจัย',consent:'รอความยินยอม',pre:'แบบสอบถามก่อน',calibration:'รอ Calibration',calibrating:'กำลัง Calibration',instructions:'พร้อมเริ่มงาน',recording:'กำลังบันทึก',interrupted:'ถูกขัดจังหวะ',post:'แบบสอบถามหลัง',thankyou:'รอจบ session',completed:'เสร็จสิ้น',withdrawn:'ถอนตัว'};
export const conditions={good:'Good + Good',bad:'Bad + Bad',mixed:'Mixed'};
export function StateBadge({state}){return <Badge kind={state==='completed'?'success':state==='recording'?'live':state==='interrupted'?'warning':''}>{stateNames[state]||state}</Badge>}
export {default as QuestionForm} from './QuestionnaireForm';
