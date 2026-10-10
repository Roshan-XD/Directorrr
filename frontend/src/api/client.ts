import { productResponse } from "./product";
import type {
  Catalog,
  CreativeRequest,
  ProductJob,
  DiscoveryResult,
  ModelCard,
  StorageReport,
  RemovalPlan,
  ConsoleReport,
} from "./product";
import type {
  GenerationJob,
  RuntimeReport,
  HardwareProfile,
  ModelsResponse,
  InstallationPlan,
  InstallationStatus,
  InstallationJob,
  LicenseRequirements,
  Acknowledgement,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public status = 0,
    public code = "request_failed",
  ) {
    super(message);
  }
}

// Basic runtime guards catch a wrong server/HTML proxy response without pretending
// TypeScript types alone validate JSON. The backend remains the schema authority.
const object = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;
const strings = (value: unknown) =>
  Array.isArray(value) && value.every((item) => typeof item === "string");
const quantity = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value) && value >= 0;
const nullableQuantity = (value: unknown) => value === null || quantity(value);
const nullableText = (value: unknown) =>
  value === null || typeof value === "string";
const observation = (value: unknown) =>
  object(value) &&
  [
    "installed",
    "not_detected",
    "unknown",
    "not_tested",
    "not_configured",
  ].includes(String(value.status)) &&
  nullableText(value.version) &&
  typeof value.source === "string" &&
  typeof value.detail === "string";
const runtimeReport = (data: Record<string, unknown>) =>
  typeof data.operating_system === "string" &&
  typeof data.architecture === "string" &&
  ["python", "pytorch", "comfyui", "cuda_toolkit", "driver_cuda"].every((key) =>
    observation(data[key]),
  ) &&
  Array.isArray(data.gpu_drivers) &&
  data.gpu_drivers.every(
    (gpu) =>
      object(gpu) &&
      typeof gpu.name === "string" &&
      ["nvidia", "amd", "intel", "unknown"].includes(String(gpu.vendor)) &&
      observation(gpu.driver),
  ) &&
  strings(data.missing_prerequisites) &&
  strings(data.unresolved_questions) &&
  strings(data.warnings) &&
  ["incomplete", "unknown"].includes(String(data.readiness)) &&
  data.gpu_execution === "not_tested" &&
  data.generation_ready === false;
const digest = (value: unknown) =>
  typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
const id = (value: unknown) =>
  typeof value === "string" && /^[0-9a-f]{32}$/.test(value);
const licenseInfo = (value: unknown) =>
  value === null ||
  (object(value) &&
    typeof value.identifier === "string" &&
    nullableText(value.source) &&
    strings(value.usage_restrictions) &&
    strings(value.acknowledgement_requirements));
const artifactReview = (value: unknown) =>
  value === undefined ||
  value === null ||
  (object(value) &&
    typeof value.can_review === "boolean" &&
    Array.isArray(value.blockers) &&
    value.blockers.every(
      (issue) =>
        object(issue) &&
        typeof issue.code === "string" &&
        typeof issue.message === "string",
    ) &&
    nullableQuantity(value.expected_download_bytes) &&
    nullableQuantity(value.required_storage_bytes) &&
    typeof value.destination_template === "string" &&
    value.requires_acknowledgement === true &&
    value.requires_manager_key === true &&
    value.generation_ready === false &&
    (!value.can_review ||
      (value.blockers.length === 0 &&
        quantity(value.expected_download_bytes) &&
        quantity(value.required_storage_bytes) &&
        value.destination_template.length > 0)));
const checks = (value: unknown) =>
  Array.isArray(value) &&
  value.every(
    (item) =>
      object(item) &&
      typeof item.resource === "string" &&
      typeof item.status === "string" &&
      typeof item.reason === "string",
  );
const component = (value: unknown) =>
  object(value) &&
  ["id", "role", "repository_id", "filename", "destination"].every(
    (key) => typeof value[key] === "string",
  ) &&
  nullableQuantity(value.expected_size_bytes) &&
  nullableQuantity(value.estimated_size_bytes);
