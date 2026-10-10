import type {
  Capability,
  CreativeRequest,
  ProductJob,
} from "../../api/product";
import { Panel } from "../ui";

export interface PlannedShot {
  id: number;
  settings: CreativeRequest;
  notes: string;
  previousJob: string;
}

// Creative planning is local session state. It never queues conditioned inference.
export function ShotPlanner({
  model,
  draft,
  jobs,
  shots,
  onChange,
}: {
  model: Capability;
  draft?: CreativeRequest;
  jobs: ProductJob[];
  shots: PlannedShot[];
  onChange: (shots: PlannedShot[]) => void;
}) {
  const update = (id: number, patch: Partial<PlannedShot>) =>
    onChange(
      shots.map((shot) => (shot.id === id ? { ...shot, ...patch } : shot)),
    );
  return (
    <Panel>
      <details>
        <summary>Plan a sequence of shots</summary>
        <p>
          Planning only, kept for this browser session. Adding a shot starts no
          generation. Continuity execution needs a separately validated model
          adapter.
          {model.continuation === "none" &&
            " Wan does not support conditioned continuation."}
        </p>
        <button
          className="button secondary"
          disabled={!draft?.prompt.trim() || shots.length >= 12}
          onClick={() => {
            if (draft)
              onChange([
                ...shots,
                {
                  id: Math.max(0, ...shots.map((shot) => shot.id)) + 1,
                  settings: { ...draft },
                  notes: "",
                  previousJob: "",
                },
              ]);
          }}
        >
          Add current shot to plan
        </button>
        {!shots.length && <p>No planned shots. Enter a prompt first.</p>}
        <div className="model-grid">
          {shots.map((shot, index) => (
            <section
              className="shot-card"
              key={shot.id}
              aria-label={`Planned shot ${index + 1}`}
            >
              <h3>Shot {String(index + 1).padStart(2, "0")}</h3>
              <p>{shot.settings.prompt}</p>
              <p>
                {shot.settings.model_id} · approximately{" "}
                {shot.settings.duration}s · {shot.settings.resolution}
              </p>
              <p>
                {shot.settings.camera} camera · {shot.settings.quality} · seed{" "}
                {shot.settings.seed ?? "random"}
              </p>
              <label className="field">
                Continuity notes
                <textarea
                  value={shot.notes}
                  maxLength={1000}
                  onChange={(event) =>
                    update(shot.id, { notes: event.target.value })
                  }
                />
              </label>
              <label className="field">
                Previous completed clip (planning reference)
                <select
                  value={shot.previousJob}
                  onChange={(event) =>
                    update(shot.id, { previousJob: event.target.value })
                  }
                >
                  <option value="">None</option>
                  {jobs
                    .filter((job) => job.state === "completed")
                    .map((job, i) => (
                      <option key={job.id} value={job.id}>
                        Completed scene {i + 1}
                      </option>
                    ))}
                </select>
              </label>
              <button className="button secondary" disabled>
                Continue previous shot · adapter validation required
              </button>
              <button
                className="text-button"
                onClick={() =>
                  onChange(shots.filter((item) => item.id !== shot.id))
                }
              >
                Remove from plan
              </button>
            </section>
          ))}
        </div>
      </details>
    </Panel>
  );
}
