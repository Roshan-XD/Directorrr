import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { DirectorApi } from "./api/client";
import "./styles.css";

try {
  const api = new DirectorApi(import.meta.env.VITE_API_BASE_URL || "/api");
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App api={api} />
    </StrictMode>,
  );
} catch {
  // Do not expose configured URL credentials if configuration is invalid.
  document.getElementById("root")!.textContent =
    "Invalid Director API configuration. Use a local HTTP(S) backend through the documented proxy.";
}
