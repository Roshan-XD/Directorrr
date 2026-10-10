import { studioResponse } from "./studio";
import { h3Response } from "./h3";
export type Workspace =
  | "text-to-video"
  | "image-to-video"
  | "reference-to-video"
  | "first-last-frame"
  | "sequence"
  | "video-to-video"
  | "text-to-image"
  | "image-to-image"
  | "reference-image"
  | "inpainting"
  | "audio-conditioned-video";
export interface Capability {
  id: string;
  name: string;
  repository: string;
  manifest_id?: string | null;
  license_source: string;
  adapter: string | null;
  workspaces: Workspace[];
  native_audio: boolean;
  continuation: string;
  fps: number;
  frame_multiple: number;
  frame_offset: number;
  durations: { seconds: number; frames: number }[];
  resolutions: { id: string; width: number; height: number; aspect: string }[];
  qualities: Record<string, number>;
  default_resolution: string;
  default_duration: number;
  evidence: string[];
  blockers: string[];
  installed: boolean;
  runnable: boolean;
  model_bytes: number;
  installation_status: string;
  compatibility: string;
}
export interface CreativeRequest {
  model_id: string;
  workspace: Workspace;
  prompt: string;
  resolution: string;
  duration: number;
  quality: string;
  seed: number | null;
  camera: string;
  steps?: number;
  cfg: number;
  shift: number;
  negative_prompt: string;
  export_fps: number;
}
export type ProductJob = import("./types").GenerationJob & {
  creative?: CreativeRequest & {
    width: number;
    height: number;
    frames: number;
    fps: number;
  };
  tracking_warning?: string;
};
export interface Catalog {
  models: Capability[];
  production_ready: false;
}
export interface DiscoveryResult {
  items: {
    id: string;
    title: string;
    source: string;
    license: string;
    pipeline: string;
    downloads: number | null;
    status: string;
    gated?: boolean;
    likes?: number | null;
    license_state?: string;
    updated?: string | null;
    revision: string | null;
  }[];
  cached: boolean;
  next_cursor?: string | null;
  message: string;
}
export interface ModelCard {
  repository: string;
  revision: string;
  card_text: string;
  runnable: false;
  publisher: string;
  license: string;
  pipeline: string;
  updated: string | null;
  tags: string[];
  files: { name: string; size: number | null; sha256: string | null }[];
  repository_bytes: number | null;
  cached: boolean;
  message: string;
}
export interface StorageReport {
  categories: Record<
    string,
    { bytes: number; complete: boolean; warnings: string[] }
  >;
  free_bytes: number;
  low_disk: boolean;
  cleanup_policy: string;
  cache_cleanup_enabled: false;
  unknown_files_are_not_deletion_targets: true;
}
export interface RemovalPlan {
  model_id: string;
  files: string[];
  shared_files: string[];
  reclaim_bytes: number;
  blockers: string[];
  preserves: string[];
  digest: string;
}
export interface ConsoleReport {
  events: {
    time: string;
    stage: string;
    message: string;
    level: string;
    count?: number;
  }[];
}
const obj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null;
const strings = (v: unknown) =>
  Array.isArray(v) && v.every((x) => typeof x === "string");
const number = (v: unknown): v is number =>
  typeof v === "number" && Number.isFinite(v) && v >= 0;
