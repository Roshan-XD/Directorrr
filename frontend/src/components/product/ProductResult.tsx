import { useEffect, useState } from "react";
import type { DirectorApi } from "../../api/client";
import type { ProductJob } from "../../api/product";
import { DevelopmentResult } from "../DevelopmentResult";
import { Badge } from "../ui";
import { message } from "./message";
export function ProductResult({
  api,
  job,
  authorized,
}: {
  api: DirectorApi;
  job: ProductJob;
  authorized: boolean;
}) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let local = "";
    const controller = new AbortController();
    setUrl("");
    setError("");
    if (job.state === "completed")
      api
        .generationOutput(job.id, controller.signal)
        .then((blob) => {
          if (!controller.signal.aborted) {
            local = URL.createObjectURL(blob);
            setUrl(local);
          }
        })
        .catch((e) => {
          if (!controller.signal.aborted) setError(message(e));
        });
    return () => {
      controller.abort();
      if (local) URL.revokeObjectURL(local);
    };
  }, [api, job.id, job.state]);
  return (
    <>
      <Badge>{job.state}</Badge>
      {job.state === "completed" && (
        <a className="text-button" href="#library">
          Open saved result Library
        </a>
      )}
      <p role="status">{job.message}</p>
      {job.progress !== null && <progress value={job.progress} max={1} />}
      {error && <p role="alert">{error}</p>}
      {url && (
        <>
          <video
            controls
            preload="metadata"
            src={url}
            aria-label="Generated scene preview"
          />
          <a
            className="button secondary"
            href={url}
            target="_blank"
            rel="noreferrer"
          >
            Open video
          </a>
          <a
            className="button secondary"
            href={url}
            download={job.output_filename || "Director.webm"}
          >
            Save video
          </a>
        </>
      )}
      {job.state === "completed" &&
        job.creative?.model_id !== "minimax-h3-optimized" && (
          <DevelopmentResult
            key={job.id}
            api={api}
            jobId={job.id}
            authorized={authorized}
          />
        )}
      {job.state === "completed" &&
        job.creative?.model_id === "minimax-h3-optimized" && (
          <p>
            Native audio/video MP4 is ready for preview and saving. H3 Resolve
            audio handoff is not yet validated.
          </p>
        )}
    </>
  );
}
