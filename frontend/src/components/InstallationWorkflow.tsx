import { useCallback, useEffect, useState } from "react";
import type { DirectorApi } from "../api/client";
import type {
  InstallationJob,
  InstallationPlan,
  LicenseRequirements,
  RegisteredModel,
} from "../api/types";
import { useResource } from "../hooks/useResource";
import { ReviewDialog } from "./ReviewDialog";
import { Badge, bytes, ErrorState, Loading, Notice, stateLabel } from "./ui";

const terminal = new Set([
  "ready",
  "failed",
  "cancelled",
  "corrupted",
  "not_installed",
]);
const message = (error: unknown) =>
  error instanceof Error ? error.message : "Operation failed";

export function InstallationWorkflow({
  api,
  item,
  plan,
  authorized,
  allowFixture,
  remember,
  onComplete,
}: {
  api: DirectorApi;
  item: RegisteredModel;
  plan?: InstallationPlan;
  authorized: boolean;
  allowFixture: boolean;
  remember: (id: string) => void;
  onComplete: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [job, setJob] = useState<InstallationJob>();
  const [error, setError] = useState("");
  const [cancelling, setCancelling] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const fixture =
    allowFixture &&
    item.manifest.is_fixture &&
    item.manifest.id === "fixture-tiny";
  const review = plan?.artifact_review;
  const eligible =
    fixture && review?.can_review && review.blockers.length === 0;
  const jobId = job?.id;
  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await api.job(jobId!, controller.signal);
        if (controller.signal.aborted) return;
        if (next.id !== jobId || next.model_id !== item.manifest.id)
          throw new Error("Unexpected installation job identity.");
        setJob(next);
        setError("");
        if (terminal.has(next.state)) onComplete();
        else timer = setTimeout(() => void poll(), 2000);
      } catch (failure) {
        if (!controller.signal.aborted)
          setError(
            `${message(failure)} Check Jobs before starting another attempt.`,
          );
      }
    }
    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [api, jobId, item.manifest.id, onComplete, refresh]);
  async function cancel() {
    setCancelling(true);
    try {
      setJob(await api.cancel(job!.id));
      setRefresh((value) => value + 1);
    } catch (failure) {
      setError(message(failure));
    } finally {
      setCancelling(false);
    }
  }
  return (
    <div className="detail-section">
      <span className="eyebrow">ARTIFACT INSTALLATION</span>
      {review ? (
        <>
          <p>
            {review.can_review
              ? "Artifact metadata can be reviewed. Your acknowledgement and confirmation are still required."
              : "Artifact installation is blocked."}
          </p>
          <p className="field-hint">
            Manager storage budget: {bytes(review.required_storage_bytes)} ·
            includes cache, staging and a safety margin.
          </p>
          <p className="field-hint break-word">
            Destination: {review.destination_template}
          </p>
          {review.blockers.map((issue) => (
            <Notice danger key={issue.code}>
              {issue.message}
            </Notice>
          ))}
        </>
      ) : (
        <Notice>
          Waiting for a valid backend artifact preflight. Installation remains
          disabled.
        </Notice>
      )}
      <Notice>
        {fixture
          ? "Development test fixture — excluded from generation choices. Its fictional hardware requirements do not apply to copying this test file."
          : "Real-model installation, including Wan, is disabled in this milestone."}{" "}
        Artifact files and generation readiness are separate.
      </Notice>
      <button
        className="button secondary full-width"
        disabled={
          !eligible || !authorized || (!!job && !terminal.has(job.state))
        }
        onClick={() => {
          setError("");
          setOpen(true);
        }}
      >
        Review license and installation
      </button>
      {!authorized && (
        <p className="field-hint">
          Enter your manager key above to review and authorize a privileged
          operation.
        </p>
      )}
      {error && <Notice danger>{error}</Notice>}
      {job && (
        <section
          aria-label="Current installation job"
          aria-live="polite"
          className="installation-progress"
        >
          <Badge
            tone={
              job.state === "ready"
                ? "green"
                : job.state === "failed"
                  ? "red"
                  : "muted"
            }
          >
            {stateLabel(job.state)}
          </Badge>
          <p className="break-word">
            Job <code>{job.id}</code>
          </p>
          <label>
            Transfer candidate bytes{" "}
            <progress
              aria-label="Installation transfer progress"
              max={job.total_expected_bytes || 1}
              value={job.candidate_bytes}
            />
          </label>
          <p>
            {bytes(job.candidate_bytes)} / {bytes(job.total_expected_bytes)}{" "}
            transferred · {bytes(job.verified_bytes)} verified
          </p>
          <progress
            aria-label="Installation verification progress"
            max={job.total_expected_bytes || 1}
            value={job.verified_bytes}
          />
          <p>
            {job.state === "ready"
              ? "Fixture files installed and verified. Generation remains unavailable."
              : "Transfer progress is not proof of valid files."}
          </p>
          {job.error && (
            <Notice danger>
              {job.error.message} ({job.error.code})
            </Notice>
          )}
          {job.cancel_requested && (
            <Notice>
              Cancellation requested; waiting for backend confirmation.
              Transfers may stop only at supported checkpoints.
            </Notice>
          )}
          {!terminal.has(job.state) && (
            <button
              className="button secondary"
              disabled={
                !authorized ||
                cancelling ||
                job.cancel_requested ||
                job.state === "installing"
              }
              onClick={() => void cancel()}
            >
              Cancel installation
            </button>
          )}
          <button
            className="text-button"
            onClick={() => setRefresh((value) => value + 1)}
          >
            Refresh job status
          </button>
          <a href="#jobs">View in Jobs</a>
        </section>
      )}
      {open && (
        <InstallationReview
          api={api}
          modelId={item.manifest.id}
          onClose={() => setOpen(false)}
          onStarted={(next) => {
            remember(next.id);
            setJob(next);
            setOpen(false);
          }}
        />
      )}
    </div>
  );
}

