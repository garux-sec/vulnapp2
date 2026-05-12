import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// VULNERABLE #18: Source maps enabled in production build — exposes original source code
export default defineConfig({
  plugins: [vue()],
  build: {
    sourcemap: true,          // VULNERABLE #18: .js.map files generated and served
    minify: false,            // VULNERABLE: unminified source in production
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    hmr: false,
    // VULNERABLE #23: No security headers configured (no X-Frame-Options)
    headers: {
      // 'X-Frame-Options': 'DENY',          // intentionally omitted → clickjacking
      // 'Content-Security-Policy': '...',    // intentionally omitted → XSS
      // 'X-Content-Type-Options': 'nosniff', // intentionally omitted
    },
  },
})
