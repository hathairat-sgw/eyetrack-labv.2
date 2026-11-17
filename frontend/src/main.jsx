import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter,Routes,Route,Navigate} from 'react-router-dom';
import {Researcher,Dashboard,Sessions,Questionnaires,Tasks,Device,Runner,RunnerSession,Results,SessionResults,ExportPage} from './Researcher';
import Participant from './Participant';
import ExternalControl from './ExternalControl';
import TrackCatalog from './TrackCatalog';
import Stimulus from './Stimulus';
import LebPreview from './LebPreview';
import './styles.css';
class Boundary extends React.Component{state={error:null};static getDerivedStateFromError(error){return {error}}render(){return this.state.error?<div className="fatal"><h1>เปิดหน้านี้ไม่สำเร็จ</h1><p>{this.state.error.message}</p><a href="/">กลับไปหน้าแรก</a></div>:this.props.children}}
createRoot(document.getElementById('root')).render(<Boundary><BrowserRouter><Routes><Route path="/" element={<Navigate to="/researcher" replace/>}/><Route path="/researcher" element={<Researcher/>}><Route index element={<Dashboard/>}/><Route path="undefined" element={<Navigate to="/researcher/external" replace/>}/><Route path="external" element={<ExternalControl/>}/><Route path="external/:sid" element={<ExternalControl/>}/><Route path="tracks" element={<TrackCatalog/>}/><Route path="sessions" element={<Sessions/>}/><Route path="questionnaires" element={<Questionnaires/>}/><Route path="device" element={<Device/>}/><Route path="tasks" element={<Tasks/>}/><Route path="runner" element={<Runner/>}/><Route path="runner/:sid" element={<RunnerSession/>}/><Route path="results" element={<Results/>}/><Route path="results/:sid" element={<SessionResults/>}/><Route path="export" element={<ExportPage/>}/></Route><Route path="/participant/:sid" element={<Participant/>}/><Route path="/stimuli/leb-preview" element={<LebPreview/>}/><Route path="/stimuli/demo" element={<Stimulus preview/>}/><Route path="*" element={<div className="fatal"><h1>ไม่พบหน้านี้</h1><a href="/">กลับหน้าแรก</a></div>}/></Routes></BrowserRouter></Boundary>);

