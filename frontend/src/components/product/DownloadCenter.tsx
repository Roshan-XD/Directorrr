import { useEffect, useState } from "react";
import type { DirectorApi } from "../../api/client";
import type { Downloads, DownloadRemoval } from "../../api/studio";
import { Panel, bytes, Badge } from "../ui";
import { message } from "./message";
export function DownloadCenter({ api }: { api: DirectorApi }) {
  const [data, setData] = useState<Downloads>();
  const [error, setError] = useState("");
  const [removal, setRemoval] = useState<DownloadRemoval>();
  const [confirmed, setConfirmed] = useState(false);
  useEffect(() => {
    let alive = true;
    const load = () =>
      void api
        .downloads()
        .then((d) => {
          if (alive) {
            setData(d);
            setError("");
          }
        })
        .catch((e) => {
          if (alive) setError(message(e));
        });
    load();
    const timer = setInterval(load, 2500);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [api]);
  return (
    <>
      <h1>Downloads</h1>
      <p>
        Persistent, pinned repository data transfers. Downloaded does not mean
        runnable.
      </p>
      {error && <p role="alert">{error}</p>}
      {removal && (
        <Panel>
          <h2>Remove exact downloaded data?</h2>
          <p>
            {bytes(removal.reclaim_bytes)} · {removal.files.length} owned files.
            Installed models, original media and SDK cache preserved.
          </p>
          <label className="check-row">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            I explicitly confirm deleting only this reviewed data.
          </label>
          <button
            className="button secondary"
            disabled={!confirmed}
            onClick={() =>
              void api
                .removeDownload(removal.job_id, removal.digest)
                .then(() => {
                  setRemoval(undefined);
                  return api.downloads();
                })
                .then(setData)
                .catch((e) => setError(message(e)))
            }
          >
            Confirm data removal
          </button>
          <button className="text-button" onClick={() => setRemoval(undefined)}>
            Keep files
          </button>
        </Panel>
      )}
      {data && !data.real_downloads_enabled && (
        <p className="notice">
          Generic repository downloads are disabled. The reviewed H3 Optimized
          installation requires its own explicit confirmation in Model Store.
        </p>
      )}
      {!data ? (
        <p role="status">Loading downloads…</p>
      ) : !data.jobs.length ? (
        <Panel>
          No downloads yet. Select exact files in a published model card to
          review a plan.
        </Panel>
      ) : (
        data.jobs.map((job) => (
          <Panel key={job.id}>
            <h2>{job.repository}</h2>
            <Badge>{job.state}</Badge>
            <p role="status">{job.message}</p>
            {job.technical_details && (
              <details>
                <summary>Technical Details</summary>
                <pre style={{ whiteSpace: "pre-wrap" }}>
                  {job.technical_details}
                </pre>
              </details>
            )}
            <p>
              Candidate bytes {bytes(job.candidate_bytes)} · verified{" "}
              {bytes(job.verified_bytes)} / {bytes(job.total_bytes)}
            </p>
            <p>
              {job.speed_bytes_per_second
                ? `Observed candidate rate ${bytes(job.speed_bytes_per_second)}/s · estimated remaining ${Math.ceil(job.eta_seconds ?? 0)} s`
                : "Speed / ETA unavailable. Candidate bytes are not integrity proof."}
            </p>
            <progress
              aria-label="Verified download bytes"
              max={job.total_bytes || 1}
              value={job.verified_bytes}
            />
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
                Cancel download
              </button>
            )}
            <details>
              <summary>Exact pinned plan</summary>
              <pre>{JSON.stringify(job.plan, null, 2)}</pre>
            </details>
            {["failed", "cancelled", "completed"].includes(job.state) && (
              <button
                className="text-button"
                onClick={() =>
                  void api
                    .downloadRemoval(job.id)
                    .then((p) => {
                      setRemoval(p);
                      setConfirmed(false);
                    })
                    .catch((e) => setError(message(e)))
                }
              >
                Review downloaded-data removal
              </button>
            )}
            <p>
              Retry: return to the model card and review a fresh plan.
              Interrupted jobs never restart automatically.
            </p>
          </Panel>
        ))
      )}
    </>
  );
}
