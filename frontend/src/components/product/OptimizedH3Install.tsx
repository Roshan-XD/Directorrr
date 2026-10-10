import { useEffect, useState } from "react";
import type { DirectorApi } from "../../api/client";
import type { DownloadPlan, DownloadJob } from "../../api/studio";
import { Panel, bytes } from "../ui";
import { message } from "./message";

const repository = "DmitryDB/MiniMax-H3-ComfyUI-Quants";
const files = [
  "FL2VA/MiniMax-H3_FL2VA-NVFP4.safetensors",
  "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
  "vae/MiniMax-H3_VideoVAE-FP16.safetensors",
  "vae/MiniMax-H3_AudioVAE-FP32.safetensors",
];

export function OptimizedH3Install({
  api,
  changed,
  disabled = false,
}: {
  api: DirectorApi;
  changed: () => Promise<void>;
  disabled?: boolean;
}) {
  const [plan, setPlan] = useState<DownloadPlan>();
  const [accepted, setAccepted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<DownloadJob>();
  const [error, setError] = useState("");
  useEffect(() => {
    if (!job || ["completed", "failed", "cancelled"].includes(job.state))
      return;
    let alive = true;
    const timer = setInterval(() => {
      void api
        .downloads()
        .then(async (data) => {
          const next = data.jobs.find((j) => j.id === job.id);
          if (alive && next) {
            setJob(next);
            if (next.state === "completed") await changed();
          }
        })
        .catch((e) => {
          if (alive) setError(message(e));
        });
    }, 2500);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [api, job?.id, job?.state, changed]);
  async function review() {
    setBusy(true);
    setError("");
    setAccepted(false);
    try {
      setPlan(await api.downloadPlan(repository, files));
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function install() {
    if (!plan || !accepted) return;
    setBusy(true);
    setError("");
    try {
      setJob(await api.startDownload(plan));
      setPlan(undefined);
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      {!job && (
        <button
          className="button primary"
          disabled={busy || disabled}
          onClick={() => void review()}
        >
          {busy ? "Checking installation…" : "Install MiniMax H3 Optimized"}
        </button>
      )}
      {error && <p role="alert">{error}</p>}
      {plan && (
        <Panel>
          <section
            role="region"
            aria-label="Optimized H3 installation confirmation"
          >
            <h3>Confirm MiniMax H3 Optimized installation</h3>
            <p>
              {plan.variant} · {plan.quantization}
            </p>
            <p>
              Download: {bytes(plan.total_bytes)} (
              {plan.total_bytes.toLocaleString()} bytes),{" "}
              {plan.components.length} files. Free disk:{" "}
              {bytes(plan.free_bytes ?? null)}. Required staging/cache reserve:{" "}
              {bytes(plan.required_free_bytes)}.
            </p>
            <p>
              Destination: {plan.destination}. Text-to-video with native audio.
              No custom nodes.
            </p>
            {plan.warnings.map((w) => (
              <p className="notice" key={w}>
                {w}
              </p>
            ))}
            {plan.blockers.map((b) => (
              <p role="alert" key={b}>
                {b}
              </p>
            ))}
            <details>
              <summary>Exact files and hashes</summary>
              {plan.components.map((c) => (
                <p key={c.filename}>
                  {c.filename} · {bytes(c.expected_size_bytes)} · SHA-256{" "}
                  {c.sha256}
                </p>
              ))}
            </details>
            <a href={plan.license_source} target="_blank" rel="noreferrer">
              {plan.license}
            </a>
            <p>
              Qwen encoder:{" "}
              <a
                href="https://github.com/QwenLM/Qwen3-VL/blob/main/LICENSE"
                target="_blank"
                rel="noreferrer"
              >
                Apache 2.0
              </a>
              . Applicable notices are retained.
            </p>
            <details>
              <summary>
                Complete accompanying H3 agreement and acceptable-use policy
              </summary>
              <pre style={{ whiteSpace: "pre-wrap" }}>{plan.license_text}</pre>
            </details>
            {plan.encoder_license && (
              <details>
                <summary>Retained Qwen Apache 2.0 license</summary>
                <pre style={{ whiteSpace: "pre-wrap" }}>
                  {plan.encoder_license.text}
                </pre>
              </details>
            )}
            <ul>
              {plan.license_conditions?.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
            <label className="check-row">
              <input
                type="checkbox"
                checked={accepted}
                onChange={(e) => setAccepted(e.target.checked)}
              />
              I explicitly accept the displayed terms and confirm all
              territorial/use conditions above.
            </label>
            <button
              className="button primary"
              disabled={!accepted || busy || !!plan.blockers.length || disabled}
              onClick={() => void install()}
            >
              Confirm / Install {bytes(plan.total_bytes)}
            </button>
            <button
              className="text-button"
              disabled={busy}
              onClick={() => {
                setPlan(undefined);
                setAccepted(false);
              }}
            >
              Cancel review
            </button>
          </section>
        </Panel>
      )}
      {job && (
        <div role="status">
          <p>
            {job.state} — {job.message}
          </p>
          {job.technical_details && (
            <details>
              <summary>Technical Details</summary>
              <pre style={{ whiteSpace: "pre-wrap" }}>
                {job.technical_details}
              </pre>
            </details>
          )}
          <progress
            aria-label="H3 verified bytes"
            max={job.total_bytes || 1}
            value={job.verified_bytes}
          />
          <p>
            {bytes(job.candidate_bytes)} downloaded / {bytes(job.total_bytes)};{" "}
            {bytes(job.verified_bytes)} verified. Also tracked in Downloads.
          </p>
          {["queued", "downloading", "verifying", "installing"].includes(
            job.state,
          ) && (
            <button
              className="button secondary"
              onClick={() =>
                void api
                  .cancelDownload(job.id)
                  .catch((e) => setError(message(e)))
              }
            >
              Cancel installation
            </button>
          )}
          {["failed", "cancelled"].includes(job.state) && (
            <button
              className="button secondary"
              onClick={() => {
                setJob(undefined);
                void review();
              }}
            >
              Review retry
            </button>
          )}
        </div>
      )}
    </>
  );
}
