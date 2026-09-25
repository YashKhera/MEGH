import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev: API calls use relative paths, proxied to the FastAPI backend.
// No host:port appears anywhere in the UI.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '^/(health|storms|storm|predict|explain|auth|metrics|frames)': 'http://127.0.0.1:8000',
    },
  },
})
