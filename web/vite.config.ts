import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// No /api proxy here on purpose — this POC makes zero backend calls at
// runtime (see POC_SPEC.md rule 1). All screens read from the local
// fixture-data seam instead of a network request.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 5173,
  },
});
