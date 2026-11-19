import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = env.VITE_BACKEND_TARGET || 'http://127.0.0.1:8000'

  // O backend expõe todas as rotas sob /api (mesmo formato usado em produção)
  const proxyConfig = {
    '/api': {
      target: backendTarget,
      changeOrigin: true,
    },
  }

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      host: '0.0.0.0', // Permite que outros computadores/celulares na rede local acessem pelo IP do servidor
      proxy: proxyConfig,
    },
    preview: {
      port: 5173,
      host: '0.0.0.0',
      proxy: proxyConfig,
    },
  }
})
