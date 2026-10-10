import { useState } from "react";
import type { DirectorApi } from "../api/client";
import type { ResolveTimelines } from "../api/types";
import { Panel } from "./ui";

export function DevelopmentTimeline({
  api,
  authorized,
  jobId,
  onPlaced,
}: {
  api: DirectorApi;
  authorized: boolean;
  jobId?: string;
  onPlaced?: () => void;
}) {
  const [review, setReview] = useState<ResolveTimelines>();
  const [selected, setSelected] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [placed, setPlaced] = useState(false);
  async function inspect() {
    setBusy(true);
    setError("");
    setConfirmed(false);
    setReview(undefined);
    try {
      const next = await api.resolveTimelines();
      setReview(next);
      setSelected(next.current_timeline_id ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Resolve unavailable");
    } finally {
      setBusy(false);
    }
  }
  async function place() {
    if (!review || !confirmed || busy || placed) return;
    const target = review.timelines.find((t) => t.id === selected);
    setBusy(true);
    setError("");
    try {
      const body = {
        confirmed: true,
        create_new: review.timelines.length === 0,
        timeline_id: target?.id ?? null,
        timeline_name: target?.name ?? "Director AI Test",
      };
      const result = jobId
        ? (await api.placeResolveJob(jobId, body)).placement!
        : await api.addToTimeline(body);
      setMessage(
        `Placed the ${jobId ? "generated" : "Stage 9"} clip on ${result.timeline} (${result.duration_seconds.toFixed(3)} seconds).`,
      );
      setPlaced(true);
      onPlaced?.();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Placement failed. Inspect Resolve before retrying.",
      );
      setConfirmed(false);
      setReview(undefined);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Panel>
      <h2>Development timeline placement</h2>
      <p>
        {jobId
          ? "Review the target for this newly generated, imported clip. No other media will be inserted."
          : "Only the verified, already imported Stage 9 clip is supported. This does not import the current preview or other media."}
      </p>
      <button
        className="button secondary"
        disabled={!authorized || busy || placed}
        onClick={() => void inspect()}
      >
        Review Resolve timelines
      </button>
      {review && (
        <>
          <p>Project: {review.project}</p>
          {review.timelines.length ? (
            <label className="field">
              Target timeline
              <select
                value={selected}
                onChange={(e) => {
                  setSelected(e.target.value);
                  setConfirmed(false);
                }}
              >
                <option value="">Select a timeline</option>
                {review.timelines.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p>No timelines exist. Create “Director AI Test”.</p>
          )}
          <label>
            <input
              type="checkbox"
              checked={confirmed}
              disabled={busy || placed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />{" "}
            I approve inserting the one {jobId ? "generated" : "Stage 9"} clip
            into this timeline
            {review.timelines.length === 0
              ? " and creating Director AI Test"
              : ""}
            .
          </label>
          <button
            className="button primary"
            disabled={
              !authorized ||
              busy ||
              placed ||
              !confirmed ||
              (review.timelines.length > 0 && !selected)
            }
            onClick={() => void place()}
          >
            Add to Timeline
          </button>
        </>
      )}
      {busy && <p role="status">Contacting Resolve…</p>}
      {message && <p role="status">{message}</p>}
      {review && !placed && (
        <button
          className="button secondary"
          disabled={busy}
          onClick={() => {
            setReview(undefined);
            setConfirmed(false);
            setMessage("Placement declined; no timeline change requested.");
          }}
        >
          Decline placement
        </button>
      )}
      {error && (
        <p role="alert" className="inline-error">
          {error}
        </p>
      )}
    </Panel>
  );
}
