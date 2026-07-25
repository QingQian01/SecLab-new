import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // @novnc/novnc 使用了 top-level await，需要 esnext target 才能构建。
  build: { target: 'esnext' },
  optimizeDeps: { esbuildOptions: { target: 'esnext' } },
  server: {
    proxy: {
      // 将 /api/agent 开头的请求代理到 FastAPI Agent 服务（开发环境）
      '/api/agent': {
        target: 'http://localhost:8010',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api\/agent/, '')
      },
      // Docker API 代理：operation 操作环境路由（start/stop/status/vnc 桥接）
      // 由 ai-agent-service（8010）提供，ws:true 支持 noVNC WebSocket 桥接。
      '/api/docker': {
        target: 'http://localhost:8010',
        changeOrigin: true,
        ws: true,
      }
    }
  }
})
