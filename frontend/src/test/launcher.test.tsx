import { expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { apiProxy, trustedSessionRequest, localApiGuard } from "../proxy";
import { DirectorApi } from "../api/client";
import { ManagerAuthorization } from "../components/ManagerAuthorization";

const headers = {
  host: "127.0.0.1:5173",
  origin: "http://127.0.0.1:5173",
  "x-director-session": "launcher",
};
it("injects the server-only key for trusted explicit session requests; never replaces wrong keys", () => {
  let listener: (
    out: {
      setHeader: ReturnType<typeof vi.fn>;
      removeHeader: ReturnType<typeof vi.fn>;
    },
    req: { headers: Record<string, string> },
  ) => void;
  const options = apiProxy("http://127.0.0.1:8000", "s".repeat(64));
  options.configure?.(
    {
      on: (_: string, callback: typeof listener) => {
        listener = callback;
      },
    } as never,
    options,
  );
  const outgoing = { setHeader: vi.fn(), removeHeader: vi.fn() };
  listener!(outgoing, { headers });
  expect(outgoing.setHeader).toHaveBeenCalledWith(
    "X-Director-Key",
    "s".repeat(64),
  );
  expect(outgoing.removeHeader).toHaveBeenCalledWith("X-Director-Session");
  outgoing.setHeader.mockClear();
  listener!(outgoing, { headers: { ...headers, "x-director-key": "wrong" } });
  expect(outgoing.setHeader).not.toHaveBeenCalledWith(
    "X-Director-Key",
    expect.anything(),
  );
  outgoing.setHeader.mockClear();
  listener!(outgoing, {
    headers: { ...headers, origin: "https://evil.example" },
  });
  expect(outgoing.setHeader).not.toHaveBeenCalled();
});
it("rejects absent origin proof, foreign referrers and wrong hosts", () => {
  expect(trustedSessionRequest({ headers: { host: headers.host } })).toBe(
    false,
  );
  expect(
    trustedSessionRequest({
      headers: { ...headers, host: "evil.example:5173" },
    }),
  ).toBe(false);
  expect(
    trustedSessionRequest({
      headers: {
        host: headers.host,
        "sec-fetch-site": "same-origin",
        referer: "http://127.0.0.1:5173/",
      },
    }),
  ).toBe(true);
  expect(
    trustedSessionRequest({
      headers: {
        host: headers.host,
        "sec-fetch-site": "same-origin",
        referer: "https://evil.example/",
      },
    }),
  ).toBe(false);
});
it("returns only a non-secret session flag and blocks untrusted bootstrap", () => {
  let handler: (
    req: { url: string; headers: Record<string, string> },
    res: {
      statusCode: number;
      setHeader: ReturnType<typeof vi.fn>;
      end: ReturnType<typeof vi.fn>;
    },
    next: ReturnType<typeof vi.fn>,
  ) => void;
  const plugin = localApiGuard("s".repeat(64));
  (plugin.configureServer as Function)({
    middlewares: {
      use: (_: string, fn: typeof handler) => {
        handler = fn;
      },
    },
  });
  const res = { statusCode: 0, setHeader: vi.fn(), end: vi.fn() };
  handler!({ url: "/launcher-session", headers }, res, vi.fn());
  expect(res.statusCode).toBe(200);
  expect(res.end).toHaveBeenCalledWith('{"automatic":true}');
  expect(JSON.stringify(res.end.mock.calls)).not.toContain("s".repeat(64));
  handler!(
    {
      url: "/launcher-session",
      headers: { ...headers, origin: "https://evil.example" },
    },
    res,
    vi.fn(),
  );
  expect(res.statusCode).toBe(403);
});
it("uses automatic authorization without receiving or storing a key", async () => {
  const fetcher = vi.fn(
    async (url: string | URL | Request, _options?: RequestInit) =>
      String(url).endsWith("launcher-session")
        ? new Response('{"automatic":true}')
        : new Response("video", { headers: { "Content-Type": "video/webm" } }),
  );
  const api = new DirectorApi("/api", 1000, fetcher, true);
  const changed = vi.fn();
  render(<ManagerAuthorization api={api} onChange={changed} />);
  await screen.findByText("Local session connected");
  expect(screen.queryByLabelText("Manager key")).not.toBeInTheDocument();
  await waitFor(() => expect(changed).toHaveBeenCalledWith(true));
  await api.generationOutput("a".repeat(32));
  const options = fetcher.mock.calls.at(-1)?.[1] as RequestInit | undefined;
  expect(options?.headers).toHaveProperty("X-Director-Session", "launcher");
  expect(options?.headers).not.toHaveProperty("X-Director-Key");
  expect(localStorage.getItem("director-manager-key")).toBeNull();
});