function registeredModel(value: unknown) {
  if (!object(value) || !object(value.manifest) || !object(value.compatibility))
    return false;
  const m = value.manifest;
  const c = value.compatibility;
  return (
    ["id", "name", "description", "license", "support_status"].every(
      (key) => typeof m[key] === "string",
    ) &&
    typeof m.is_mock === "boolean" &&
    typeof m.is_fixture === "boolean" &&
    typeof m.artifact_installation_reviewed === "boolean" &&
    strings(m.tasks) &&
    Array.isArray(m.components) &&
    m.components.every(component) &&
    object(m.requirements) &&
    ["min_ram_gb", "min_vram_gb", "min_free_storage_gb"].every((key) =>
      nullableQuantity((m.requirements as Record<string, unknown>)[key]),
    ) &&
    (m.license_info === null ||
      (object(m.license_info) &&
        typeof m.license_info.identifier === "string" &&
        nullableText(m.license_info.source) &&
        strings(m.license_info.usage_restrictions) &&
        strings(m.license_info.acknowledgement_requirements))) &&
    typeof c.status === "string" &&
    typeof c.assessment === "string" &&
    checks(c.checks) &&
    checks(c.profile_checks) &&
    strings(c.notes)
  );
}
export function validateResponse<T>(data: unknown, kind: string): T {
  if (kind.startsWith("product")) {
    if (!productResponse(data, kind))
      throw new ApiError("Invalid product response", 0, "invalid_response");
    return data as T;
  }
  if (kind === "resolveResult") {
    if (
      !object(data) ||
      data.development_only !== true ||
      !id(data.job_id) ||
      ![
        "generated",
        "converting",
        "converted",
        "importing",
        "imported",
        "placed",
        "failed",
      ].includes(String(data.state)) ||
      (data.message !== undefined && typeof data.message !== "string") ||
      (["imported", "placed"].includes(String(data.state)) &&
        (typeof data.media_id !== "string" ||
          data.filename !== `Director_${data.job_id}.mp4`)) ||
      (data.state === "placed" &&
        !validateResponse(data.placement, "resolvePlacement"))
    )
      throw new ApiError("Invalid Resolve job response", 0, "invalid_response");
    return data as T;
  }
  if (kind === "resolveTimelines" || kind === "resolvePlacement") {
    const valid =
      object(data) &&
      data.development_only === true &&
      typeof data.project === "string" &&
      (kind === "resolveTimelines"
        ? typeof data.media_id === "string" &&
          nullableText(data.current_timeline_id) &&
          Array.isArray(data.timelines) &&
          data.timelines.every(
            (t) =>
              object(t) &&
              typeof t.id === "string" &&
              typeof t.name === "string",
          )
        : data.state === "placed" &&
          typeof data.timeline === "string" &&
          typeof data.item_id === "string" &&
          quantity(data.duration_seconds));
    if (!valid)
      throw new ApiError("Invalid Resolve response", 0, "invalid_response");
    return data as T;
  }
  if (kind === "generationConfig" || kind === "generationJob") {
    const validGeneration =
      object(data) &&
      data.development_only === true &&
      (kind === "generationConfig"
        ? typeof data.enabled === "boolean"
        : id(data.id) &&
          ["queued", "running", "completed", "failed", "cancelled"].includes(
            String(data.state),
          ) &&
          nullableText(data.comfy_prompt_id) &&
          nullableText(data.output_filename) &&
          (data.output_url === null ||
            data.output_url === `/api/dev/generation/jobs/${data.id}/output`) &&
          (data.progress === null ||
            (quantity(data.progress) && Number(data.progress) <= 1)) &&
          typeof data.message === "string");
    if (!validGeneration)
      throw new ApiError(
        "Invalid development generation response",
        0,
        "invalid_response",
      );
    return data as T;
  }
  const valid =
    object(data) &&
    (kind === "launcher"
      ? typeof data.automatic === "boolean"
      : kind === "runtime"
        ? runtimeReport(data)
        : kind === "license"
          ? typeof data.model_id === "string" &&
            digest(data.manifest_digest) &&
            digest(data.document_set_digest) &&
            data.policy_version === "1" &&
            licenseInfo(data.license_info) &&
            Array.isArray(data.documents) &&
            data.documents.length > 0 &&
            data.documents.every(
              (document) =>
                object(document) &&
                typeof document.id === "string" &&
                typeof document.version === "string" &&
                typeof document.text === "string" &&
                document.text.trim().length > 0 &&
                digest(document.sha256) &&
                nullableText(document.source),
            )
          : kind === "acknowledgement"
            ? id(data.id) &&
              typeof data.model_id === "string" &&
              digest(data.document_set_digest) &&
              data.policy_version === "1" &&
              typeof data.accepted_at === "string"
            : kind === "models"
              ? Array.isArray(data.models) &&
                data.models.every(registeredModel) &&
                strings(data.hardware_warnings)
              : kind === "hardware"
                ? object(data.cpu) &&
                  nullableText(data.cpu.name) &&
                  nullableQuantity(data.cpu.physical_cores) &&
                  nullableQuantity(data.cpu.logical_cores) &&
                  object(data.ram) &&
                  nullableQuantity(data.ram.total_gb) &&
                  nullableQuantity(data.ram.available_gb) &&
                  object(data.storage) &&
                  typeof data.storage.path === "string" &&
                  nullableQuantity(data.storage.total_gb) &&
                  nullableQuantity(data.storage.free_gb) &&
                  typeof data.platform === "string" &&
                  typeof data.gpu_detection_complete === "boolean" &&
                  Array.isArray(data.gpus) &&
                  data.gpus.every(
                    (gpu) =>
                      object(gpu) &&
                      typeof gpu.name === "string" &&
                      typeof gpu.vendor === "string" &&
                      nullableQuantity(gpu.vram_gb) &&
                      typeof gpu.vram_is_estimate === "boolean" &&
                      typeof gpu.source === "string" &&
                      nullableText(gpu.architecture),
                  ) &&
                  strings(data.warnings)
                : kind === "plan"
                  ? artifactReview(data.artifact_review) &&
                    typeof data.model_id === "string" &&
                    Array.isArray(data.blockers) &&
                    data.blockers.every(
                      (issue) =>
                        object(issue) && typeof issue.message === "string",
                    ) &&
                    Array.isArray(data.components) &&
                    data.components.every(
                      (item) => object(item) && component(item.component),
                    ) &&
                    strings(data.warnings) &&
                    strings(data.missing_metadata) &&
                    [
                      "total_expected_download_bytes",
                      "total_estimated_download_bytes",
                      "required_storage_bytes",
                    ].every((key) => nullableQuantity(data[key])) &&
                    object(data.storage) &&
                    typeof data.storage.root === "string" &&
                    nullableQuantity(data.storage.free_bytes)
                  : kind === "installation"
                    ? typeof data.model_id === "string" &&
                      typeof data.state === "string" &&
                      typeof data.artifact_ready === "boolean" &&
                      nullableText(data.job_id)
                    : kind === "job"
                      ? typeof data.id === "string" &&
                        typeof data.model_id === "string" &&
                        typeof data.operation === "string" &&
                        typeof data.state === "string" &&
                        quantity(data.candidate_bytes) &&
                        quantity(data.total_expected_bytes) &&
                        quantity(data.verified_bytes) &&
                        typeof data.cancel_requested === "boolean" &&
                        nullableText(data.current_component) &&
                        (data.error === null ||
                          (object(data.error) &&
                            typeof data.error.code === "string" &&
                            typeof data.error.message === "string"))
                      : false);
  if (!valid)
    throw new ApiError(
      "The backend returned an unexpected response. Check its URL and version.",
      0,
      "invalid_response",
    );
  return data as T;
}

