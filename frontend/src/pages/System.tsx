import { useCallback } from "react";
import type { DirectorApi } from "../api/client";
import { useResource } from "../hooks/useResource";
import {
  Badge,
  ErrorState,
  gib,
  Icon,
  Loading,
  Notice,
  PageHeading,
  Panel,
} from "../components/ui";

export function System({ api }: { api: DirectorApi }) {
  const load = useCallback(
    (signal: AbortSignal) => api.hardware(signal),
    [api],
  );
  const result = useResource(load);
  const hardware = result.data;
  const loadRuntime = useCallback(
    (signal: AbortSignal) => api.runtime(signal),
    [api],
  );
  const runtime = useResource(loadRuntime);
  return (
    <>
      <PageHeading
        eyebrow="LOCAL HARDWARE"
        title="Know your system"
        action={
          <button
            className="button secondary"
            onClick={() => {
              result.reload();
              runtime.reload();
            }}
            disabled={result.loading || runtime.loading}
          >
            <Icon name="refresh" />
            Refresh
          </button>
        }
      >
        A hardware snapshot, with uncertainty clearly visible.
      </PageHeading>
      {result.loading ? (
        <Loading text="Inspecting local hardware…" />
      ) : result.error ? (
        <ErrorState error={result.error} retry={result.reload} />
      ) : (
        hardware && (
          <>
            <div className="stats-grid">
              <Panel>
                <div className="metric-label">
                  Processor <Icon name="system" />
                </div>
                <h2>{hardware.cpu.name ?? "Unknown CPU"}</h2>
                <p>
                  {hardware.cpu.physical_cores ?? "Unknown"} physical cores ·{" "}
                  {hardware.cpu.logical_cores ?? "Unknown"} threads
                </p>
                <Badge>{hardware.platform}</Badge>
              </Panel>
              <Panel>
                <div className="metric-label">System RAM</div>
                <div className="metric">{gib(hardware.ram.total_gb)}</div>
                <p>{gib(hardware.ram.available_gb)} currently available</p>
                <small>Total RAM does not predict peak inference memory.</small>
              </Panel>
              <Panel>
                <div className="metric-label">Storage available</div>
                <div className="metric">{gib(hardware.storage.free_gb)}</div>
                <p>of {gib(hardware.storage.total_gb)}</p>
                <small className="break-word">{hardware.storage.path}</small>
              </Panel>
            </div>
            <Panel>
              <div className="panel-heading">
                <h2>Graphics processors</h2>
                <Badge>{hardware.gpus.length} detected</Badge>
              </div>
              {hardware.gpus.length === 0 ? (
                <div className="empty">
                  {hardware.gpu_detection_complete
                    ? "No GPU detected."
                    : "GPU detection is incomplete. Available GPUs are unknown."}
                </div>
              ) : (
                <div className="gpu-list">
                  {hardware.gpus.map((gpu, index) => (
                    <div className="gpu-row" key={`${gpu.name}-${index}`}>
                      <div className="gpu-icon">
                        <Icon name="system" size={24} />
                      </div>
                      <div>
                        <h3>{gpu.name}</h3>
                        <p>
                          {gpu.vendor.toUpperCase()} · Architecture:{" "}
                          {gpu.architecture ?? "Unknown"}
                        </p>
                        <small>Source: {gpu.source.replaceAll("_", " ")}</small>
                      </div>
                      <div className="gpu-memory">
                        <strong>{gib(gpu.vram_gb)}</strong>
                        <span>
                          VRAM {gpu.vram_is_estimate ? "· estimate" : ""}
                        </span>
                        {gpu.vram_is_estimate && (
                          <Badge tone="amber">
                            Unreliable for compatibility
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
            {!hardware.gpu_detection_complete && (
              <Notice>
                GPU detection did not complete. Missing entries do not prove a
                GPU is absent.
              </Notice>
            )}
            <Panel>
              <h2>Detection notes</h2>
              {hardware.warnings.length ? (
                <ul className="reason-list">
                  {hardware.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              ) : (
                <p>No detection warnings reported.</p>
              )}
              <p className="field-hint">
                Unknown values are not zero. Hardware capacity alone does not
                verify model or runtime compatibility.
              </p>
            </Panel>
          </>
        )
      )}
      <Panel>
        <h2>Runtime diagnostics</h2>
        <p>
          Read-only metadata. GPU execution and Wan generation have not been
          tested.
        </p>
        {runtime.loading ? (
          <Loading text="Inspecting runtime metadata…" />
        ) : runtime.error ? (
          <ErrorState error={runtime.error} retry={runtime.reload} />
        ) : (
          runtime.data && (
            <>
              <p>
                {runtime.data.operating_system} · {runtime.data.architecture} ·
                Readiness: {runtime.data.readiness}
              </p>
              <div className="stats-grid">
                {(
                  [
                    ["Python", runtime.data.python],
                    ["PyTorch", runtime.data.pytorch],
                    ["ComfyUI", runtime.data.comfyui],
                    ["Driver CUDA capability", runtime.data.driver_cuda],
                    ["CUDA toolkit", runtime.data.cuda_toolkit],
                  ] as const
                ).map(([label, item]) => (
                  <div key={label}>
                    <h3>{label}</h3>
                    <Badge>{item.status.replaceAll("_", " ")}</Badge>
                    <p>Version: {item.version ?? "Unknown"}</p>
                    <p>{item.detail}</p>
                    <small>Source: {item.source.replaceAll("_", " ")}</small>
                  </div>
                ))}
              </div>
              <h3>GPU drivers</h3>
              {runtime.data.gpu_drivers.length ? (
                <ul className="reason-list">
                  {runtime.data.gpu_drivers.map((gpu, index) => (
                    <li key={index}>
                      {gpu.name} ({gpu.vendor}) · Driver:{" "}
                      {gpu.driver.version ?? "Unknown"} · {gpu.driver.detail}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>
                  No driver entries observed. This alone does not establish GPU
                  absence.
                </p>
              )}
              <h3>Missing prerequisites</h3>
              {runtime.data.missing_prerequisites.length ? (
                <ul className="reason-list">
                  {runtime.data.missing_prerequisites.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p>
                  No missing prerequisites established. Compatibility remains
                  unverified.
                </p>
              )}
              <h3>Unresolved compatibility</h3>
              <ul className="reason-list">
                {runtime.data.unresolved_questions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <h3>Runtime warnings</h3>
              {runtime.data.warnings.length ? (
                <ul className="reason-list">
                  {runtime.data.warnings.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p>No runtime detection warnings reported.</p>
              )}
            </>
          )
        )}
      </Panel>
    </>
  );
}
