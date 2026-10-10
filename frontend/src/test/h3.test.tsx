import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { DirectorApi, validateResponse } from "../api/client";
import type { H3Plan } from "../api/h3";
import { H3InstallReview } from "../components/product/H3InstallReview";

const revision = "42ed227ee7df40d41602854ae760620d6eb651fe";
const plan: H3Plan = {
  repository: "MiniMaxAI/MiniMax-H3",
  revision,
  workflow: "t2va",
  runtime: "diffusers-modular",
  runtime_version: "0.41.0",
  download_bytes: 144039659327,
  installed_payload_bytes: 144039659327,
  required_free_bytes: 442856396221,
  free_bytes: 145000000000,
  destination: "Owned H3 candidate",
  license: "MiniMax H3 Community License",
  license_source: `https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/${revision}/LICENSE`,
  license_sha256: "a".repeat(64),
  license_conditions: ["Territory restrictions apply"],
  memory_guidance_bytes: 75000000000,
  memory_source:
    "https://huggingface.co/docs/diffusers/v0.41.0/api/pipelines/minimax_h3#memory",
  hardware: {
    ram_bytes: 32 * 1024 ** 3,
    available_ram_gb: 14,
    gpus: [
      { name: "RTX 5080", vendor: "nvidia", vram_gb: 16, is_estimate: false },
    ],
  },
  files: [
    {
      filename: "LICENSE",
      expected_size_bytes: 17604,
      sha256: null,
      git_blob_sha1: "b".repeat(40),
      destination: "LICENSE",
      url: `https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/${revision}/LICENSE`,
    },
  ],
  blockers: [
    "Host RAM is below the documented working set",
    "Insufficient disk",
  ],
  warnings: ["Audio must be preserved"],
  state: "not_installed",
  can_install: false,
  ready: false,
  digest: "c".repeat(64),
};

it("Install opens a real preflight without accepting terms or transferring data", async () => {
  const api = new DirectorApi("/api");
  const review = vi.spyOn(api, "h3InstallationPlan").mockResolvedValue(plan);
  const download = vi.spyOn(api, "startDownload");
  const user = userEvent.setup();
  render(<H3InstallReview api={api} />);
  expect(review).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "Install MiniMax H3" }));
  expect(
    await screen.findByRole("region", {
      name: "MiniMax H3 installation review",
    }),
  ).toBeVisible();
  expect(
    screen.getByText(new RegExp(plan.download_bytes.toLocaleString())),
  ).toBeVisible();
  expect(screen.getByText("Insufficient disk")).toBeVisible();
  const acknowledgement = screen.getByRole("checkbox");
  expect(acknowledgement).not.toBeChecked();
  await user.click(acknowledgement);
  expect(
    screen.getByRole("button", { name: /Download unavailable/ }),
  ).toBeDisabled();
  expect(download).not.toHaveBeenCalled();
  await user.click(
    screen.getByRole("button", { name: "Close installation review" }),
  );
  expect(screen.queryByRole("region")).not.toBeInTheDocument();
});

it("shows plan request failures without using a fake plan", async () => {
  const api = new DirectorApi("/api");
  vi.spyOn(api, "h3InstallationPlan").mockRejectedValue(
    new Error("Director unavailable"),
  );
  render(<H3InstallReview api={api} />);
  await userEvent.click(
    screen.getByRole("button", { name: "Install MiniMax H3" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Director unavailable",
  );
  expect(screen.queryByRole("region")).not.toBeInTheDocument();
});

it("guards official identity, paths, hardware and false readiness", () => {
  expect(() => validateResponse(plan, "productH3Plan")).not.toThrow();
  for (const changes of [
    { ready: true },
    { repository: "other/H3" },
    { revision: "b".repeat(40) },
    { hardware: {} },
    { license_source: "javascript:alert(1)" },
    { can_install: true },
  ]) {
    expect(() =>
      validateResponse({ ...plan, ...changes }, "productH3Plan"),
    ).toThrow();
  }
});
