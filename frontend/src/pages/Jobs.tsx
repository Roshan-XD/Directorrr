import { useEffect, useState } from "react";
import { ManagerAuthorization } from "../components/ManagerAuthorization";
import type { DirectorApi } from "../api/client";
import type { InstallationJob } from "../api/types";
import { jobIdPattern } from "../hooks/history";
import {
  Badge,
  bytes,
  Icon,
  Notice,
  PageHeading,
  Panel,
  stateLabel,
} from "../components/ui";

const terminal = new Set([
  "ready",
  "failed",
  "cancelled",
  "corrupted",
  "not_installed",
]);
export function Jobs({
  api,
  ids,
  remember,
  forget,
}: {
  api: DirectorApi;
  ids: string[];
  remember: (id: string) => void;
  forget: (id: string) => void;
}) {
  const [lookup, setLookup] = useState("");
  const [lookupError, setLookupError] = useState("");
  const [jobs, setJobs] = useState<Record<string, InstallationJob>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [refresh, setRefresh] = useState(0);
  const [cancelling, setCancelling] = useState("");
  const [keySet, setKeySet] = useState(api.hasKey());
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async (targets: string[]) => {
      const active: string[] = [];
      await Promise.all(
        targets.map(async (id) => {
          try {
            const job = await api.job(id, controller.signal);
            if (controller.signal.aborted) return;
            setJobs((previous) => ({ ...previous, [id]: job }));
            setErrors((previous) => {
              const next = { ...previous };
              delete next[id];
              return next;
            });
            if (!terminal.has(job.state)) active.push(id);
          } catch (error) {
            if (!controller.signal.aborted)
              setErrors((previous) => ({
                ...previous,
                [id]: error instanceof Error ? error.message : "Lookup failed",
              }));
          }
        }),
      );
      if (!controller.signal.aborted && active.length)
        timer = setTimeout(() => {
          void poll(active);
        }, 4000);
    };
    void poll(ids);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [api, ids, refresh]);
  async function cancel(id: string) {
    setCancelling(id);
    try {
      const job = await api.cancel(id);
      setJobs((previous) => ({ ...previous, [id]: job }));
      setRefresh((v) => v + 1);
    } catch (error) {
      setErrors((previous) => ({
        ...previous,
        [id]: error instanceof Error ? error.message : "Cancellation failed",
      }));
    } finally {
      setCancelling("");
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="INSTALLATION ACTIVITY"
        title="Keep track of every step"
        action={
          <button
            className="button secondary"
            onClick={() => setRefresh((v) => v + 1)}
          >
            <Icon name="refresh" />
            Refresh jobs
          </button>
        }
      >
        Inspect artifact jobs without confusing download progress with
        generation readiness.
      </PageHeading>
      <Panel className="job-lookup">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const id = lookup.trim();
            if (!jobIdPattern.test(id)) {
              setLookupError(
                "Enter a 32-character lowercase hexadecimal job ID.",
              );
              return;
            }
            setLookupError("");
            remember(id);
            setRefresh((v) => v + 1);
            setLookup("");
          }}
        >
          <label className="field">
            Look up a job
            <input
              value={lookup}
              onChange={(event) => setLookup(event.target.value)}
              placeholder="Paste a backend job ID"
              spellCheck={false}
              aria-describedby="job-history-note"
            />
          </label>
          <button className="button secondary" type="submit">
            Track job
            <Icon name="arrow" size={16} />
          </button>
        </form>
        {lookupError && (
          <p role="alert" className="inline-error">
            {lookupError}
          </p>
        )}
        <p id="job-history-note" className="field-hint">
          The backend has no job-list endpoint. This tab remembers up to 12
          known IDs; model status can also reveal a recent job. Active jobs
          refresh every 4 seconds.
        </p>
      </Panel>
      {!ids.length && (
        <Panel>
          <div className="empty jobs-empty">
            <Icon name="jobs" size={36} />
            <h2>No tracked jobs yet</h2>
            <p>
              Paste an ID from a backend installation or offline fixture.
              <br />
              Opening this page never starts a download.
            </p>
          </div>
        </Panel>
      )}
      <div className="job-list">
        {ids.map((id) => {
          const job = jobs[id];
          const error = errors[id];
          const ratio =
            job && job.total_expected_bytes > 0
              ? Math.min(
                  100,
                  Math.max(
                    0,
                    (job.candidate_bytes / job.total_expected_bytes) * 100,
                  ),
                )
              : null;
          return (
            <Panel className="job-card" key={id}>
              <div className="panel-heading">
                <div>
                  <h2>
                    {job
                      ? `${job.operation} · ${job.model_id}`
                      : "Looking up job…"}
                  </h2>
                  <code className="job-id">{id}</code>
                </div>
                <Badge
                  tone={
                    job?.state === "failed" || job?.state === "corrupted"
                      ? "red"
                      : job?.state === "ready"
                        ? "green"
                        : "muted"
                  }
                >
                  {job
                    ? stateLabel(job.state)
                    : error
                      ? "Unavailable"
                      : "Pending lookup"}
                </Badge>
              </div>
              {error && <Notice danger>{error}</Notice>}
              {job && (
                <>
                  <div className="progress-caption">
                    <span>Transfer candidate bytes</span>
                    <strong>
                      {ratio === null
                        ? "Total unknown"
                        : `${ratio.toFixed(0)}%`}
                    </strong>
                  </div>
                  <progress
                    max={100}
                    value={ratio ?? undefined}
                    aria-label={`Transfer progress for ${id}`}
                  />
                  <div className="progress-stats">
                    <span>
                      {bytes(job.candidate_bytes)} /{" "}
                      {bytes(job.total_expected_bytes || null)}
                    </span>
                    <span>Verified {bytes(job.verified_bytes)}</span>
                  </div>
                  <p className="field-hint">
                    {job.current_component
                      ? `Component: ${job.current_component}`
                      : "No component reported"}{" "}
                    · Generation unavailable
                  </p>
                  {job.cancel_requested && (
                    <Notice>
                      Cancellation requested; waiting for the backend to confirm
                      it.
                    </Notice>
                  )}
                  {job.error && (
                    <Notice danger>
                      {job.error.message} ({job.error.code})
                    </Notice>
                  )}
                  <div className="job-actions">
                    {!terminal.has(job.state) && (
                      <button
                        className="button secondary"
                        disabled={
                          !keySet ||
                          job.state === "installing" ||
                          job.cancel_requested ||
                          cancelling === id
                        }
                        onClick={() => void cancel(id)}
                      >
                        {job.state === "installing"
                          ? "Commit in progress"
                          : cancelling === id
                            ? "Requesting cancellation…"
                            : "Cancel job"}
                      </button>
                    )}
                    <button className="text-button" onClick={() => forget(id)}>
                      Forget from this tab
                    </button>
                  </div>
                </>
              )}
              {!job && (
                <button className="text-button" onClick={() => forget(id)}>
                  Forget from this tab
                </button>
              )}
            </Panel>
          );
        })}
      </div>
      <ManagerAuthorization api={api} onChange={setKeySet} />
    </>
  );
}
