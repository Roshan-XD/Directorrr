import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { DirectorApi, validateResponse } from "../api/client";
import type { DownloadPlan } from "../api/studio";
import { OptimizedH3Install } from "../components/product/OptimizedH3Install";
import { ProductModelStore } from "../components/product/ProductModelStore";
import type { Capability } from "../api/product";

const plan: DownloadPlan = {
  model_id: "minimax-h3-optimized",
  repository: "DmitryDB/MiniMax-H3-ComfyUI-Quants",
  revision: "06aba4816457400d1dcb12ffd77e37499c8116b1",
  variant: "FL2VA NVFP4 (non-HQ)",
  quantization: "NVFP4",
  components: [
    {
      filename: "FL2VA/MiniMax-H3_FL2VA-NVFP4.safetensors",
      expected_size_bytes: 33163649303,
      sha256: "a".repeat(64),
    },
  ],
  total_bytes: 33163649303,
  required_free_bytes: 68474782254,
  free_bytes: 100000000000,
  destination: "Owned Windows runtime/models",
  license: "H3 Community License",
  license_text: "Exact agreement and Exhibit A",
  license_sha256: "b".repeat(64),
  license_source:
    "https://huggingface.co/DmitryDB/MiniMax-H3-ComfyUI-Quants/blob/06aba4816457400d1dcb12ffd77e37499c8116b1/LICENSE",
  license_conditions: ["Confirm applicable territory"],
  blockers: [],
  warnings: ["32 GB RAM is experimental"],
  runnable: false,
  digest: "c".repeat(64),
};

it("requires explicit unchecked consent and confirmation, then shows the real queued transfer", async () => {
  const api = new DirectorApi("/api");
  vi.spyOn(api, "downloadPlan").mockResolvedValue(plan);
  const start = vi.spyOn(api, "startDownload").mockResolvedValue({
    id: "d".repeat(32),
    repository: plan.repository,
    revision: plan.revision,
    state: "queued",
    message: "Explicitly confirmed",
    candidate_bytes: 0,
    verified_bytes: 0,
    total_bytes: plan.total_bytes,
    created: "now",
    plan,
    runnable: false,
  });
  vi.spyOn(api, "downloads").mockResolvedValue({
    jobs: [],
    real_downloads_enabled: false,
  });
  render(<OptimizedH3Install api={api} changed={vi.fn()} />);
  const user = userEvent.setup();
  expect(start).not.toHaveBeenCalled();
  await user.click(
    screen.getByRole("button", { name: "Install MiniMax H3 Optimized" }),
  );
  const checkbox = await screen.findByRole("checkbox");
  expect(checkbox).not.toBeChecked();
  const confirm = screen.getByRole("button", { name: /Confirm \/ Install/ });
  expect(confirm).toBeDisabled();
  expect(
    screen.getByText(new RegExp(plan.total_bytes.toLocaleString() + " bytes")),
  ).toBeVisible();
  await user.click(checkbox);
  await user.click(confirm);
  expect(start).toHaveBeenCalledExactlyOnceWith(plan);
  expect(
    await screen.findByText(/queued — Explicitly confirmed/),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: "Cancel installation" }),
  ).toBeEnabled();
});

it("never starts an installation with backend blockers", async () => {
  const api = new DirectorApi("/api");
  vi.spyOn(api, "downloadPlan").mockResolvedValue({
    ...plan,
    blockers: ["Not enough disk"],
  });
  const start = vi.spyOn(api, "startDownload");
  render(<OptimizedH3Install api={api} changed={vi.fn()} />);
  const user = userEvent.setup();
  await user.click(
    screen.getByRole("button", { name: "Install MiniMax H3 Optimized" }),
  );
  await user.click(await screen.findByRole("checkbox"));
  expect(
    screen.getByRole("button", { name: /Confirm \/ Install/ }),
  ).toBeDisabled();
  expect(start).not.toHaveBeenCalled();
});

it("keeps the friendly failure and exposes worker evidence in Technical Details", async () => {
  const api = new DirectorApi("/api");
  vi.spyOn(api, "downloadPlan").mockResolvedValue(plan);
  vi.spyOn(api, "startDownload").mockResolvedValue({
    id: "d".repeat(32),
    repository: plan.repository,
    revision: plan.revision,
    state: "failed",
    message: "Transfer failed; check access, connection and SDK setup",
    technical_details:
      "LocalEntryNotFoundError: Caused by OfflineModeIsEnabled",
    candidate_bytes: 0,
    verified_bytes: 0,
    total_bytes: plan.total_bytes,
    created: "now",
    plan,
    runnable: false,
  });
  vi.spyOn(api, "downloads").mockResolvedValue({
    jobs: [],
    real_downloads_enabled: false,
  });
  render(<OptimizedH3Install api={api} changed={vi.fn()} />);
  const user = userEvent.setup();
  await user.click(
    screen.getByRole("button", { name: "Install MiniMax H3 Optimized" }),
  );
  await user.click(await screen.findByRole("checkbox"));
  await user.click(screen.getByRole("button", { name: /Confirm \/ Install/ }));
  expect(await screen.findByText(/failed — Transfer failed/)).toBeVisible();
  await user.click(screen.getByText("Technical Details"));
  expect(screen.getByText(/LocalEntryNotFoundError/)).toBeVisible();
});

it("shows Install directly on the optimized model card and Use model only when ready", () => {
  const api = new DirectorApi("/api");
  const model = {
    id: "minimax-h3-optimized",
    name: "MiniMax H3 Optimized",
    repository: plan.repository,
    workspaces: ["text-to-video"],
    native_audio: true,
    model_bytes: 0,
    installed: false,
    runnable: false,
    adapter: "minimax-h3-native-v1",
  } as Capability;
  const props = {
    api,
    models: [model],
    disabled: false,
    useModel: vi.fn(),
    changed: vi.fn(),
    act: vi.fn(),
  };
  const view = render(<ProductModelStore {...props} />);
  expect(
    screen.getByRole("button", { name: "Install MiniMax H3 Optimized" }),
  ).toBeEnabled();
  expect(screen.getByRole("button", { name: "Use model" })).toBeDisabled();
  view.rerender(
    <ProductModelStore
      {...props}
      models={[{ ...model, installed: true, runnable: true }]}
    />,
  );
  expect(
    screen.queryByRole("button", { name: "Install MiniMax H3 Optimized" }),
  ).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Use model" })).toBeEnabled();
});

it("guards optimized metadata and accepts authenticated completed MP4 responses through the client", () => {
  expect(validateResponse(plan, "productDownloadPlan")).toEqual(plan);
  expect(() =>
    validateResponse({ ...plan, free_bytes: "unknown" }, "productDownloadPlan"),
  ).toThrow();
  expect(
    validateResponse(
      {
        id: "a".repeat(32),
        repository: plan.repository,
        revision: plan.revision,
        state: "installing",
        message: "Registering",
        total_bytes: plan.total_bytes,
        verified_bytes: plan.total_bytes,
        candidate_bytes: plan.total_bytes,
        plan,
        runnable: false,
      },
      "productDownloadJob",
    ),
  ).toBeTruthy();
});
