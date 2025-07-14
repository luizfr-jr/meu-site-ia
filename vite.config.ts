import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    postcss: './postcss.config.js',
  },
  base: '/meu-site-ia/',
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: false,
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
})
