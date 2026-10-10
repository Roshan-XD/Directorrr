import type { CreativeRequest, ProductJob } from "./product";
export interface Project {
  id: string;
  name: string;
  updated: string;
  draft: Partial<CreativeRequest>;
  shots: import("../components/product/ShotPlanner").PlannedShot[];
  favorites: string[];
  presets: { name: string; settings: CreativeRequest }[];
  references: string[];
}
export interface Asset {
  id: string;
  title: string;
  filename: string;
  type: "image" | "video" | "audio";
  origin: "input" | "output";
  created: string;
  bytes: number;
  sha256: string;
  extension: string;
  project_id: string;
  job_id: string | null;
  model_id: string | null;
  favorite: boolean;
  width: number | null;
  height: number | null;
  duration: number | null;
  codec: string | null;
  thumbnail: boolean;
}
export interface Studio {
  version: 1;
  current: string;
  projects: Project[];
  media: Asset[];
  history: (ProductJob & {
    created: string;
    updated: string;
    project_id: string;
  })[];
}
export interface DownloadPlan {
  model_id?: "minimax-h3-optimized";
  variant?: string;
  quantization?: string;
  free_bytes?: number;
  license_source?: string;
  license_conditions?: string[];
  encoder_license?: {
    name: string;
    source: string;
    sha256: string;
    text: string;
  };
  repository: string;
  revision: string;
  components: {
    filename: string;
    expected_size_bytes: number | null;
    sha256: string | null;
  }[];
  total_bytes: number;
  required_free_bytes: number;
  destination: string;
  license: string;
  license_text: string | null;
  license_sha256: string | null;
  blockers: string[];
  warnings: string[];
  runnable: false;
  digest: string;
}
export interface DownloadJob {
  technical_details?: string;
  speed_bytes_per_second?: number | null;
  eta_seconds?: number | null;
  id: string;
  repository: string;
  revision: string;
  state: string;
  message: string;
  candidate_bytes: number;
  verified_bytes: number;
  total_bytes: number;
  created: string;
  plan: DownloadPlan;
  runnable: false;
}
export interface Downloads {
  jobs: DownloadJob[];
  real_downloads_enabled: boolean;
}
const obj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null;
export interface DownloadRemoval {
  job_id: string;
  files: { name: string; bytes: number; sha256: string }[];
  reclaim_bytes: number;
  preserves: string[];
  digest: string;
}
export interface ModelFiles {
  model_id: string;
  location: string;
  files: {
    path: string;
    bytes: number;
    sha256: string;
    present: boolean;
    shared_with: string[];
  }[];
  expected_assets: string[];
  last_used: string | null;
  integrity: string;
}
const id = (v: unknown) => typeof v === "string" && /^[0-9a-f]{32}$/.test(v);
const size = (v: unknown) =>
  typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
const strings = (v: unknown) =>
  Array.isArray(v) && v.every((x) => typeof x === "string");
const hash = (v: unknown) => typeof v === "string" && /^[0-9a-f]{64}$/.test(v);
export const assetGuard = (v: unknown) =>
  obj(v) &&
  id(v.id) &&
  typeof v.title === "string" &&
  typeof v.filename === "string" &&
  ["image", "video", "audio"].includes(String(v.type)) &&
  typeof v.favorite === "boolean" &&
  typeof v.thumbnail === "boolean" &&
  size(v.bytes) &&
  hash(v.sha256) &&
  id(v.project_id);
const planGuard = (v: unknown) =>
  obj(v) &&
  hash(v.digest) &&
  (v.model_id === undefined ||
    (v.model_id === "minimax-h3-optimized" &&
      typeof v.variant === "string" &&
      typeof v.quantization === "string" &&
      size(v.free_bytes) &&
      strings(v.license_conditions) &&
      typeof v.license_source === "string" &&
      v.license_source.startsWith(
        "https://huggingface.co/DmitryDB/MiniMax-H3-ComfyUI-Quants/blob/",
      ))) &&
  v.runnable === false &&
  typeof v.repository === "string" &&
  typeof v.revision === "string" &&
  /^[0-9a-f]{40}$/.test(v.revision) &&
  strings(v.blockers) &&
  strings(v.warnings) &&
  size(v.total_bytes) &&
  size(v.required_free_bytes) &&
  typeof v.destination === "string" &&
  typeof v.license === "string" &&
  (v.license_text === null || typeof v.license_text === "string") &&
  (v.license_sha256 === null || hash(v.license_sha256)) &&
  Array.isArray(v.components) &&
  v.components.every(
    (c) =>
      obj(c) &&
      typeof c.filename === "string" &&
      (c.expected_size_bytes === null || size(c.expected_size_bytes)) &&
      (c.sha256 === null || hash(c.sha256)),
  );
