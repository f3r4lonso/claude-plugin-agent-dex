import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The build goes straight into the Python package so `pip install` ships the UI.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "../api/src/agent_dex/static",
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8771",
      "/ws": { target: "ws://127.0.0.1:8771", ws: true },
    },
  },
  test: { environment: "node" },
});
