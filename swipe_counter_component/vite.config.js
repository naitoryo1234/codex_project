import { defineConfig } from "vite";

export default defineConfig({
  root: ".",
  build: {
    outDir: "build",
    assetsDir: ".",
    emptyOutDir: true,
    rollupOptions: {
      input: "index.html",
    },
  },
});