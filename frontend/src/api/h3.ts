export interface H3Plan {
  repository: string;
  revision: string;
  workflow: string;
  runtime: string;
  runtime_version: string;
  download_bytes: number;
  installed_payload_bytes: number;
  required_free_bytes: number;
  free_bytes: number | null;
  destination: string;
  license: string;
  license_source: string;
  license_sha256: string;
  license_conditions: string[];
  memory_guidance_bytes: number;
  memory_source: string;
  hardware: {
    ram_bytes: number | null;
    available_ram_gb: number | null;
    gpus: {
      name: string;
      vendor: string;
      vram_gb: number | null;
      is_estimate: boolean;
    }[];
  };
  files: {
    filename: string;
    expected_size_bytes: number;
    sha256: string | null;
    git_blob_sha1: string;
    url: string;
    destination: string;
  }[];
  blockers: string[];
  warnings: string[];
  state: "not_installed";
  can_install: false;
  ready: false;
  digest: string;
}

export function h3Response(value: unknown, kind: string) {
  if (kind !== "productH3Plan" || !value || typeof value !== "object")
    return false;
  const v = value as Record<string, unknown>;
  const strings = (x: unknown) =>
    Array.isArray(x) && x.every((s) => typeof s === "string");
  const bytes = (x: unknown) =>
    typeof x === "number" && Number.isSafeInteger(x) && x >= 0;
  const quantity = (x: unknown) =>
    x === null || (typeof x === "number" && Number.isFinite(x) && x >= 0);
  const hardware = v.hardware as Record<string, unknown> | null;
  return (
    v.repository === "MiniMaxAI/MiniMax-H3" &&
    v.revision === "42ed227ee7df40d41602854ae760620d6eb651fe" &&
    v.workflow === "t2va" &&
    v.runtime === "diffusers-modular" &&
    v.runtime_version === "0.41.0" &&
    v.can_install === false &&
    v.ready === false &&
    v.state === "not_installed" &&
    [
      "download_bytes",
      "installed_payload_bytes",
      "required_free_bytes",
      "memory_guidance_bytes",
    ].every((k) => bytes(v[k])) &&
    (v.free_bytes === null || bytes(v.free_bytes)) &&
    [
      "destination",
      "license",
      "license_source",
      "memory_source",
      "digest",
      "license_sha256",
    ].every((k) => typeof v[k] === "string") &&
    /^[0-9a-f]{64}$/.test(String(v.digest)) &&
    /^[0-9a-f]{64}$/.test(String(v.license_sha256)) &&
    strings(v.blockers) &&
    strings(v.warnings) &&
    strings(v.license_conditions) &&
    v.license_source ===
      "https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/42ed227ee7df40d41602854ae760620d6eb651fe/LICENSE" &&
    v.memory_source ===
      "https://huggingface.co/docs/diffusers/v0.41.0/api/pipelines/minimax_h3#memory" &&
    typeof hardware === "object" &&
    hardware !== null &&
    (hardware.ram_bytes === null || bytes(hardware.ram_bytes)) &&
    quantity(hardware.available_ram_gb) &&
    Array.isArray(hardware.gpus) &&
    hardware.gpus.every((g: unknown) => {
      if (!g || typeof g !== "object") return false;
      const gpu = g as Record<string, unknown>;
      return (
        typeof gpu.name === "string" &&
        typeof gpu.vendor === "string" &&
        quantity(gpu.vram_gb) &&
        typeof gpu.is_estimate === "boolean"
      );
    }) &&
    Array.isArray(v.files) &&
    v.files.length <= 100 &&
    v.files.every((f: unknown) => {
      if (!f || typeof f !== "object") return false;
      const file = f as Record<string, unknown>;
      return (
        typeof file.filename === "string" &&
        file.destination === file.filename &&
        bytes(file.expected_size_bytes) &&
        file.url ===
          `https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/${v.revision}/${file.filename}` &&
        /^[0-9a-f]{40}$/.test(String(file.git_blob_sha1)) &&
        (file.sha256 === null || /^[0-9a-f]{64}$/.test(String(file.sha256)))
      );
    })
  );
}
