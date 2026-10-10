import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { CreativeForm, ProductWorkspace } from "../pages/ProductWorkspace";
import { ProductModelStore } from "../components/product/ProductModelStore";
import { DirectorApi, validateResponse } from "../api/client";
import type { Capability } from "../api/product";
import rawWan from "../../../model_registry/capabilities/wan.json";
import rawH3 from "../../../model_registry/capabilities/minimax-h3.json";
import fixture from "./fixtures.json";
const wan: Capability = {
  ...rawWan,
  blockers: [],
  workspaces: ["text-to-video"],
  adapter: "wan-native-v1",
  native_audio: false,
  continuation: "none",
  frame_multiple: 4,
  frame_offset: 1,
  installed: true,
  runnable: true,
  model_bytes: 9828025775,
  installation_status: "installed_development",
  compatibility: "validated_baseline",
};
const h3: Capability = {
  ...rawH3,
  workspaces: [
    "text-to-video",
    "image-to-video",
    "reference-to-video",
    "first-last-frame",
  ],
  adapter: null,
  native_audio: true,
  installed: false,
  runnable: false,
  model_bytes: 0,
  installation_status: "not_installed",
  compatibility: "unknown",
};
const id = "a".repeat(32);
function apiFor(state = "queued") {
  const fetcher = vi.fn(
    async (input: string | URL | Request, options?: RequestInit) => {
      void options;
      const path = String(input);
      if (path.includes("/launcher-session"))
        return Response.json({ automatic: true });
      if (path === "/api/models") return Response.json(fixture);
      if (path === "/api/product/models")
        return Response.json({ models: [wan, h3], production_ready: false });
      if (path === "/api/product/jobs")
        return Response.json({
          jobs: [
            {
              id,
              state,
              progress: null,
              message: "Observed ComfyUI state",
              comfy_prompt_id: null,
              output_filename: null,
              output_url: null,
              development_only: true,
            },
          ],
          session_only: true,
        });
      if (path === "/api/product/installation-jobs")
        return Response.json({ jobs: [] });
      if (path === "/api/product/console")
        return Response.json({
          events: [
            {
              time: "now",
              stage: "generation",
              message: "Job queued",
              level: "info",
            },
          ],
        });
      if (path.includes("/discovery"))
        return Response.json({
          items: [
            {
              id: "a/video",
              title: "<script>test</script>",
              source: "https://huggingface.co/a/video",
              license: "unknown",
              pipeline: "text-to-video",
              downloads: null,
              revision: null,
              status: "discovered_not_runnable",
            },
          ],
          cached: false,
          message: "Metadata only",
        });
      if (path.includes("/forget"))
        return Response.json({ forgotten: true, output_deleted: false });
      return Response.json({ detail: "Unavailable" }, { status: 502 });
    },
  );
  const api = new DirectorApi("/api", 1000, fetcher, true);
  return { api, fetcher };
}
it("renders only supported workspace and hides audio on Wan", () => {
  render(<CreativeForm model={wan} disabled={false} onGenerate={vi.fn()} />);
  expect(
    screen.getByLabelText("Workspace").querySelectorAll("option"),
  ).toHaveLength(1);
  expect(screen.queryByLabelText(/Audio/)).not.toBeInTheDocument();
  expect(screen.getByText(/No interpolation/)).toBeInTheDocument();
});
it("duration, aspect, quality, random seed and camera become typed settings", async () => {
  const generate = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<CreativeForm model={wan} disabled={false} onGenerate={generate} />);
  await user.type(screen.getByLabelText("Describe your scene"), "Ocean");
  await user.selectOptions(screen.getByLabelText("Duration"), "4");
  await user.selectOptions(
    screen.getByLabelText("Aspect and resolution"),
    "portrait",
  );
  await user.selectOptions(screen.getByLabelText("Quality"), "High");
  await user.selectOptions(
    screen.getByLabelText("Camera guidance"),
    "pan-left",
  );
  await user.click(screen.getByRole("button", { name: "Generate scene" }));
  expect(generate).toHaveBeenCalledWith(
    expect.objectContaining({
      prompt: "Ocean",
      duration: 4,
      resolution: "portrait",
      quality: "High",
      camera: "pan-left",
      seed: null,
      export_fps: 16,
    }),
  );
  expect(screen.getByText(/65 frames/)).toBeInTheDocument();
});
it("seed is not prelocked and advanced controls are disclosed explicitly", async () => {
  const user = userEvent.setup();
  const generate = vi.fn().mockResolvedValue(undefined);
  render(<CreativeForm model={wan} disabled={false} onGenerate={generate} />);
  expect(screen.queryByLabelText("Seed")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("Steps override")).not.toBeInTheDocument();
  await user.click(
    screen.getByLabelText("Lock seed for repeatable comparisons"),
  );
  await user.clear(screen.getByLabelText("Seed"));
  await user.type(screen.getByLabelText("Seed"), "42");
  await user.click(screen.getByRole("button", { name: "Advanced settings" }));
  await user.type(screen.getByLabelText("Steps override"), "12");
  await user.type(screen.getByLabelText("Describe your scene"), "Ocean");
  await user.click(screen.getByRole("button", { name: "Generate scene" }));
  expect(generate).toHaveBeenCalledWith(
    expect.objectContaining({ seed: 42, steps: 12 }),
  );
});
it("invalid locked seed blocks generation", async () => {
  const user = userEvent.setup();
  render(<CreativeForm model={wan} disabled={false} onGenerate={vi.fn()} />);
  await user.type(screen.getByLabelText("Describe your scene"), "Ocean");
  await user.click(
    screen.getByLabelText("Lock seed for repeatable comparisons"),
  );
  await user.clear(screen.getByLabelText("Seed"));
  await user.type(screen.getByLabelText("Seed"), "999999999999999999999");
  expect(screen.getByRole("button", { name: "Generate scene" })).toBeDisabled();
});
it("unavailable candidate cannot generate", () => {
  render(<CreativeForm model={h3} disabled={false} onGenerate={vi.fn()} />);
  expect(screen.getByRole("button", { name: "Generate scene" })).toBeDisabled();
  expect(screen.getByText(/Discovering a model/)).toBeInTheDocument();
});
it("global job status survives navigation and no manual job ID is required", async () => {
  const { api } = apiFor();
  const user = userEvent.setup();
  render(<ProductWorkspace api={api} />);
  await screen.findByText("Local session connected");
  await screen.findByText("Your result");
  await user.click(screen.getByRole("link", { name: /Job Center/ }));
  await screen.findByRole("heading", { name: "Job Center" });
  expect(screen.queryByLabelText(/Job ID/i)).not.toBeInTheDocument();
  expect(screen.getAllByText(/Observed ComfyUI state/).length).toBeGreaterThan(
    0,
  );
  expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
});
it("Model Store shows installed/candidate states and safe discovery text", async () => {
  const { api } = apiFor("failed");
  const user = userEvent.setup();
  render(<ProductWorkspace api={api} />);
  await screen.findByText("Local session connected");
  await user.click(screen.getByRole("link", { name: "Model Store" }));
  await screen.findByRole("heading", { name: "Model Store" });
  expect(screen.getByText("Ready for local generation")).toBeInTheDocument();
  expect(screen.getByText("Candidate · not installed")).toBeInTheDocument();
  await user.type(screen.getByLabelText("Search models"), "video");
  await user.click(screen.getByRole("button", { name: "Search" }));
  await screen.findByText("<script>test</script>");
  expect(document.querySelector("script")).toBeNull();
});
it("model switching resets controls and disables unsupported adapter", async () => {
  const { api } = apiFor();
  const user = userEvent.setup();
  render(<ProductWorkspace api={api} />);
  await screen.findByText("Local session connected");
  await waitFor(() =>
    expect(screen.getByLabelText("Model")).toHaveValue(wan.id),
  );
  await user.selectOptions(screen.getByLabelText("Model"), h3.id);
  expect(screen.getByRole("button", { name: "Generate scene" })).toBeDisabled();
  expect(screen.getByLabelText("Duration")).toHaveValue("5");
});
it("activity console filters messages and is not a terminal", async () => {
  const { api } = apiFor();
  const user = userEvent.setup();
  render(<ProductWorkspace api={api} />);
  await screen.findByText("Local session connected");
  await user.click(screen.getByRole("button", { name: "Activity console" }));
  expect(
    screen.getByRole("region", { name: "Activity console" }),
  ).toBeInTheDocument();
  await user.type(screen.getByLabelText("Search activity"), "nothing");
  expect(
    screen.getByText(/This panel does not run commands/),
  ).toBeInTheDocument();
});
it("product response guards reject wrong types and untrusted source URLs", () => {
  expect(() =>
    validateResponse(
      { models: [{ id: "x" }], production_ready: false },
      "productCatalog",
    ),
  ).toThrow();
  expect(() =>
    validateResponse(
      {
        items: [
          {
            id: "x",
            source: "javascript:alert(1)",
            license: "x",
            status: "discovered_not_runnable",
          },
        ],
        cached: false,
        message: "x",
      },
      "productDiscovery",
    ),
  ).toThrow();
  expect(() =>
    validateResponse(
      {
        jobs: [{ id, state: "running", progress: 50, message: "fake" }],
        session_only: true,
      },
      "productJobs",
    ),
  ).toThrow();
});
it("privileged product requests use only in-memory launcher marker", async () => {
  const { api, fetcher } = apiFor();
  await api.launcherSession();
  await api.productCatalog();
  expect(fetcher.mock.calls.at(-1)?.[1]?.headers).toEqual(
    expect.objectContaining({ "X-Director-Session": "launcher" }),
  );
  expect(localStorage.length).toBe(0);
});

