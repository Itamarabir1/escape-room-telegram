import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// גרסה לכפיית רענון cache בדפדפן/טלפון – להעלות אחרי שינויי CSS
const ASSET_VERSION = '1.1'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'cache-bust-assets',
      apply: 'build',
      transformIndexHtml: {
        order: 'post',
        handler(html) {
          return html
            .replace(/(href="[^"]+\.css")/g, `$1?v=${ASSET_VERSION}`)
            .replace(/(src="[^"]+\.js")/g, `$1?v=${ASSET_VERSION}`)
        },
      },
    },
  ],
  base: '/static/',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