function InstallationReview({
  api,
  modelId,
  onClose,
  onStarted,
}: {
  api: DirectorApi;
  modelId: string;
  onClose: () => void;
  onStarted: (job: InstallationJob) => void;
}) {
  // Refresh snapshots whenever review opens. No old acknowledgement is reused.
  const load = useCallback(
    async (signal: AbortSignal) => {
      const [plan, license] = await Promise.all([
        api.plan(modelId, signal),
        api.licenses(modelId, signal),
      ]);
      if (plan.model_id !== modelId || license.model_id !== modelId)
        throw new Error("Unexpected model identity in review response.");
      return { plan, license };
    },
    [api, modelId],
  );
  const data = useResource(load);
  const [accepted, setAccepted] = useState(false);
  const [acknowledgement, setAcknowledgement] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ambiguous, setAmbiguous] = useState(false);
  const snapshot = data.data;
  const review = snapshot?.plan.artifact_review;
  const allowed =
    review?.can_review &&
    review.blockers.length === 0 &&
    api.hasKey() &&
    !!snapshot?.license.license_info;
  async function acknowledge(license: LicenseRequirements) {
    setBusy(true);
    setError("");
    try {
      const ack = await api.acknowledge(modelId, license.document_set_digest);
      if (
        ack.model_id !== modelId ||
        ack.document_set_digest !== license.document_set_digest
      )
        throw new Error("Acknowledgement does not match reviewed documents.");
      setAcknowledgement(ack.id);
    } catch (failure) {
      setError(message(failure));
    } finally {
      setBusy(false);
    }
  }
  async function install() {
    setBusy(true);
    setError("");
    let requested = false;
    try {
      const latest = await api.plan(modelId);
      if (
        latest.model_id !== modelId ||
        !latest.artifact_review?.can_review ||
        latest.artifact_review.blockers.length
      )
        throw new Error(
          "Installation preflight changed or is blocked. Close and review again.",
        );
      if (
        JSON.stringify(latest.artifact_review) !== JSON.stringify(review) ||
        JSON.stringify(latest.components) !==
          JSON.stringify(snapshot!.plan.components)
      )
        throw new Error(
          "Installation details changed. Close and review again.",
        );
      requested = true;
      const next = await api.install(
        modelId,
        snapshot!.license.manifest_digest,
        acknowledgement,
      );
      if (next.model_id !== modelId || !/^[0-9a-f]{32}$/.test(next.id))
        throw new Error("Unexpected installation job identity.");
      onStarted(next);
    } catch (failure) {
      setError(
        `${message(failure)}${requested ? " Check model status and Jobs before retrying; the request may have reached the backend." : ""}`,
      );
      // Never automatically retry a mutation after an uncertain response.
      if (requested) setAmbiguous(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <ReviewDialog onClose={onClose} busy={busy}>
      {data.loading ? (
        <Loading text="Refreshing plan and reviewed license documents…" />
      ) : data.error ? (
        <ErrorState error={data.error} retry={data.reload} />
      ) : (
        snapshot && (
          <>
            <div className="detail-section">
              <h3>1. Review the read-only plan</h3>
              <dl className="detail-list">
                <div>
                  <dt>Expected file bytes</dt>
                  <dd>{bytes(review?.expected_download_bytes ?? null)}</dd>
                </div>
                <div>
                  <dt>Storage budget</dt>
                  <dd>{bytes(review?.required_storage_bytes ?? null)}</dd>
                </div>
                <div>
                  <dt>Drive free</dt>
                  <dd>{bytes(snapshot.plan.storage.free_bytes)}</dd>
                </div>
              </dl>
              <p className="break-word">
                {review?.destination_template ?? "Destination unknown"}
              </p>
              {snapshot.plan.components.map(({ component }) => (
                <p className="break-word" key={component.id}>
                  <code>{component.destination}</code> ·{" "}
                  {bytes(component.expected_size_bytes)}
                </p>
              ))}
              {review?.blockers.map((issue) => (
                <Notice danger key={issue.code}>
                  {issue.message}
                </Notice>
              ))}
              <details>
                <summary>
                  Generation prerequisites and compatibility warnings
                </summary>
                {snapshot.plan.blockers.map((issue, index) => (
                  <Notice key={index}>{issue.message}</Notice>
                ))}
                {snapshot.plan.warnings.map((warning, index) => (
                  <p key={index}>{warning}</p>
                ))}
                <p>
                  These combined generation prerequisites remain unresolved. The
                  backend separately permits copying the offline fixture only.
                </p>
              </details>
            </div>
            <div className="detail-section">
              <h3>2. Read and acknowledge the license</h3>
              <p>
                {snapshot.license.license_info?.identifier ??
                  "License information incomplete"}
              </p>
              {!snapshot.license.license_info && (
                <Notice danger>
                  License information is incomplete. Acknowledgement and
                  installation remain disabled.
                </Notice>
              )}
              <p className="field-hint">
                Source: bundled synthetic fixture document, versioned and hashed
                by Director. No publisher license is implied.
              </p>
              {snapshot.license.documents.map((document) => (
                <section key={document.id}>
                  <h4>
                    {document.id} · version {document.version}
                  </h4>
                  {document.source && /^https?:\/\//.test(document.source) && (
                    <a href={document.source} target="_blank" rel="noreferrer">
                      Authoritative document source ↗
                    </a>
                  )}
                  <pre className="license-document">{document.text}</pre>
                  <p className="field-hint break-word">
                    SHA-256: {document.sha256}
                  </p>
                </section>
              ))}
              {[
                ...(snapshot.license.license_info?.usage_restrictions ?? []),
                ...(snapshot.license.license_info
                  ?.acknowledgement_requirements ?? []),
              ].map((text, index) => (
                <p key={index}>{text}</p>
              ))}
              <label className="acknowledgement">
                <input
                  type="checkbox"
                  checked={accepted}
                  disabled={busy || !!acknowledgement}
                  onChange={(event) => setAccepted(event.target.checked)}
                />
                I have read these fixture terms and acknowledge that this is a
                test file, not an AI model.
              </label>
              <button
                className="button secondary"
                disabled={!allowed || !accepted || busy || !!acknowledgement}
                onClick={() => void acknowledge(snapshot.license)}
              >
                {acknowledgement
                  ? "Acknowledgement recorded"
                  : "Record acknowledgement"}
              </button>
            </div>
            <div className="detail-section">
              <h3>3. Confirm installation</h3>
              <p>
                Confirm to copy {bytes(review?.expected_download_bytes ?? null)}{" "}
                into the Director-owned destination above. No Hugging Face
                connection will be made. Generation stays disabled.
              </p>
              <button
                className="button primary"
                disabled={!allowed || !acknowledgement || busy || ambiguous}
                onClick={() => void install()}
              >
                {busy ? "Waiting for backend…" : "Confirm offline installation"}
              </button>
            </div>
          </>
        )
      )}
      {error && <Notice danger>{error}</Notice>}
    </ReviewDialog>
  );
}