export class DirectorApi {
  h3InstallationPlan() {
    return this.request<import("./h3").H3Plan>(
      "/product/h3/installation-plan",
      "productH3Plan",
    );
  }
  currentGeneration?: GenerationJob;
  private key = "";
  private automatic = false;
  readonly base: string;
  constructor(
    base = "/api",
    private timeoutMs = 45000,
    private fetcher: typeof fetch = (...args) => fetch(...args),
    private launcherDiscovery = (import.meta.env.DEV ||
      import.meta.env.VITE_PACKAGED_DEV === "1") &&
      import.meta.env.VITE_LAUNCHER_SESSION === "1",
  ) {
    const url = new URL(
      base,
      typeof location === "undefined" ? "http://127.0.0.1" : location.origin,
    );
    if (
      !["http:", "https:"].includes(url.protocol) ||
      !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) ||
      url.username ||
      url.password ||
      url.search ||
      url.hash
    ) {
      throw new Error(
        "Director API must use a local HTTP(S) URL without credentials, query or fragment.",
      );
    }
    this.base = base.replace(/\/$/, "");
  }
  setKey(key: string) {
    this.key = key;
  } // Memory only: never localStorage, sessionStorage or VITE_ env.
  hasKey() {
    return this.key.length >= 32 || this.automatic;
  }
  isAutomatic() {
    return this.automatic;
  }
  async launcherSession(signal?: AbortSignal) {
    // Never discover credentials on unrelated/configured absolute API servers.
    if (!this.launcherDiscovery || this.base !== "/api") return false;
    const result = await this.request<{ automatic: boolean }>(
      "/launcher-session",
      "launcher",
      "GET",
      signal,
    );
    this.automatic = result.automatic === true;
    return this.automatic;
  }
  private async request<T>(
    path: string,
    kind: string,
    method = "GET",
    signal?: AbortSignal,
    body?: unknown,
  ): Promise<T> {
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, this.timeoutMs);
    const abort = () => controller.abort();
    if (signal?.aborted) controller.abort();
    signal?.addEventListener("abort", abort, { once: true });
    try {
      const headers: Record<string, string> = { Accept: "application/json" };
      if (
        method !== "GET" ||
        /^\/dev\/generation\/jobs(?:\/|$)/.test(path) ||
        path.startsWith("/dev/resolve/") ||
        path.startsWith("/product/")
      ) {
        if (!this.hasKey())
          throw new ApiError(
            "Enter a local manager key of at least 32 characters for this privileged operation.",
            0,
            "key_required",
          );
        if (this.key) headers["X-Director-Key"] = this.key;
        else if (this.automatic) headers["X-Director-Session"] = "launcher";
      }
      if (body !== undefined)
        headers["Content-Type"] =
          body instanceof Blob
            ? "application/octet-stream"
            : "application/json";
      const response = await this.fetcher(`${this.base}${path}`, {
        method,
        headers,
        signal: controller.signal,
        credentials: "omit",
        redirect: "error",
        body:
          body === undefined
            ? undefined
            : body instanceof Blob
              ? body
              : JSON.stringify(body),
      });
      if (
        (kind === "generationOutput" ||
          kind === "resolveOutput" ||
          kind === "libraryFile") &&
        response.ok
      ) {
        if (
          kind !== "libraryFile" &&
          !(
            kind === "resolveOutput"
              ? ["video/mp4"]
              : ["video/webm", "video/mp4"]
          ).includes(response.headers.get("Content-Type")?.split(";")[0] ?? "")
        )
          throw new ApiError(
            "Invalid video response",
            response.status,
            "invalid_response",
          );
        const video = await response.blob();
        if (
          !video.size ||
          video.size > (kind === "libraryFile" ? 64 : 32) * 1024 * 1024 ||
          (kind === "libraryFile" &&
            ![
              "video/webm",
              "video/mp4",
              "image/jpeg",
              "image/png",
              "audio/wav",
            ].includes(
              response.headers.get("Content-Type")?.split(";")[0] ?? "",
            ))
        )
          throw new ApiError(
            "Invalid video size",
            response.status,
            "invalid_response",
          );
        return video as T;
      }
      let data: unknown;
      try {
        data = await response.json();
      } catch {
        throw new ApiError(
          "The server did not return JSON. Is the Director backend running?",
          response.status,
          "invalid_response",
        );
      }
      if (!response.ok) {
        const detail = object(data) ? data.detail : null;
        const message =
          typeof detail === "string"
            ? detail
            : object(detail) && typeof detail.message === "string"
              ? detail.message
              : `Request failed (HTTP ${response.status}).`;
        const code =
          object(detail) && typeof detail.code === "string"
            ? detail.code
            : "http_error";
        throw new ApiError(message, response.status, code);
      }
      return validateResponse<T>(data, kind);
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (timedOut)
        throw new ApiError(
          "The backend took too long to respond. Try again; a job may still be running.",
          0,
          "timeout",
        );
      if (controller.signal.aborted)
        throw new DOMException("Request cancelled", "AbortError");
      throw new ApiError(
        "Cannot reach Director. Start the backend and check the local proxy URL.",
        0,
        "network_error",
      );
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
    }
  }
  hardware(signal?: AbortSignal) {
    return this.request<HardwareProfile>(
      "/system/hardware",
      "hardware",
      "GET",
      signal,
    );
  }
  generationConfig(signal?: AbortSignal) {
    return this.request<{ enabled: boolean; development_only: true }>(
      "/dev/generation/config",
      "generationConfig",
      "GET",
      signal,
    );
  }
  resolveTimelines(signal?: AbortSignal) {
    return this.request<import("./types").ResolveTimelines>(
      "/dev/resolve/timelines",
      "resolveTimelines",
      "GET",
      signal,
    );
  }
  resolveResult(id: string, signal?: AbortSignal) {
    return this.request<import("./types").ResolveResult>(
      `/dev/resolve/jobs/${encodeURIComponent(id)}`,
      "resolveResult",
      "GET",
      signal,
    );
  }
  importToResolve(id: string) {
    return this.request<import("./types").ResolveResult>(
      `/dev/resolve/jobs/${encodeURIComponent(id)}/import`,
      "resolveResult",
      "POST",
    );
  }
  placeResolveJob(
    id: string,
    body: {
      confirmed: boolean;
      create_new: boolean;
      timeline_id: string | null;
      timeline_name: string;
    },
  ) {
    return this.request<import("./types").ResolveResult>(
      `/dev/resolve/jobs/${encodeURIComponent(id)}/placement`,
      "resolveResult",
      "POST",
      undefined,
      body,
    );
  }
  resolveOutput(id: string) {
    return this.request<Blob>(
      `/dev/resolve/jobs/${encodeURIComponent(id)}/output`,
      "resolveOutput",
      "GET",
    );
  }
  addToTimeline(body: {
    confirmed: boolean;
    create_new: boolean;
    timeline_id: string | null;
    timeline_name: string;
  }) {
    return this.request<import("./types").ResolvePlacement>(
      "/dev/resolve/placement",
      "resolvePlacement",
      "POST",
      undefined,
      body,
    );
  }
  async generate(prompt: string, seed: number, signal?: AbortSignal) {
    const job = await this.request<GenerationJob>(
      "/dev/generation/jobs",
      "generationJob",
      "POST",
      signal,
      { prompt, seed },
    );
    this.currentGeneration = job;
    return job;
  }
  async generationJob(id: string, signal?: AbortSignal) {
    const job = await this.request<GenerationJob>(
      `/dev/generation/jobs/${encodeURIComponent(id)}`,
      "generationJob",
      "GET",
      signal,
    );
    this.currentGeneration = job;
    return job;
  }
  generationOutput(id: string, signal?: AbortSignal) {
    return this.request<Blob>(
      `/dev/generation/jobs/${encodeURIComponent(id)}/output`,
      "generationOutput",
      "GET",
      signal,
    );
  }
  modelCard(repository: string) {
    return this.request<ModelCard>(
      `/product/discovery/details?repository=${encodeURIComponent(repository)}`,
      "productCard",
    );
  }
  installationJobs() {
    return this.request<{ jobs: InstallationJob[] }>(
      "/product/installation-jobs",
      "productInstallJobs",
    );
  }
  cachePlan() {
    return this.request<{
      files: string[];
      blockers: string[];
      shared_preserved: string[];
      reclaim_bytes: number;
      unknown_files_preserved: true;
      digest: string;
    }>("/product/cache/removal-plan", "productCachePlan");
  }
  clearOwnedCache(digest: string) {
    return this.request<{
      removed: true;
      reclaimed_bytes: number;
      shared_preserved: string[];
    }>("/product/cache/remove", "productRemoved", "POST", undefined, {
      confirmed: true,
      digest,
    });
  }
  productCatalog() {
    return this.request<Catalog>("/product/models", "productCatalog");
  }
  productJobs() {
    return this.request<{ jobs: ProductJob[]; session_only: true }>(
      "/product/jobs",
      "productJobs",
    );
  }
  creativeGenerate(body: CreativeRequest) {
    return this.request<ProductJob>(
      "/product/generation",
      "generationJob",
      "POST",
      undefined,
      body,
    );
  }
  cancelGeneration(id: string) {
    return this.request<ProductJob>(
      `/product/jobs/${encodeURIComponent(id)}/cancel`,
      "generationJob",
      "POST",
    );
  }
  forgetGeneration(id: string) {
    return this.request<{ forgotten: true; output_deleted: false }>(
      `/product/jobs/${encodeURIComponent(id)}/forget`,
      "productForgot",
      "POST",
    );
  }
  discover(query: string, filters: Record<string, string> = {}) {
    return this.request<DiscoveryResult>(
      `/product/discovery?${new URLSearchParams({ q: query, ...filters })}`,
      "productDiscovery",
    );
  }
  studio() {
    return this.request<import("./studio").Studio>(
      "/product/studio",
      "productStudio",
    );
  }
  saveProject(project: import("./studio").Project) {
    return this.request<import("./studio").Studio>(
      "/product/studio/projects",
      "productStudio",
      "POST",
      undefined,
      project,
    );
  }
  uploadAsset(file: File) {
    return this.request<import("./studio").Asset>(
      `/product/library/upload?filename=${encodeURIComponent(file.name)}`,
      "productAsset",
      "POST",
      undefined,
      file,
    );
  }
  libraryFile(id: string, thumbnail = false) {
    return this.request<Blob>(
      `/product/library/${encodeURIComponent(id)}/file?thumbnail=${thumbnail}`,
      "libraryFile",
    );
  }
  editAsset(id: string, body: { title?: string; favorite?: boolean }) {
    return this.request<import("./studio").Asset>(
      `/product/library/${encodeURIComponent(id)}/edit`,
      "productAsset",
      "POST",
      undefined,
      body,
    );
  }
  deleteAsset(id: string) {
    return this.request<{ deleted: true }>(
      `/product/library/${encodeURIComponent(id)}/delete`,
      "productAssetDeleted",
      "POST",
      undefined,
      { confirmed: true },
    );
  }
  revealAsset(id: string) {
    return this.request<{ revealed: true }>(
      `/product/library/${encodeURIComponent(id)}/reveal`,
      "productRevealed",
      "POST",
    );
  }
  assetHandoffs(id: string) {
    return this.request<{
      actions: { model_id: string; model_name: string; workspace: string }[];
      message: string;
    }>(
      `/product/library/${encodeURIComponent(id)}/handoffs`,
      "productHandoffs",
    );
  }
  recoverOutputs() {
    return this.request<{ imported: number }>(
      "/product/library/import-outputs",
      "productRecovered",
      "POST",
    );
  }
  downloads() {
    return this.request<import("./studio").Downloads>(
      "/product/downloads",
      "productDownloads",
    );
  }
  downloadRemoval(id: string) {
    return this.request<import("./studio").DownloadRemoval>(
      `/product/downloads/${encodeURIComponent(id)}/removal-plan`,
      "productDownloadRemoval",
    );
  }
  removeDownload(id: string, digest: string) {
    return this.request<{
      removed: true;
      reclaimed_bytes: number;
      shared_preserved: string[];
    }>(
      `/product/downloads/${encodeURIComponent(id)}/remove`,
      "productRemoved",
      "POST",
      undefined,
      { confirmed: true, digest },
    );
  }
  modelFiles(id: string) {
    return this.request<import("./studio").ModelFiles>(
      `/product/models/${encodeURIComponent(id)}/files`,
      "productModelFiles",
    );
  }
  verifyModel(id: string) {
    return this.request<{
      valid: boolean;
      reports: unknown[];
      generation_validated: false;
    }>(
      `/product/models/${encodeURIComponent(id)}/verify`,
      "productModelVerified",
      "POST",
    );
  }
  modelUpdates(id: string) {
    return this.request<{
      components: unknown[];
      replacement_allowed: false;
      message: string;
    }>(
      `/product/models/${encodeURIComponent(id)}/update-check`,
      "productModelUpdates",
    );
  }
  downloadPlan(repository: string, files: string[]) {
    return this.request<import("./studio").DownloadPlan>(
      "/product/downloads/plan",
      "productDownloadPlan",
      "POST",
      undefined,
      { repository, files },
    );
  }
  startDownload(plan: import("./studio").DownloadPlan) {
    return this.request<import("./studio").DownloadJob>(
      "/product/downloads",
      "productDownloadJob",
      "POST",
      undefined,
      {
        repository: plan.repository,
        files: plan.components.map((c) => c.filename),
        digest: plan.digest,
        confirmed: true,
        accepted_license: true,
      },
    );
  }
  cancelDownload(id: string) {
    return this.request<import("./studio").DownloadJob>(
      `/product/downloads/${encodeURIComponent(id)}/cancel`,
      "productDownloadJob",
      "POST",
    );
  }
  storage() {
    return this.request<StorageReport>("/product/storage", "productStorage");
  }
  removalPlan(id: string) {
    return this.request<RemovalPlan>(
      `/product/models/${encodeURIComponent(id)}/removal-plan`,
      "productRemoval",
    );
  }
  removeModel(id: string, digest: string) {
    return this.request<{
      removed: true;
      reclaimed_bytes: number;
      shared_preserved: string[];
    }>(
      `/product/models/${encodeURIComponent(id)}/remove`,
      "productRemoved",
      "POST",
      undefined,
      { confirmed: true, digest },
    );
  }
  consoleEvents() {
    return this.request<ConsoleReport>("/product/console", "productConsole");
  }
  clearConsole() {
    return this.request<{ cleared: true }>(
      "/product/console/clear",
      "productClear",
      "POST",
    );
  }
  runtime(signal?: AbortSignal) {
    return this.request<RuntimeReport>(
      "/system/runtime",
      "runtime",
      "GET",
      signal,
    );
  }
  models(signal?: AbortSignal) {
    return this.request<ModelsResponse>("/models", "models", "GET", signal);
  }
  plan(id: string, signal?: AbortSignal) {
    return this.request<InstallationPlan>(
      `/models/${encodeURIComponent(id)}/installation-plan`,
      "plan",
      "GET",
      signal,
    );
  }
  installation(id: string, signal?: AbortSignal) {
    return this.request<InstallationStatus>(
      `/models/${encodeURIComponent(id)}/installation`,
      "installation",
      "GET",
      signal,
    );
  }
  job(id: string, signal?: AbortSignal) {
    return this.request<InstallationJob>(
      `/installation-jobs/${encodeURIComponent(id)}`,
      "job",
      "GET",
      signal,
    );
  }
  cancel(id: string) {
    return this.request<InstallationJob>(
      `/installation-jobs/${encodeURIComponent(id)}/cancel`,
      "job",
      "POST",
    );
  }
  licenses(id: string, signal?: AbortSignal) {
    return this.request<LicenseRequirements>(
      `/models/${encodeURIComponent(id)}/license-requirements`,
      "license",
      "GET",
      signal,
    );
  }
  acknowledge(id: string, documentSetDigest: string) {
    return this.request<Acknowledgement>(
      `/models/${encodeURIComponent(id)}/license-acknowledgements`,
      "acknowledgement",
      "POST",
      undefined,
      {
        accepted: true,
        document_set_digest: documentSetDigest,
        policy_version: "1",
      },
    );
  }
  install(id: string, manifestDigest: string, acknowledgementId: string) {
    return this.request<InstallationJob>(
      `/models/${encodeURIComponent(id)}/installations`,
      "job",
      "POST",
      undefined,
      {
        manifest_digest: manifestDigest,
        acknowledgement_id: acknowledgementId,
      },
    );
  }
}
