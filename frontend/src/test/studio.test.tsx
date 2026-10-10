import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, expect, vi, beforeEach } from "vitest";
import { DirectorApi, validateResponse } from "../api/client";
import { AssetLibrary } from "../components/product/AssetLibrary";
import { ProjectTools } from "../components/product/ProjectTools";
import { DownloadCenter } from "../components/product/DownloadCenter";
import { ProductModelStore } from "../components/product/ProductModelStore";
import type { Asset, Studio, DownloadPlan } from "../api/studio";
const id = "a".repeat(32);
const asset: Asset = {
  id,
  title: "Ocean",
  filename: "scene.webm",
  type: "video",
  origin: "output",
  created: "now",
  bytes: 4,
  sha256: "a".repeat(64),
  extension: ".webm",
  project_id: id,
  job_id: id,
  model_id: "wan21-t2v-13b",
  favorite: false,
  width: 320,
  height: 192,
  duration: 1.0625,
  codec: "vp9",
  thumbnail: true,
};
const studio: Studio = {
  version: 1,
  current: id,
  projects: [
    {
      id,
      name: "Development",
      updated: "now",
      draft: {},
      shots: [],
      favorites: [],
      presets: [],
      references: [],
    },
  ],
  media: [asset],
  history: [],
};
beforeEach(() => {
  URL.createObjectURL = vi.fn(() => "blob:fixture");
  URL.revokeObjectURL = vi.fn();
});
function api() {
  const value = new DirectorApi("/api", 1000, vi.fn());
  value.setKey("a".repeat(40));
  vi.spyOn(value, "libraryFile").mockResolvedValue(
    new Blob(["safe"], { type: "video/webm" }),
  );
  return value;
}
it("guards Library, projects and data-only download contracts", () => {
  expect(validateResponse(studio, "productStudio")).toEqual(studio);
  expect(() =>
    validateResponse(
      { ...studio, media: [{ ...asset, sha256: "wrong" }] },
      "productStudio",
    ),
  ).toThrow();
  expect(() =>
    validateResponse(
      {
        jobs: [{ state: "completed", runnable: true }],
        real_downloads_enabled: false,
      },
      "productDownloads",
    ),
  ).toThrow();
});
it("shows managed metadata, previews and explicit Library-copy deletion", async () => {
  const value = api();
  const remove = vi
    .spyOn(value, "deleteAsset")
    .mockResolvedValue({ deleted: true });
  const user = userEvent.setup();
  render(
    <AssetLibrary
      api={value}
      studio={studio}
      refresh={vi.fn().mockResolvedValue(undefined)}
    />,
  );
  await user.click(screen.getByRole("button", { name: "Open Ocean" }));
  expect(
    screen.getByRole("button", { name: "Delete Library copy" }),
  ).toBeDisabled();
  await user.click(
    screen.getByRole("checkbox", { name: /Remove only this Library copy/ }),
  );
  await user.click(screen.getByRole("button", { name: "Delete Library copy" }));
  expect(remove).toHaveBeenCalledWith(id);
});
it("explains unsupported image-to-video handoff instead of requesting inference", async () => {
  const value = api();
  vi.spyOn(value, "assetHandoffs").mockResolvedValue({
    actions: [],
    message: "Wan T2V cannot accept a reference.",
  });
  const generation = vi.spyOn(value, "creativeGenerate");
  const user = userEvent.setup();
  render(
    <AssetLibrary
      api={value}
      studio={{
        ...studio,
        media: [{ ...asset, type: "image", filename: "character.png" }],
      }}
      refresh={vi.fn()}
    />,
  );
  await user.click(screen.getByRole("button", { name: "Open Ocean" }));
  await user.click(
    screen.getByRole("button", { name: "Animate / use as reference" }),
  );
  expect(
    await screen.findByText(/No compatible installed adapter/),
  ).toBeInTheDocument();
  expect(generation).not.toHaveBeenCalled();
});
it("filters Library by media and favorites without deleting originals", async () => {
  const value = api();
  render(<AssetLibrary api={value} studio={studio} refresh={vi.fn()} />);
  const user = userEvent.setup();
  await user.selectOptions(
    screen.getByRole("combobox", { name: "Library type" }),
    "image",
  );
  expect(
    screen.queryByRole("button", { name: "Open Ocean" }),
  ).not.toBeInTheDocument();
  expect(screen.getByText("A home for every scene")).toBeInTheDocument();
});
it("saves a named project and never starts generation", async () => {
  const save = vi.fn().mockResolvedValue(undefined);
  render(<ProjectTools studio={studio} save={save} restore={vi.fn()} />);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Project name"), "Film one");
  await user.click(screen.getByRole("button", { name: "New project" }));
  expect(save).toHaveBeenCalledWith(
    expect.objectContaining({ name: "Film one", references: [], shots: [] }),
  );
});
it("shows persistent download progress and cancellation", async () => {
  const value = api();
  const plan: DownloadPlan = {
    repository: "example/data",
    revision: "a".repeat(40),
    components: [],
    total_bytes: 10,
    required_free_bytes: 20,
    destination: "owned",
    license: "mit",
    license_text: "terms",
    license_sha256: "a".repeat(64),
    blockers: [],
    warnings: [],
    runnable: false,
    digest: "a".repeat(64),
  };
  const job = {
    id,
    repository: "example/data",
    revision: plan.revision,
    state: "downloading",
    message: "Downloading 1/1",
    candidate_bytes: 5,
    verified_bytes: 0,
    total_bytes: 10,
    created: "now",
    plan,
    runnable: false as const,
  };
  vi.spyOn(value, "downloads").mockResolvedValue({
    jobs: [job],
    real_downloads_enabled: false,
  });
  const cancel = vi.spyOn(value, "cancelDownload").mockResolvedValue(job);
  render(<DownloadCenter api={value} />);
  expect(await screen.findByText("Downloading 1/1")).toBeInTheDocument();
  expect(screen.getByRole("progressbar")).toHaveAttribute("value", "0");
  await userEvent.click(
    screen.getByRole("button", { name: "Cancel download" }),
  );
  expect(cancel).toHaveBeenCalledWith(id);
});
it("upload sends only raw media with privileged session auth and guards the response", async () => {
  const fetcher = vi.fn(
    async (_input: string | URL | Request, _options?: RequestInit) =>
      Response.json(asset),
  );
  const value = new DirectorApi("/api", 1000, fetcher);
  value.setKey("b".repeat(40));
  const file = new File(["safe"], "scene.webm");
  await value.uploadAsset(file);
  const options = fetcher.mock.calls[0][1] as RequestInit;
  expect(options.body).toBe(file);
  expect(options.headers).toMatchObject({
    "X-Director-Key": "b".repeat(40),
    "Content-Type": "application/octet-stream",
  });
});

