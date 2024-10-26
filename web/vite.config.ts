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
    } as AliasOptions,
  },
});
