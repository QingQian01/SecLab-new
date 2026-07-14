import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 将 /api/agent 开头的请求代理到 FastAPI Agent 服务（开发环境）
      '/api/agent': {
        target: 'http://localhost:8010',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api\/agent/, '')
      },
      // 保留旧的 Docker API 代理（兼容）
      '/api/docker': {
        target: 'http://localhost:8087',
        changeOrigin: true,
      }
    }
  }
})
