import type { IncomingMessage } from "node:http";
import type { Plugin, ProxyOptions } from "vite";

export function backendTarget(value: string) {
  const url = new URL(value);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname !== "/"
  ) {
    throw new Error(
      "DIRECTOR_BACKEND_URL must be a loopback HTTP(S) origin without credentials or a path.",
    );
  }
  return url.origin;
}
export function trustedRequest(request: Pick<IncomingMessage, "headers">) {
  const host = request.headers.host;
  if (!host || !/^(127\.0\.0\.1|localhost|\[::1\]):\d+$/.test(host))
    return false;
  const origin = request.headers.origin;
  return !origin || origin === `http://${host}`;
}
// Automatic authorization is limited to the launcher's own browser origin.
// GET fetches may omit Origin; require same-origin Fetch Metadata + Referer then.
export function trustedSessionRequest(
  request: Pick<IncomingMessage, "headers">,
) {
  if (request.headers.host !== "127.0.0.1:5173") return false;
  if (request.headers.origin)
    return request.headers.origin === "http://127.0.0.1:5173";
  if (request.headers["sec-fetch-site"] !== "same-origin") return false;
  try {
    return (
      new URL(String(request.headers.referer)).origin ===
      "http://127.0.0.1:5173"
    );
  } catch {
    return false;
  }
}
export function localApiGuard(sessionKey?: string): Plugin {
  const install = (server: {
    middlewares: {
      use: (
        path: string,
        handler: (
          req: IncomingMessage,
          res: import("node:http").ServerResponse,
          next: () => void,
        ) => void,
      ) => void;
    };
  }) => {
    server.middlewares.use("/api", (req, res, next) => {
      if (req.url === "/launcher-session") {
        const trusted = trustedSessionRequest(req);
        res.statusCode = trusted ? 200 : 403;
        res.setHeader("Content-Type", "application/json");
        res.setHeader("Cache-Control", "no-store");
        res.end(
          JSON.stringify(
            trusted
              ? { automatic: Boolean(sessionKey) }
              : { detail: "Untrusted session origin" },
          ),
        );
        return;
      }
      if (
        sessionKey &&
        req.headers["x-director-session"] === "launcher" &&
        !trustedSessionRequest(req)
      ) {
        res.statusCode = 403;
        res.end(JSON.stringify({ detail: "Untrusted session origin" }));
        return;
      }
      if (trustedRequest(req)) return next();
      res.statusCode = 403;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ detail: "Untrusted local frontend origin" }));
    });
  };
  return {
    name: "director-local-api-guard",
    configureServer: install,
    configurePreviewServer: install,
  };
}
export function apiProxy(target: string, sessionKey?: string): ProxyOptions {
  return {
    target,
    changeOrigin: true,
    configure(proxy) {
      proxy.on("proxyReq", (proxyReq, req) => {
        // Only rewrite a browser Origin after the guard checked Host + Origin.
        // The launcher passes this secret only to server process memory.
        // Preserve supplied wrong keys: they must still fail backend auth.
        if (
          sessionKey &&
          trustedSessionRequest(req) &&
          req.headers["x-director-session"] === "launcher" &&
          !req.headers["x-director-key"]
        )
          proxyReq.setHeader("X-Director-Key", sessionKey);
        proxyReq.removeHeader("X-Director-Session");
        if (req.headers.origin && trustedRequest(req))
          proxyReq.setHeader("Origin", target);
      });
    },
  };
}
