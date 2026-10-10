import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DirectorApi, validateResponse } from "../api/client";
import type { RuntimeReport } from "../api/types";
import { System } from "../pages/System";
import fixture from "./fixtures.json";

const observation = {
  status: "unknown" as const,
  version: null,
  source: "test",
  detail: "Unknown metadata",
};
const report: RuntimeReport = {
  operating_system: "Windows",
  architecture: "AMD64",
  python: { ...observation, status: "installed", version: "3.11.5" },
  pytorch: observation,
  comfyui: { ...observation, status: "not_configured" },
  driver_cuda: observation,
  cuda_toolkit: { ...observation, status: "not_tested" },
  gpu_drivers: [
    {
      name: "Intel Graphics",
      vendor: "intel",
      driver: { ...observation, version: "31.0.1" },
    },
  ],
  missing_prerequisites: ["ComfyUI is not configured"],
  unresolved_questions: ["GPU execution remains unverified"],
  warnings: ["Driver query incomplete"],
  readiness: "incomplete",
  gpu_execution: "not_tested",
  generation_ready: false,
};

function api(response: () => Promise<Response>) {
  return new DirectorApi(
    "/api",
    45000,
    vi.fn((path) =>
      String(path).endsWith("/runtime")
        ? response()
        : Promise.resolve(new Response(JSON.stringify(fixture.hardware))),
    ),
  );
}

describe("runtime diagnostics", () => {
  it("shows loading without substituting fixtures", async () => {
    render(<System api={api(() => new Promise(() => {}))} />);
    expect(
      await screen.findByText("Inspecting runtime metadata…"),
    ).toBeInTheDocument();
  });
  it("displays honest metadata and unknown compatibility", async () => {
    render(
      <System api={api(async () => new Response(JSON.stringify(report)))} />,
    );
    expect(await screen.findByText("Version: 3.11.5")).toBeInTheDocument();
    expect(screen.getByText("not configured")).toBeInTheDocument();
    expect(
      screen.getByText("GPU execution remains unverified"),
    ).toBeInTheDocument();
    expect(screen.getByText("Driver query incomplete")).toBeInTheDocument();
    expect(screen.getByText(/Driver: 31.0.1/)).toBeInTheDocument();
  });
  it("shows API errors while retaining independent hardware results", async () => {
    render(
      <System
        api={api(
          async () =>
            new Response(JSON.stringify({ detail: "Runtime unavailable" }), {
              status: 503,
            }),
        )}
      />,
    );
    expect(await screen.findByText("Runtime unavailable")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /try again/i }),
    ).toBeInTheDocument();
  });
  it("rejects malformed diagnostics and invented readiness", () => {
    for (const value of [
      { ...report, python: {} },
      { ...report, generation_ready: true },
      { ...report, gpu_execution: "verified" },
    ])
      expect(() => validateResponse(value, "runtime")).toThrow();
  });
  it("calls real endpoint without transmitting manager credentials", async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify(report)));
    const client = new DirectorApi("/api", 100, fetcher);
    client.setKey("secret".repeat(8));
    await client.runtime();
    expect(fetcher).toHaveBeenCalledWith(
      "/api/system/runtime",
      expect.objectContaining({
        headers: { Accept: "application/json" },
        method: "GET",
      }),
    );
  });
});
