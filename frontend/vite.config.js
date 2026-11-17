import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],server:{proxy:{'/api':(process.env.EYETRACK_BACKEND_URL||'http://127.0.0.1:8000'),'/ws':{target:(process.env.EYETRACK_BACKEND_URL||'http://127.0.0.1:8000').replace('http','ws'),ws:true}}}});

