import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {fileURLToPath} from 'node:url';
export default defineConfig({root:fileURLToPath(new URL('./web-demo',import.meta.url)),base:'./',plugins:[react()],build:{outDir:'../../web-dist',emptyOutDir:true},server:{host:'127.0.0.1',port:5180,strictPort:true}});
