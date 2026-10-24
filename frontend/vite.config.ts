import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api and /media are forwarded to the FastAPI backend (built in a later problem).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Allow GitHub Codespaces' forwarded URLs (*.app.github.dev) as well as localhost.
    allowedHosts: [".app.github.dev", "localhost", "127.0.0.1"],
    proxy: {
      "/api": "http://localhost:8000",
      "/media": "http://localhost:8000",
    },
  },
});
