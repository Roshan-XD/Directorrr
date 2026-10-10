import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { DirectorApi } from "../api/client";
import type { InstallationJob } from "../api/types";
import fixture from "./fixtures.json";

const id = "a".repeat(32);
function job(state = "downloading"): InstallationJob {
  return {
    id,
    model_id: "fixture-tiny",
    operation: "install",
    state,
    total_expected_bytes: 60,
    candidate_bytes: 30,
    verified_bytes: 0,
    cancel_requested: false,
    current_component: "tiny",
    error:
      state === "failed"
        ? { code: "network_failure", message: "Network unavailable" }
        : null,
    created_at: "2026-10-09T00:00:00Z",
    updated_at: "2026-10-09T00:00:00Z",
    generation_ready: false,
  };
}
function client(overrides: Record<string, unknown> = {}) {
  const untested = {
    status: "unknown",
    version: null,
    source: "test",
    detail: "Not validated",
  };
  const responses: Record<string, unknown> = {
    "/api/models": fixture.models,
    "/api/system/hardware": fixture.hardware,
    "/api/system/runtime": {
      operating_system: "Windows",
      architecture: "AMD64",
      python: untested,
      pytorch: untested,
      comfyui: untested,
      cuda_toolkit: untested,
      driver_cuda: untested,
      gpu_drivers: [],
      missing_prerequisites: [],
      unresolved_questions: [],
      warnings: [],
      readiness: "unknown",
      gpu_execution: "not_tested",
      generation_ready: false,
    },
    [`/api/installation-jobs/${id}`]: job(),
    [`/api/installation-jobs/${id}/cancel`]: {
      ...job("cancelled"),
      cancel_requested: true,
    },
    ...overrides,
  };
  for (const model of fixture.models.models) {
    const modelId = model.manifest.id;
    responses[`/api/models/${modelId}/installation-plan`] =
      fixture.plans[modelId as keyof typeof fixture.plans];
    responses[`/api/models/${modelId}/installation`] = {
      model_id: modelId,
      state: "not_installed",
      artifact_ready: false,
      generation_ready: false,
      job_id: null,
      verification: [],
      incomplete_bundles: [],
    };
  }
  const fetcher = vi.fn(
    async (path: string | URL | Request, _options?: RequestInit) => {
      if (String(path).endsWith("/cancel"))
        responses[`/api/installation-jobs/${id}`] = responses[String(path)];
      return new Response(JSON.stringify(responses[String(path)]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  );
  const api = new DirectorApi("/api", 45000, fetcher as typeof fetch);
  return { api, fetcher };
}
describe("Director workspace", () => {
  it("shows hardware errors without replacing missing values with fake readings", async () => {
    window.location.hash = "#system";
    const { api } = client({ "/api/system/hardware": {} });
    render(<App api={api} />);
    await screen.findByRole("alert");
    expect(screen.queryByText("Test GPU")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
  });
  it("navigates all four sections and keeps generation disabled", async () => {
    const user = userEvent.setup();
    const { api, fetcher } = client();
    render(<App api={api} />);
    expect(
      screen.getByRole("button", { name: /Generate video/ }),
    ).toBeDisabled();
    expect(
      screen.getByText(/Inference is not implemented yet/),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("radio", { name: "Image to video" }));
    expect(screen.getByRole("button", { name: "Choose image" })).toBeDisabled();
    await user.type(
      screen.getByRole("textbox", { name: "Your prompt" }),
      "A scene",
    );
    await user.click(screen.getByRole("link", { name: "Models" }));
    await screen.findByRole("heading", { name: "Find your creative engine" });
    await screen.findByRole("button", { name: /MOCK CPU Video Example/ });
    await user.click(screen.getByRole("link", { name: "Jobs" }));
    await screen.findByText("No tracked jobs yet");
    await user.click(screen.getByRole("link", { name: "System" }));
    await screen.findByRole("heading", { name: "Test CPU" });
    expect(
      fetcher.mock.calls.every((call) => !String(call[0]).includes("generate")),
    ).toBe(true);
  });
  it("shows actual manifest evidence, unknown requirements and blockers", async () => {
    window.location.hash = "#models";
    const { api } = client();
    render(<App api={api} />);
    const wan = await screen.findByRole("button", { name: /Wan 2.1/ });
    await userEvent.click(wan);
    await waitFor(() =>
      expect(screen.getByText("Exact download").nextSibling).toHaveTextContent(
        "9.15 GiB",
      ),
    );
    expect(
      screen.getByText("Required storage incl. overhead").nextSibling,
    ).toHaveTextContent("Unknown");
    expect(
      screen.getByText(/Complete artifact and license review is outstanding/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Review license and installation/ }),
    ).toBeDisabled();
    expect(screen.getAllByText("Blocker").length).toBeGreaterThan(0);
  });
  it("handles future unknown compatibility without claiming support", async () => {
    const data = structuredClone(fixture.models);
    data.models[0].compatibility.assessment =
      "new_unknown_value" as (typeof data.models)[0]["compatibility"]["assessment"];
    window.location.hash = "#models";
    const { api } = client({ "/api/models": data });
    render(<App api={api} />);
    await screen.findByRole("button", { name: /MOCK CPU Video Example/ });
    expect(screen.getAllByText("Compatibility unknown").length).toBeGreaterThan(
      0,
    );
  });
  it("shows hardware, estimates and detection warnings", async () => {
    window.location.hash = "#system";
    const { api } = client();
    render(<App api={api} />);
    await screen.findByText("Test GPU");
    expect(screen.getByText("32.00 GiB")).toBeInTheDocument();
    expect(
      screen.getByText("Architecture: Unknown", { exact: false }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Unreliable for compatibility"),
    ).toBeInTheDocument();
    expect(screen.getByText(fixture.hardware.warnings[0])).toBeInTheDocument();
  });
  it("distinguishes incomplete GPU detection from no GPU", async () => {
    window.location.hash = "#system";
    const hardware = {
      ...fixture.hardware,
      gpus: [],
      gpu_detection_complete: false,
    };
    const { api } = client({ "/api/system/hardware": hardware });
    render(<App api={api} />);
    await screen.findByText(
      "GPU detection is incomplete. Available GPUs are unknown.",
    );
    expect(screen.queryByText("No GPU detected.")).not.toBeInTheDocument();
  });
  it("shows a loading state without successful placeholder data", () => {
    const api = new DirectorApi(
      "/api",
      45000,
      vi.fn(() => new Promise<Response>(() => {})),
    );
    window.location.hash = "#models";
    render(<App api={api} />);
    expect(screen.getByText("Reading model registry…")).toBeInTheDocument();
    expect(screen.queryByText("Backend connected")).not.toBeInTheDocument();
  });
  it("shows connection errors and allows retry", async () => {
    window.location.hash = "#models";
    const fetcher = vi.fn().mockRejectedValue(new Error("offline"));
    render(<App api={new DirectorApi("/api", 100, fetcher)} />);
    await screen.findByRole("alert");
    expect(screen.getByText("Backend unavailable")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  });
  it("shows empty registry and search states", async () => {
    window.location.hash = "#models";
    const { api } = client({
      "/api/models": { models: [], hardware_warnings: [] },
    });
    render(<App api={api} />);
    await screen.findByText("Your registry is empty");
  });
  it("supports keyboard navigation and a skip link", async () => {
    const { api } = client();
    render(<App api={api} />);
    const user = userEvent.setup();
    await user.tab();
    expect(screen.getByRole("link", { name: "Skip to content" })).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("main")).toHaveFocus();
    screen.getByRole("link", { name: "System" }).focus();
    await user.keyboard("{Enter}");
    await screen.findByRole("heading", { name: "Know your system" });
  });
  it.each(["checking", "downloading", "ready", "failed", "cancelled"])(
    "tracks real job lookup with state %s",
    async (state) => {
      window.location.hash = "#jobs";
      const { api, fetcher } = client({
        [`/api/installation-jobs/${id}`]: job(state),
      });
      render(<App api={api} />);
      const user = userEvent.setup();
      await user.type(
        screen.getByRole("textbox", { name: "Look up a job" }),
        id,
      );
      await user.click(screen.getByRole("button", { name: "Track job" }));
      await screen.findByText(state);
      expect(
        fetcher.mock.calls.some(
          (call) => String(call[0]) === `/api/installation-jobs/${id}`,
        ),
      ).toBe(true);
      expect(sessionStorage.getItem("director.job-ids.v1")).toContain(id);
      expect(screen.getByText(/Verified 0 B/)).toBeInTheDocument();
      expect(
        fetcher.mock.calls.every(
          (call) => String(call[0]) !== "/api/installation-jobs",
        ),
      ).toBe(true);
    },
  );
  it("rejects invalid job IDs before making a lookup request", async () => {
    window.location.hash = "#jobs";
    const { api, fetcher } = client();
    render(<App api={api} />);
    await userEvent.type(
      screen.getByRole("textbox", { name: "Look up a job" }),
      "../bad",
    );
    await userEvent.click(screen.getByRole("button", { name: "Track job" }));
    expect(screen.getByRole("alert")).toHaveTextContent("32-character");
    expect(
      fetcher.mock.calls.every(
        (call) => !String(call[0]).includes("installation-jobs"),
      ),
    ).toBe(true);
  });
  it("keeps a key in memory only and cancels only on explicit click", async () => {
    window.location.hash = "#jobs";
    sessionStorage.setItem("director.job-ids.v1", JSON.stringify([id]));
    const { api, fetcher } = client();
    render(<App api={api} />);
    const user = userEvent.setup();
    const cancel = await screen.findByRole("button", { name: "Cancel job" });
    expect(cancel).toBeDisabled();
    const key = "private-test-key-never-persisted-12345";
    await user.type(screen.getByLabelText("Manager key"), key);
    await user.click(screen.getByRole("button", { name: "Use key" }));
    expect(cancel).toBeEnabled();
    expect(JSON.stringify({ ...sessionStorage })).not.toContain(key);
    await user.click(cancel);
    await screen.findByText("cancelled");
    const request = fetcher.mock.calls.find((call) =>
      String(call[0]).endsWith("/cancel"),
    );
    expect((request?.[1] as RequestInit).headers).toHaveProperty(
      "X-Director-Key",
      key,
    );
    await user.click(screen.getByRole("button", { name: "Clear key" }));
    expect(api.hasKey()).toBe(false);
  });
});
