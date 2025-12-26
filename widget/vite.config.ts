import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
      output: {
        entryFileNames: 'zunkiree-widget.iife.js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name][extname]',
      },
    },
    cssCodeSplit: false,
    minify: 'terser',
  },
  server: {
    port: 5173,
    cors: true,
  },
})
