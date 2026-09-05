import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

const root = import.meta.dirname

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(root, "./src"),
    },
  },
  build: {
    rollupOptions: {
      input: {
        landing: path.resolve(root, "index.html"),
        app: path.resolve(root, "app.html"),
      },
    },
  },
})