const jobGuard = (v: unknown) =>
  obj(v) &&
  id(v.id) &&
  v.runnable === false &&
  [
    "queued",
    "downloading",
    "verifying",
    "installing",
    "completed",
    "failed",
    "cancelled",
  ].includes(String(v.state)) &&
  typeof v.message === "string" &&
  (v.technical_details === undefined ||
    typeof v.technical_details === "string") &&
  size(v.total_bytes) &&
  size(v.verified_bytes) &&
  size(v.candidate_bytes) &&
  planGuard(v.plan);
export function studioResponse(
  data: Record<string, unknown>,
  kind: string,
): boolean {
  if (kind === "productStudio")
    return (
      data.version === 1 &&
      id(data.current) &&
      Array.isArray(data.projects) &&
      data.projects.length <= 50 &&
      data.projects.every(
        (p) =>
          obj(p) &&
          id(p.id) &&
          typeof p.name === "string" &&
          obj(p.draft) &&
          Array.isArray(p.shots) &&
          strings(p.favorites) &&
          strings(p.references) &&
          Array.isArray(p.presets),
      ) &&
      Array.isArray(data.media) &&
      data.media.length <= 500 &&
      data.media.every(assetGuard) &&
      Array.isArray(data.history) &&
      data.history.every(
        (j) => obj(j) && id(j.id) && typeof j.state === "string",
      )
    );
  if (kind === "productAsset") return assetGuard(data);
  if (kind === "productModelFiles")
    return (
      typeof data.model_id === "string" &&
      typeof data.location === "string" &&
      strings(data.expected_assets) &&
      Array.isArray(data.files) &&
      data.files.every(
        (f) =>
          obj(f) &&
          typeof f.path === "string" &&
          size(f.bytes) &&
          hash(f.sha256) &&
          typeof f.present === "boolean" &&
          strings(f.shared_with),
      )
    );
  if (kind === "productModelVerified")
    return (
      typeof data.valid === "boolean" &&
      Array.isArray(data.reports) &&
      data.generation_validated === false
    );
  if (kind === "productModelUpdates")
    return (
      Array.isArray(data.components) &&
      data.replacement_allowed === false &&
      typeof data.message === "string"
    );
  if (kind === "productDownloadRemoval")
    return (
      id(data.job_id) &&
      hash(data.digest) &&
      size(data.reclaim_bytes) &&
      strings(data.preserves) &&
      Array.isArray(data.files) &&
      data.files.every(
        (f) =>
          obj(f) &&
          typeof f.name === "string" &&
          size(f.bytes) &&
          hash(f.sha256),
      )
    );
  if (kind === "productAssetDeleted")
    return data.deleted === true && data.original_generation_preserved === true;
  if (kind === "productRevealed") return data.revealed === true;
  if (kind === "productRecovered")
    return size(data.imported) && data.original_files_preserved === true;
  if (kind === "productHandoffs")
    return (
      typeof data.message === "string" &&
      Array.isArray(data.actions) &&
      data.actions.every(
        (a) =>
          obj(a) &&
          typeof a.model_id === "string" &&
          typeof a.model_name === "string" &&
          typeof a.workspace === "string",
      )
    );
  if (kind === "productDownloadPlan") return planGuard(data);
  if (kind === "productDownloadJob") return jobGuard(data);
  if (kind === "productDownloads")
    return (
      typeof data.real_downloads_enabled === "boolean" &&
      Array.isArray(data.jobs) &&
      data.jobs.every(jobGuard)
    );
  return false;
}
