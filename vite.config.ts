import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    postcss: './postcss.config.js',
  },
  base: process.env.GITHUB_PAGES ? '/hubcientifico/' : '/',
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: false,
    target: 'esnext',
    rollupOptions: {
      treeshake: false,
      output: {
        format: 'es',
        inlineDynamicImports: true,
      },
    },
  },
  optimizeDeps: {
    force: true,
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@heroui/react',
      'framer-motion',
      'lucide-react',
    ],
  },
})
