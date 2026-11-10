import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
export default defineConfig({plugins:[react()],resolve:{alias:{'@':path.resolve('.')}},build:{outDir:'.negotiation-preview-build',emptyOutDir:true,copyPublicDir:false,cssCodeSplit:false,rolldownOptions:{input:path.resolve('negotiation-preview.html'),output:{inlineDynamicImports:true}}}});
