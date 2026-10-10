import { useState } from "react";
import type { DirectorApi } from "../api/client";
import type { ResolveResult } from "../api/types";
import { DevelopmentTimeline } from "./DevelopmentTimeline";

export function DevelopmentResult({
  api,
  jobId,
  authorized,
}: {
  api: DirectorApi;
  jobId: string;
  authorized: boolean;
}) {
  const [result, setResult] = useState<ResolveResult>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [importAttempted, setImportAttempted] = useState(false);
  async function update(importing = false) {
    if (busy) return;
    setBusy(true);
    setError("");
    if (importing) setImportAttempted(true);
    try {
      const next = importing
        ? await api.importToResolve(jobId)
        : await api.resolveResult(jobId);
      setResult(next);
      if (!importing) setImportAttempted(next.state !== "generated");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Resolve operation failed");
    } finally {
      setBusy(false);
    }
  }
  const imported = result && ["imported", "placed"].includes(result.state);
  const attempted = result && !["generated"].includes(result.state);
  return (
    <>
      <p role="status">
        {busy
          ? "Converting / contacting Resolve…"
          : result
            ? `${result.state}: ${result.message ?? "Review result"}`
            : "Generated. Import this result to Resolve when ready."}
      </p>
      <button
        className="button primary"
        disabled={!authorized || busy || importAttempted || !!attempted}
        onClick={() => void update(true)}
      >
        Import to Resolve
      </button>
      <button
        className="button secondary"
        disabled={!authorized || busy}
        onClick={() => void update()}
      >
        Refresh Resolve result
      </button>
      {error && (
        <p role="alert" className="inline-error">
          {error}
        </p>
      )}
      {imported && (
        <p>
          Resolve-compatible MP4: {result.filename}. Media Pool item:{" "}
          {result.media_id}.
        </p>
      )}
      {result?.state === "imported" && (
        <DevelopmentTimeline
          api={api}
          authorized={authorized}
          jobId={jobId}
          onPlaced={() => void update()}
        />
      )}
      {result?.state === "placed" && (
        <p>Placed on {result.placement?.timeline}.</p>
      )}
    </>
  );
}
