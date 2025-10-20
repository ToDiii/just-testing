import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

const virtualBuildInfoModule = {
  name: 'virtual-build-info',
  resolveId(id) {
    if (id === 'virtual:build-info') {
      return id;
    }
  },
  load(id) {
    if (id === 'virtual:build-info') {
      const buildDate = new Date().toLocaleString('en-GB', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
      return `export const buildInfo = { buildDate: '${buildDate}' };`;
    }
  },
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte(), virtualBuildInfoModule],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
