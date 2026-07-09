import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import legacy from '@vitejs/plugin-legacy';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    legacy({
      targets: ['ie >= 11', 'chrome >= 40', 'firefox >= 40', 'safari >= 10'],
      additionalLegacyPolyfills: ['regenerator-runtime/runtime', 'whatwg-fetch'],
      renderLegacyChunks: true,
    }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist-new-flat',
    assetsDir: 'assets',
  },
});