it("shot planning retains notes across navigation and never queues inference", async () => {
  const { api, fetcher } = apiFor("failed");
  const user = userEvent.setup();
  window.location.hash = "";
  render(<ProductWorkspace api={api} />);
  await screen.findByText("Local session connected");
  await user.type(
    await screen.findByLabelText("Describe your scene"),
    "Sunset shot",
  );
  await user.click(screen.getByText("Plan a sequence of shots"));
  await user.click(
    screen.getByRole("button", { name: "Add current shot to plan" }),
  );
  await user.type(screen.getByLabelText("Continuity notes"), "Same horizon");
  expect(
    screen.getByRole("button", { name: /Continue previous shot/ }),
  ).toBeDisabled();
  await user.click(screen.getByRole("link", { name: /^Job Center/ }));
  await user.click(screen.getByRole("link", { name: "Generate" }));
  await user.click(screen.getByText("Plan a sequence of shots"));
  expect(screen.getByLabelText("Continuity notes")).toHaveValue("Same horizon");
  expect(
    fetcher.mock.calls.some(([path]) =>
      String(path).includes("/product/generation"),
    ),
  ).toBe(false);
});

it("model removal stays disabled until an explicit fresh inventory acknowledgement", async () => {
  const { api } = apiFor();
  const plan = {
    model_id: wan.id,
    files: ["only-model"],
    shared_files: ["encoder"],
    reclaim_bytes: 4,
    blockers: [],
    preserves: ["videos"],
    digest: "a".repeat(64),
  };
  vi.spyOn(api, "removalPlan").mockResolvedValue(plan);
  const remove = vi.spyOn(api, "removeModel").mockResolvedValue({
    removed: true,
    reclaimed_bytes: 4,
    shared_preserved: ["encoder"],
  });
  const changed = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(
    <ProductModelStore
      api={api}
      models={[wan]}
      disabled={false}
      useModel={vi.fn()}
      changed={changed}
      act={async (fn) => {
        await fn();
      }}
    />,
  );
  await user.click(screen.getByRole("button", { name: "Model details" }));
  await user.click(
    screen.getByRole("button", { name: "Review model removal" }),
  );
  const confirm = await screen.findByRole("button", {
    name: "Confirm model removal",
  });
  expect(confirm).toBeDisabled();
  const check = screen.getByRole("checkbox");
  expect(check).not.toBeChecked();
  await user.click(check);
  await user.click(confirm);
  expect(remove).toHaveBeenCalledWith(wan.id, plan.digest);
  expect(changed).toHaveBeenCalled();
});

it("published inventory guards reject invalid hashes and missing size metadata", () => {
  const card = {
    repository: "a/model",
    revision: "a".repeat(40),
    card_text: "Plain card",
    runnable: false,
    publisher: "a",
    license: "unknown",
    pipeline: "video",
    updated: null,
    tags: [],
    files: [{ name: "model", size: null, sha256: null }],
    repository_bytes: null,
    cached: true,
    message: "Offline",
  };
  expect(() => validateResponse(card, "productCard")).not.toThrow();
  expect(() =>
    validateResponse(
      { ...card, files: [{ name: "model", sha256: "bad", size: 4 }] },
      "productCard",
    ),
  ).toThrow();
  expect(() =>
    validateResponse(
      { ...card, files: [{ name: "model", sha256: null }] },
      "productCard",
    ),
  ).toThrow();
});
