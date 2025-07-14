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
        manualChunks: undefined,
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
      'firebase/app',
      'firebase/firestore',
    ],
  },
  define: {
    // Ensure environment variables are properly defined
    'import.meta.env.VITE_FIREBASE_API_KEY': JSON.stringify(process.env.VITE_FIREBASE_API_KEY || 'demo-api-key'),
    'import.meta.env.VITE_FIREBASE_PROJECT_ID': JSON.stringify(process.env.VITE_FIREBASE_PROJECT_ID || 'meu-site-ia-demo'),
  }
})
