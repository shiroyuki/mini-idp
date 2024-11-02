import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../midp/webui', // Custom output folder
    watch: true, // Enable watch mode
  },
});
