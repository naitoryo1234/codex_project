import { defineConfig } from "vite";

const buildId = new Date().toISOString();

export default defineConfig({
  define: {
    __BUILD_ID__: JSON.stringify(buildId)
  },
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