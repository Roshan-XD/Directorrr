import { useState } from "react";
import type { DirectorApi } from "../../api/client";
import type { H3Plan } from "../../api/h3";
import { Panel, bytes } from "../ui";
import { message } from "./message";

export function H3InstallReview({ api }: { api: DirectorApi }) {
  const [plan, setPlan] = useState<H3Plan>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [accepted, setAccepted] = useState(false);
  async function review() {
    setLoading(true);
    setError("");
    setAccepted(false);
    try {
      setPlan(await api.h3InstallationPlan());
    } catch (e) {
      setError(message(e));
    } finally {
      setLoading(false);
    }
  }
  return (
    <>
      <button
        className="button secondary"
        disabled={loading}
        onClick={() => void review()}
      >
        {loading ? "Checking H3 installation…" : "Install MiniMax H3"}
      </button>
      <p>
        Install opens an exact-file review. It never starts a download
        automatically.
      </p>
      {error && <p role="alert">{error}</p>}
      {plan && (
        <Panel>
          <section role="region" aria-label="MiniMax H3 installation review">
            <h3>MiniMax H3 — installation blocked</h3>
            <p>
              {plan.repository} · revision {plan.revision}
            </p>
            <p>
              Text → video + native stereo audio. Runtime: {plan.runtime}{" "}
              {plan.runtime_version}. This is a reviewed candidate, not a
              runnable adapter.
            </p>
            <p>
              Download: {bytes(plan.download_bytes)} (
              {plan.download_bytes.toLocaleString()} bytes), {plan.files.length}{" "}
              files.
            </p>
            <p>
              Installed model payload: {bytes(plan.installed_payload_bytes)}.
              Runtime packages are additional. Staging/cache/rollback budget:{" "}
              {bytes(plan.required_free_bytes)}. Free disk:{" "}
              {bytes(plan.free_bytes)}.
            </p>
            <p>{plan.destination}</p>
            <p>
              Host RAM: {bytes(plan.hardware.ram_bytes)}. Documented INT8
              offload working set: approximately{" "}
              {bytes(plan.memory_guidance_bytes)} (an estimate, not a measured
              minimum). CPU/group offload and video-VAE offload would be
              required on a 16 GB GPU.
            </p>
            <a href={plan.memory_source} target="_blank" rel="noreferrer">
              Official memory guidance
            </a>
            <p>
              <a href={plan.license_source} target="_blank" rel="noreferrer">
                {plan.license}
              </a>
            </p>
            <p>Document SHA-256: {plan.license_sha256}</p>
            <ul>
              {plan.license_conditions.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
            {plan.blockers.map((b) => (
              <p className="notice" key={b}>
                {b}
              </p>
            ))}
            <details>
              <summary>Warnings and exact file inventory</summary>
              {plan.warnings.map((w) => (
                <p key={w}>{w}</p>
              ))}
              {plan.files.map((f) => (
                <p key={f.filename}>
                  {f.filename} · {f.expected_size_bytes.toLocaleString()} bytes
                  ·{" "}
                  {f.sha256
                    ? `SHA-256 ${f.sha256}`
                    : `Pinned Git blob ${f.git_blob_sha1}; SHA-256 not recorded`}
                </p>
              ))}
            </details>
            <label className="check-row">
              <input
                type="checkbox"
                checked={accepted}
                onChange={(e) => setAccepted(e.target.checked)}
              />
              I reviewed this plan; this does not accept terms or authorize a
              transfer.
            </label>
            <button className="button" disabled>
              Download unavailable — resolve blockers first
            </button>
            <button
              className="text-button"
              onClick={() => {
                setPlan(undefined);
                setAccepted(false);
              }}
            >
              Close installation review
            </button>
          </section>
        </Panel>
      )}
    </>
  );
}
