import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DirectorApi, validateResponse } from "../api/client";
import { DevelopmentGenerate } from "../components/DevelopmentGenerate";
import type { GenerationJob } from "../api/types";

const id = "b".repeat(32);
function job(state: GenerationJob["state"]): GenerationJob {
  return {
    id,
    state,
    comfy_prompt_id: "12345678-1234-1234-1234-123456789abc",
    progress: null,
    message:
      state === "failed" ? "ComfyUI execution failed" : "Development job",
    output_filename:
      state === "completed" ? `Director_Stage8_${id}_1_.webm` : null,
    output_url:
      state === "completed" ? `/api/dev/generation/jobs/${id}/output` : null,
    development_only: true,
  };
}
beforeEach(() => {
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(() => "blob:local-preview"),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    value: vi.fn(),
  });
});
function setup({
  enabled = true,
  states = ["completed"],
  fail = false,
}: {
  enabled?: boolean;
  states?: GenerationJob["state"][];
  fail?: boolean;
} = {}) {
  const sequence = [...states];
  const fetcher = vi.fn(
    async (url: string | URL | Request, options?: RequestInit) => {
      const path = String(url);
      if (path.endsWith("/config"))
        return Response.json({ enabled, development_only: true });
      if (fail)
        return Response.json(
          { detail: { message: "ComfyUI unavailable" } },
          { status: 502 },
        );
      if (path.endsWith("/output"))
        return new Response("fixture video", {
          headers: { "Content-Type": "video/webm" },
        });
      return Response.json(
        options?.method === "POST"
          ? job("queued")
          : job(sequence.length > 1 ? sequence.shift()! : sequence[0]),
      );
    },
  );
  const api = new DirectorApi("/api", 45000, fetcher as typeof fetch);
  return { api, fetcher };
}
async function enter(api: DirectorApi) {
  api.setKey("k".repeat(32));
  render(<DevelopmentGenerate api={api} />);
  await waitFor(() =>
    expect(
      screen.queryByText("Checking development adapter…"),
    ).not.toBeInTheDocument(),
  );
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Your prompt"), "Ocean at sunset");
  return user;
}
describe("Development generation", () => {
  it("requires manager authorization and backend opt-in", async () => {
    const { api } = setup();
    render(<DevelopmentGenerate api={api} />);
    await screen.findByText(/Enter your local manager key/);
    expect(
      screen.getByRole("button", { name: "Generate video" }),
    ).toBeDisabled();
  });
  it("stays disabled when backend mode is off", async () => {
    const { api } = setup({ enabled: false });
    await enter(api);
    expect(
      screen.getByRole("button", { name: "Generate video" }),
    ).toBeDisabled();
  });
  it("submits prompt and seed only, tracks completion and previews an authenticated blob", async () => {
    const { api, fetcher } = setup();
    const user = await enter(api);
    await user.click(screen.getByRole("button", { name: "Generate video" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Generated video")).toHaveAttribute(
        "src",
        "blob:local-preview",
      ),
    );
    const submission = fetcher.mock.calls.find(
      ([, init]) => init?.method === "POST",
    )!;
    expect(JSON.parse(submission[1]!.body as string)).toEqual({
      prompt: "Ocean at sunset",
      seed: 20261009,
    });
    const output = fetcher.mock.calls.find(([path]) =>
      String(path).endsWith("/output"),
    )!;
    expect(output[1]?.headers).toHaveProperty("X-Director-Key", "k".repeat(32));
    expect(String(output[0])).not.toContain("kkkk");
    expect(localStorage.length).toBe(0);
  });
  it("shows running state and prevents duplicate submission", async () => {
    const { api, fetcher } = setup({ states: ["running", "completed"] });
    const user = await enter(api);
    await user.click(screen.getByRole("button", { name: "Generate video" }));
    await screen.findByText("running: Development job");
    expect(
      screen.getByRole("button", { name: "Generate video" }),
    ).toBeDisabled();
    await screen.findByLabelText("Generated video", {}, { timeout: 4000 });
    expect(
      fetcher.mock.calls.filter(([, init]) => init?.method === "POST"),
    ).toHaveLength(1);
  });
  it("shows execution failures", async () => {
    const { api } = setup({ states: ["failed"] });
    const user = await enter(api);
    await user.click(screen.getByRole("button", { name: "Generate video" }));
    await screen.findByText("failed: ComfyUI execution failed");
    expect(screen.queryByLabelText("Generated video")).not.toBeInTheDocument();
  });
  it("shows submission errors without fabricating success", async () => {
    const { api } = setup({ fail: true });
    const user = await enter(api);
    await user.click(screen.getByRole("button", { name: "Generate video" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "ComfyUI unavailable",
    );
  });
  it("revokes preview URLs on unmount", async () => {
    const { api } = setup();
    api.setKey("k".repeat(32));
    const view = render(<DevelopmentGenerate api={api} />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Your prompt"), "ocean");
    await user.click(screen.getByRole("button", { name: "Generate video" }));
    await screen.findByLabelText("Generated video");
    view.unmount();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:local-preview");
  });
  it("rejects malformed status and external output URLs", () => {
    expect(() =>
      validateResponse(
        { ...job("completed"), output_url: "http://evil.example" },
        "generationJob",
      ),
    ).toThrow();
    expect(() =>
      validateResponse({ ...job("running"), progress: 90 }, "generationJob"),
    ).toThrow();
  });
});
