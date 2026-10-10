import { useEffect, useRef, useState } from "react";
import type { DirectorApi } from "../api/client";
import type { GenerationJob } from "../api/types";
import { ManagerAuthorization } from "./ManagerAuthorization";
import { DevelopmentResult } from "./DevelopmentResult";
import { Badge, Notice, PageHeading, Panel } from "./ui";

export function DevelopmentGenerate({ api }: { api: DirectorApi }) {
  const [enabled, setEnabled] = useState(false);
  const [checking, setChecking] = useState(true);
  const [authorized, setAuthorized] = useState(api.hasKey());
  const [prompt, setPrompt] = useState("");
  const [seed, setSeed] = useState("20261009");
  const [job, setJob] = useState<GenerationJob | undefined>(
    api.currentGeneration,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [video, setVideo] = useState("");
  const active = useRef(false);
  const pending = useRef<AbortController | null>(null);
  const videoUrl = useRef("");
  useEffect(() => {
    const controller = new AbortController();
    api
      .generationConfig(controller.signal)
      .then((config) => setEnabled(config.enabled))
      .catch((e: Error) => {
        if (!controller.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setChecking(false);
      });
    return () => {
      controller.abort();
      pending.current?.abort();
      if (videoUrl.current) URL.revokeObjectURL(videoUrl.current);
    };
  }, [api]);
  async function follow(id: string, signal: AbortSignal) {
    while (!signal.aborted) {
      const current = await api.generationJob(id, signal);
      setJob(current);
      if (current.state === "completed") {
        const blob = await api.generationOutput(id, signal);
        if (signal.aborted) return;
        if (videoUrl.current) URL.revokeObjectURL(videoUrl.current);
        videoUrl.current = URL.createObjectURL(blob);
        setVideo(videoUrl.current);
        return;
      }
      if (["failed", "cancelled"].includes(current.state)) return;
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
  }
  async function run(resume = false) {
    if (active.current) return;
    active.current = true;
    setBusy(true);
    setError("");
    if (!resume) {
      if (videoUrl.current) URL.revokeObjectURL(videoUrl.current);
      videoUrl.current = "";
      setVideo("");
      setJob(undefined);
    }
    const controller = new AbortController();
    pending.current = controller;
    try {
      const current =
        resume && job
          ? job
          : await api.generate(prompt, Number(seed), controller.signal);
      setJob(current);
      await follow(current.id, controller.signal);
    } catch (e) {
      if (!controller.signal.aborted)
        setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      active.current = false;
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  const tracking = job && ["queued", "running"].includes(job.state);
  const validSeed = /^\d+$/.test(seed) && Number.isSafeInteger(Number(seed));
  return (
    <>
      <PageHeading
        eyebrow="DEVELOPMENT WORKSPACE"
        title="Generate video"
        action={<Badge tone="amber">Local development only</Badge>}
      >
        Validated Wan 2.1 T2V-1.3B workflow. Native Windows production remains
        disabled.
      </PageHeading>
      <ManagerAuthorization api={api} onChange={setAuthorized} />
      <div className="generate-grid">
        <Panel className="prompt-panel">
          <h2>Scene setup</h2>
          <Notice>
            Fixed text-to-video test: 320×192 · 17 frames · 8 steps · 16 fps.
            Image-to-video is unavailable.
          </Notice>
          <label className="field">
            Your prompt
            <textarea
              rows={6}
              maxLength={2000}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={busy || !!tracking}
            />
          </label>
          <label className="field">
            Seed
            <input
              type="number"
              min="0"
              max="9007199254740991"
              step="1"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              disabled={busy || !!tracking}
            />
          </label>
          {checking && <p role="status">Checking development adapter…</p>}
          {!checking && !enabled && (
            <Notice>Development generation is disabled on the backend.</Notice>
          )}
          {!authorized && (
            <p className="field-hint">
              Enter your local manager key before generating.
            </p>
          )}
          <button
            className="button primary generate-button"
            disabled={
              !enabled ||
              !authorized ||
              !prompt.trim() ||
              !validSeed ||
              busy ||
              !!tracking
            }
            onClick={() => void run()}
          >
            Generate video
          </button>
          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
          {job && (
            <button
              className="button secondary"
              disabled={busy || !authorized}
              onClick={() => void run(true)}
            >
              Refresh status / preview
            </button>
          )}
          <p className="field-hint">
            Leaving this page stops monitoring, not ComfyUI execution. No
            automatic retries or new submissions.
          </p>
        </Panel>
        <Panel className="preview-panel">
          <div className="panel-heading">
            <h2>Preview</h2>
            <Badge>Local output</Badge>
          </div>
          <p role="status" aria-live="polite">
            {job ? `${job.state}: ${job.message}` : "No generation submitted"}
          </p>
          {job && <p className="field-hint">Job {job.id}</p>}
          {job?.progress !== null && job?.progress !== undefined && (
            <progress
              aria-label="Generation progress"
              value={job.progress}
              max={1}
            />
          )}
          {busy && <p>Tracking ComfyUI. Step percentage is unavailable.</p>}
          {video ? (
            <video
              aria-label="Generated video"
              controls
              src={video}
              style={{ width: "100%" }}
            />
          ) : (
            <div className="preview-stage">
              <p>Your completed video will appear here.</p>
            </div>
          )}
          {job?.output_filename && (
            <p className="field-hint">{job.output_filename}</p>
          )}
        </Panel>
      </div>
      {job?.state === "completed" && (
        <DevelopmentResult
          key={job.id}
          api={api}
          jobId={job.id}
          authorized={authorized}
        />
      )}
    </>
  );
}