it("reviews selected metadata but cannot start a blocked download", async () => {
  const value = api();
  const user = userEvent.setup();
  vi.spyOn(value, "discover").mockResolvedValue({
    items: [
      {
        id: "example/data",
        title: "example/data",
        source: "https://huggingface.co/example/data",
        license: "mit",
        pipeline: "text-to-image",
        downloads: 1,
        status: "discovered_not_runnable",
        revision: "a".repeat(40),
      },
    ],
    cached: false,
    message: "Live metadata",
  });
  vi.spyOn(value, "modelCard").mockResolvedValue({
    repository: "example/data",
    revision: "a".repeat(40),
    card_text: "Terms",
    runnable: false,
    publisher: "example",
    license: "mit",
    pipeline: "text-to-image",
    updated: null,
    tags: [],
    files: [{ name: "model.safetensors", size: 10, sha256: "a".repeat(64) }],
    repository_bytes: 10,
    cached: false,
    message: "Metadata",
  });
  vi.spyOn(value, "downloadPlan").mockResolvedValue({
    repository: "example/data",
    revision: "a".repeat(40),
    components: [
      {
        filename: "model.safetensors",
        expected_size_bytes: 10,
        sha256: "a".repeat(64),
      },
    ],
    total_bytes: 10,
    required_free_bytes: 20,
    destination: "owned",
    license: "mit",
    license_text: "Terms",
    license_sha256: "a".repeat(64),
    blockers: ["Real downloads disabled"],
    warnings: [],
    runnable: false,
    digest: "a".repeat(64),
  });
  const start = vi.spyOn(value, "startDownload");
  render(
    <ProductModelStore
      api={value}
      models={[]}
      disabled={false}
      useModel={vi.fn()}
      changed={vi.fn()}
      act={async (fn) => {
        await fn();
      }}
    />,
  );
  await user.type(screen.getByLabelText("Search models"), "data");
  await user.click(screen.getByRole("button", { name: /^Search$/ }));
  await user.click(
    await screen.findByRole("button", { name: "Read published model card" }),
  );
  await user.click(
    await screen.findByText("Select exact files for a data-only download plan"),
  );
  await user.click(screen.getByRole("checkbox", { name: /model.safetensors/ }));
  await user.click(
    screen.getByRole("button", { name: "Review selected download" }),
  );
  expect(
    await screen.findByRole("button", { name: "Confirm download" }),
  ).toBeDisabled();
  const check = screen.getByRole("checkbox", {
    name: /I reviewed the pinned files/,
  });
  expect(check).not.toBeChecked();
  await user.click(check);
  expect(
    screen.getByRole("button", { name: "Confirm download" }),
  ).toBeDisabled();
  expect(start).not.toHaveBeenCalled();
});
