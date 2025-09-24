import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server:{
    sourcemap:true,
    proxy:{
      '/api':{
        target: 'http://localhost:6969',
        changeOrigin: true,
      }
    }
  }
})
