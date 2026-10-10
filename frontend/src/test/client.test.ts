import { afterEach, describe, expect, it, vi } from "vitest";
import { DirectorApi } from "../api/client";
import fixture from "./fixtures.json";
import { readHistory, writeHistory } from "../hooks/history";
import { apiProxy, backendTarget, trustedRequest } from "../proxy";

afterEach(() => vi.useRealTimers());
describe("typed API client", () => {
  it("rejects incomplete nested model fields instead of crashing the UI", async () => {
    const data = structuredClone(fixture.models);
    const broken = data.models[0].manifest as unknown as Record<
      string,
      unknown
    >;
    broken.tasks = null;
    const api = new DirectorApi(
      "/api",
      100,
      vi.fn(async () => new Response(JSON.stringify(data))),
    );
    await expect(api.models()).rejects.toMatchObject({
      code: "invalid_response",
    });
  });
  it("handles real-shaped JSON and configurable base paths", async () => {
    const fetcher = vi.fn(
      async () => new Response(JSON.stringify(fixture.models), { status: 200 }),
    );
    const api = new DirectorApi("http://127.0.0.1:8000/api", 45000, fetcher);
    expect((await api.models()).models).toHaveLength(3);
    expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/models",
      expect.objectContaining({
        method: "GET",
        redirect: "error",
        credentials: "omit",
      }),
    );
  });
  it.each([
    "https://remote.example/api",
    "http://secret:password@localhost/api",
    "file:///api",
  ])("rejects unsafe target %s", (url) => {
    expect(() => new DirectorApi(url)).toThrow();
  });
  it("does not send a manager key on GET requests", async () => {
    const fetcher = vi.fn(
      async (_url: string | URL | Request, _options?: RequestInit) =>
        new Response(JSON.stringify(fixture.hardware)),
    );
    const api = new DirectorApi("/api", 45000, fetcher);
    api.setKey("a".repeat(32));
    await api.hardware();
    expect(fetcher.mock.calls[0][1]?.headers).not.toHaveProperty(
      "X-Director-Key",
    );
  });
  it("handles structured backend errors", async () => {
    const api = new DirectorApi(
      "/api",
      100,
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              detail: {
                code: "cancellation_too_late",
                message: "Job in commit section",
              },
            }),
            { status: 409 },
          ),
      ),
    );
    api.setKey("a".repeat(32));
    await expect(api.cancel("a".repeat(32))).rejects.toMatchObject({
      status: 409,
      code: "cancellation_too_late",
      message: "Job in commit section",
    });
  });
  it.each([
    {},
    { models: [], hardware_warnings: null },
    "<html>Wrong server</html>",
  ])("rejects malformed response %j", async (response) => {
    const api = new DirectorApi(
      "/api",
      100,
      vi.fn(
        async () =>
          new Response(
            typeof response === "string" ? response : JSON.stringify(response),
          ),
      ),
    );
    await expect(api.models()).rejects.toMatchObject({
      code: "invalid_response",
    });
  });
  it("handles a network failure without pretending success", async () => {
    const api = new DirectorApi(
      "/api",
      100,
      vi.fn(async () => {
        throw new Error("offline");
      }),
    );
    await expect(api.models()).rejects.toMatchObject({ code: "network_error" });
  });
  it("times out and aborts the underlying request", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn(
      (_url: string | URL | Request, options?: RequestInit) =>
        new Promise<Response>((_resolve, reject) =>
          options?.signal?.addEventListener("abort", () =>
            reject(new DOMException("aborted", "AbortError")),
          ),
        ),
    );
    const api = new DirectorApi("/api", 10, fetcher);
    const expected = expect(api.models()).rejects.toMatchObject({
      code: "timeout",
    });
    await vi.advanceTimersByTimeAsync(11);
    await expected;
    expect(fetcher.mock.calls[0][1]?.signal?.aborted).toBe(true);
  });
});
describe("local proxy and session boundaries", () => {
  it("allows only matching local browser origins", () => {
    expect(
      trustedRequest({
        headers: { host: "127.0.0.1:5173", origin: "http://127.0.0.1:5173" },
      }),
    ).toBe(true);
    expect(
      trustedRequest({
        headers: { host: "127.0.0.1:5173", origin: "https://evil.example" },
      }),
    ).toBe(false);
    expect(trustedRequest({ headers: { host: "evil.example:5173" } })).toBe(
      false,
    );
    expect(() => backendTarget("https://evil.example")).toThrow();
    expect(() => backendTarget("http://token@localhost:8000")).toThrow();
    expect(backendTarget("http://127.0.0.1:8000")).toBe(
      "http://127.0.0.1:8000",
    );
  });
  it("rewrites trusted Origin without injecting a key", () => {
    let listener: (
      proxyReq: { setHeader: ReturnType<typeof vi.fn> },
      req: { headers: Record<string, string> },
    ) => void;
    const options = apiProxy("http://127.0.0.1:8000");
    const fake = {
      on: vi.fn((_event, callback) => {
        listener = callback;
      }),
    };
    options.configure?.(fake as never, options);
    const outgoing = { setHeader: vi.fn(), removeHeader: vi.fn() };
    listener!(outgoing, {
      headers: { host: "127.0.0.1:5173", origin: "http://127.0.0.1:5173" },
    });
    expect(outgoing.setHeader).toHaveBeenCalledExactlyOnceWith(
      "Origin",
      "http://127.0.0.1:8000",
    );
  });
  it("validates and caps job history", () => {
    sessionStorage.setItem("director.job-ids.v1", "bad JSON");
    expect(readHistory()).toEqual([]);
    sessionStorage.setItem(
      "director.job-ids.v1",
      JSON.stringify(["../bad", "a".repeat(32), "a".repeat(32)]),
    );
    expect(readHistory()).toEqual(["a".repeat(32)]);
    writeHistory(
      Array.from({ length: 20 }, (_, i) => i.toString(16).padStart(32, "0")),
    );
    expect(readHistory()).toHaveLength(12);
  });
});