export function productResponse(data: unknown, kind: string): boolean {
  if (!obj(data)) return false;
  if (studioResponse(data, kind)) return true;
  if (h3Response(data, kind)) return true;
  if (kind === "productCatalog")
    return (
      data.production_ready === false &&
      Array.isArray(data.models) &&
      data.models.every(
        (m) =>
          obj(m) &&
          typeof m.id === "string" &&
          typeof m.name === "string" &&
          typeof m.repository === "string" &&
          typeof m.license_source === "string" &&
          (m.adapter === null || typeof m.adapter === "string") &&
          strings(m.workspaces) &&
          strings(m.blockers) &&
          strings(m.evidence) &&
          typeof m.runnable === "boolean" &&
          typeof m.installed === "boolean" &&
          number(m.model_bytes) &&
          number(m.fps) &&
          number(m.default_duration) &&
          typeof m.default_resolution === "string" &&
          obj(m.qualities) &&
          Object.values(m.qualities).every(number) &&
          Array.isArray(m.resolutions) &&
          m.resolutions.every(
            (r) =>
              obj(r) &&
              typeof r.id === "string" &&
              number(r.width) &&
              number(r.height) &&
              typeof r.aspect === "string",
          ) &&
          Array.isArray(m.durations) &&
          m.durations.every(
            (d) => obj(d) && number(d.seconds) && number(d.frames),
          ) &&
          typeof m.native_audio === "boolean",
      )
    );
  if (kind === "productJobs")
    return (
      data.session_only === true &&
      Array.isArray(data.jobs) &&
      data.jobs.every(
        (j) =>
          obj(j) &&
          typeof j.id === "string" &&
          /^[0-9a-f]{32}$/.test(j.id) &&
          ["queued", "running", "completed", "failed", "cancelled"].includes(
            String(j.state),
          ) &&
          typeof j.message === "string" &&
          (j.progress === null || (number(j.progress) && j.progress <= 1)),
      )
    );
  if (kind === "productDiscovery")
    return (
      typeof data.cached === "boolean" &&
      typeof data.message === "string" &&
      Array.isArray(data.items) &&
      data.items.every(
        (i) =>
          obj(i) &&
          typeof i.id === "string" &&
          typeof i.source === "string" &&
          /^https:\/\/huggingface\.co\/[-\w.]+\/[-\w.]+$/.test(i.source) &&
          typeof i.license === "string" &&
          i.status === "discovered_not_runnable",
      )
    );
  if (kind === "productStorage")
    return (
      obj(data.categories) &&
      Object.values(data.categories).every(
        (c) =>
          obj(c) &&
          number(c.bytes) &&
          typeof c.complete === "boolean" &&
          strings(c.warnings),
      ) &&
      number(data.free_bytes) &&
      typeof data.low_disk === "boolean" &&
      typeof data.cleanup_policy === "string" &&
      data.cache_cleanup_enabled === false
    );
  if (kind === "productRemoval")
    return (
      typeof data.model_id === "string" &&
      strings(data.files) &&
      strings(data.shared_files) &&
      strings(data.blockers) &&
      strings(data.preserves) &&
      number(data.reclaim_bytes) &&
      typeof data.digest === "string" &&
      /^[0-9a-f]{64}$/.test(data.digest)
    );
  if (kind === "productCard")
    return (
      typeof data.repository === "string" &&
      typeof data.revision === "string" &&
      /^[0-9a-f]{40}$/.test(data.revision) &&
      typeof data.card_text === "string" &&
      data.card_text.length <= 128 * 1024 &&
      data.runnable === false &&
      typeof data.publisher === "string" &&
      typeof data.license === "string" &&
      typeof data.pipeline === "string" &&
      (data.updated === null || typeof data.updated === "string") &&
      strings(data.tags) &&
      (data.repository_bytes === null || number(data.repository_bytes)) &&
      typeof data.cached === "boolean" &&
      typeof data.message === "string" &&
      Array.isArray(data.files) &&
      data.files.length <= 1000 &&
      data.files.every(
        (file) =>
          obj(file) &&
          typeof file.name === "string" &&
          (file.size === null || number(file.size)) &&
          (file.sha256 === null ||
            (typeof file.sha256 === "string" &&
              /^[0-9a-f]{64}$/.test(file.sha256))),
      )
    );
  if (kind === "productInstallJobs")
    return (
      Array.isArray(data.jobs) &&
      data.jobs.every(
        (j) =>
          obj(j) &&
          typeof j.id === "string" &&
          /^[0-9a-f]{32}$/.test(j.id) &&
          typeof j.model_id === "string" &&
          typeof j.state === "string" &&
          number(j.total_expected_bytes) &&
          number(j.verified_bytes) &&
          number(j.candidate_bytes),
      )
    );
  if (kind === "productCachePlan")
    return (
      strings(data.files) &&
      strings(data.blockers) &&
      strings(data.shared_preserved) &&
      number(data.reclaim_bytes) &&
      data.unknown_files_preserved === true &&
      typeof data.digest === "string" &&
      /^[0-9a-f]{64}$/.test(data.digest)
    );
  if (kind === "productConsole")
    return (
      Array.isArray(data.events) &&
      data.events.every(
        (e) =>
          obj(e) &&
          ["time", "stage", "message", "level"].every(
            (k) => typeof e[k] === "string",
          ),
      )
    );
  if (kind === "productForgot")
    return data.forgotten === true && data.output_deleted === false;
  if (kind === "productRemoved")
    return (
      data.removed === true &&
      number(data.reclaimed_bytes) &&
      strings(data.shared_preserved)
    );
  if (kind === "productClear") return data.cleared === true;
  return false;
}
