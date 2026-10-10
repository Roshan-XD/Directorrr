/** Read-only contracts used by the UI. Null means unmeasured, never zero. */
export interface ResolveTimelines {
  development_only: true;
  project: string;
  media_id: string;
  current_timeline_id: string | null;
  timelines: { id: string; name: string }[];
}
export interface ResolvePlacement {
  development_only: true;
  state: "placed";
  project: string;
  timeline: string;
  item_id: string;
  duration_seconds: number;
}
export interface ResolveResult {
  development_only: true;
  job_id: string;
  state:
    | "generated"
    | "converting"
    | "converted"
    | "importing"
    | "imported"
    | "placed"
    | "failed";
  filename?: string;
  media_id?: string;
  message?: string;
  placement?: ResolvePlacement;
}
export interface HardwareProfile {
  platform: string;
  cpu: {
    name: string | null;
    physical_cores: number | null;
    logical_cores: number | null;
  };
  ram: { total_gb: number | null; available_gb: number | null };
  gpus: {
    name: string;
    vendor: string;
    vram_gb: number | null;
    vram_is_estimate: boolean;
    source: string;
    architecture: string | null;
  }[];
  gpu_detection_complete: boolean;
  storage: { path: string; total_gb: number | null; free_gb: number | null };
  warnings: string[];
}
export interface LicenseInfo {
  identifier: string;
  source: string | null;
  usage_restrictions: string[];
  acknowledgement_requirements: string[];
}
export interface Component {
  id: string;
  role: string;
  repository_id: string;
  pinned_revision: string | null;
  filename: string;
  destination: string;
  expected_size_bytes: number | null;
  estimated_size_bytes: number | null;
  sha256: string | null;
}
export interface Manifest {
  id: string;
  name: string;
  description: string;
  is_mock: boolean;
  is_fixture: boolean;
  tasks: string[];
  runtime: string;
  license: string;
  support_status: string;
  huggingface_repo_id: string | null;
  components: Component[];
  artifact_installation_reviewed: boolean;
  license_info: LicenseInfo | null;
  unresolved_assumptions: string[];
  requirements: {
    min_ram_gb: number | null;
    min_vram_gb: number | null;
    min_free_storage_gb: number | null;
    gpu_required: boolean;
    limitations: string[];
  };
}
export interface Check {
  resource: string;
  status: string;
  reason: string;
}
export interface Compatibility {
  status: string;
  assessment: string;
  checks: Check[];
  profile_checks: Check[];
  notes: string[];
}
export interface RegisteredModel {
  manifest: Manifest;
  compatibility: Compatibility;
}
export interface ModelsResponse {
  models: RegisteredModel[];
  hardware_warnings: string[];
}
export interface InstallationPlan {
  artifact_review?: ArtifactReview | null;
  model_id: string;
  read_only: true;
  ready_for_installation: false;
  status: string;
  total_expected_download_bytes: number | null;
  total_estimated_download_bytes: number | null;
  known_download_bytes: number;
  required_storage_bytes: number | null;
  storage: {
    root: string;
    free_bytes: number | null;
    total_bytes: number | null;
  };
  components: { component: Component; destination_path: string | null }[];
  blockers: { code: string; message: string; component_id: string | null }[];
  warnings: string[];
  missing_metadata: string[];
}
export interface ArtifactReview {
  can_review: boolean;
  blockers: { code: string; message: string }[];
  expected_download_bytes: number | null;
  required_storage_bytes: number | null;
  destination_template: string;
  requires_acknowledgement: true;
  requires_manager_key: true;
  generation_ready: false;
}
export interface LicenseRequirements {
  model_id: string;
  manifest_digest: string;
  document_set_digest: string;
  policy_version: "1";
  license_info: LicenseInfo | null;
  documents: {
    id: string;
    version: string;
    text: string;
    sha256: string;
    source: string | null;
  }[];
}
export interface Acknowledgement {
  id: string;
  model_id: string;
  document_set_digest: string;
  policy_version: "1";
  accepted_at: string;
}
export interface Verification {
  component_id: string;
  valid: boolean;
  code: string;
  actual_size: number | null;
}
export interface InstallationStatus {
  model_id: string;
  state: string;
  artifact_ready: boolean;
  generation_ready: false;
  job_id: string | null;
  verification: Verification[];
  incomplete_bundles: string[];
}
export interface InstallationJob {
  id: string;
  model_id: string;
  operation: string;
  state: string;
  total_expected_bytes: number;
  candidate_bytes: number;
  verified_bytes: number;
  cancel_requested: boolean;
  current_component: string | null;
  error: { code: string; message: string } | null;
  created_at: string;
  updated_at: string;
  generation_ready: false;
}
export type RuntimeObservation = {
  status:
    "installed" | "not_detected" | "unknown" | "not_tested" | "not_configured";
  version: string | null;
  source: string;
  detail: string;
};
export type RuntimeReport = {
  operating_system: string;
  architecture: string;
  python: RuntimeObservation;
  pytorch: RuntimeObservation;
  comfyui: RuntimeObservation;
  cuda_toolkit: RuntimeObservation;
  driver_cuda: RuntimeObservation;
  gpu_drivers: { name: string; vendor: string; driver: RuntimeObservation }[];
  missing_prerequisites: string[];
  unresolved_questions: string[];
  warnings: string[];
  readiness: "incomplete" | "unknown";
  gpu_execution: "not_tested";
  generation_ready: false;
};
export interface GenerationJob {
  id: string;
  state: "queued" | "running" | "completed" | "failed" | "cancelled";
  comfy_prompt_id: string | null;
  progress: number | null;
  message: string;
  output_filename: string | null;
  output_url: string | null;
  development_only: true;
}
