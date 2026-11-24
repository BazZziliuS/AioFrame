import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Allow tunnels (cloudflared / ngrok) used to open the dev server inside Telegram
    allowedHosts: true,
    proxy: {
      "/api": "http://127.0.0.1:8080",
    },
  },
  build: {
    // FastAPI serves the built app from webapp/static
    outDir: "../webapp/static",
    emptyOutDir: true,
    // HeroUI + react-aria are ~190 kB gzip: fine for a Mini App, no need to warn
    chunkSizeWarningLimit: 700,
  },
});
