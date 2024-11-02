import { AliasOptions, defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

//@ts-ignore
import path from "path";
const root = path.resolve(__dirname, "src");


// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": root,
      "@auth": path.join(root, "features/auth"),
      "@gallery": path.join(root, "features/gallery"),
      "@preferences": path.join(root, "features/preferences"),
      "@navigation": path.join(root, "features/navigation"),
    } as AliasOptions,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:4000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://localhost:4000',
        changeOrigin: true,
      }
    }
  },
})
