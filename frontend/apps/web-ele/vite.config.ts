import { defineConfig, viteCssLayerPlugin } from '@vben/vite-config';

import ElementPlus from 'unplugin-element-plus/vite';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      plugins: [
        // element-plus 的 css 包进 @layer el，使 Tailwind 工具类可覆盖组件样式
        viteCssLayerPlugin({ layerName: 'el', packageName: 'element-plus' }),
        ElementPlus({ format: 'esm' }),
      ],
      server: {
        proxy: {
          // 用 /api/（带斜杠）匹配，避免误匹配前端路由 /api-assets。
          '/api/': {
            changeOrigin: true,
            // 去掉 /api 前缀；集合根路径（/api/xxx 无更深路径段）补尾斜杠，
            // 避免 FastAPI 307 重定向到后端直连地址触发浏览器 CORS。
            rewrite: (path) => {
              const stripped = path.replace(/^\/api/, '');
              const clean = stripped.split('?')[0];
              if (clean && clean !== '/' && !clean.slice(1).includes('/')) {
                return stripped.replace(clean, `${clean}/`);
              }
              return stripped;
            },
            // SAIL 后端 FastAPI
            target: 'http://localhost:8765/api',
            ws: true,
          },
        },
      },
    },
  };
});
