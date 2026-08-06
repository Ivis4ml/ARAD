import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

// 单文件产出：Atlas 必须是自包含的一页，不依赖任何网络请求。
// Python 渲染器随后把投影 JSON 注入 <head>，因此 app 启动时数据已在文档里。
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: { outDir: 'dist', assetsInlineLimit: 100000000, cssCodeSplit: false },
})
