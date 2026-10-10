import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { apiProxy, backendTarget, localApiGuard } from "./src/proxy.ts";

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd(), "DIRECTOR_");
  const target = backendTarget(
    env.DIRECTOR_BACKEND_URL || "http://127.0.0.1:8000",
  );
  const sessionKey =
    command === "serve" && mode !== "production"
      ? process.env.DIRECTOR_LAUNCHER_TOKEN
      : undefined;
  if (sessionKey && sessionKey.length < 64)
    throw new Error("Invalid launcher session configuration");
  return {
    plugins: [localApiGuard(sessionKey), react()],
    server: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: { "/api": apiProxy(target, sessionKey) },
    },
    preview: {
      host: "127.0.0.1",
      port: 4173,
      strictPort: true,
      proxy: { "/api": apiProxy(target) },
    },
  };
});
