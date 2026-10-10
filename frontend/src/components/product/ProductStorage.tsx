import { useEffect, useState } from "react";
import type { DirectorApi } from "../../api/client";
import type { StorageReport } from "../../api/product";
import { Panel, bytes } from "../ui";
import { message } from "./message";
export function ProductStorage({
  api,
  authorized,
}: {
  api: DirectorApi;
  authorized: boolean;
}) {
  const [data, setData] = useState<StorageReport>();
  const [plan, setPlan] =
    useState<Awaited<ReturnType<DirectorApi["cachePlan"]>>>();
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!authorized) return;
    let live = true;
    api
      .storage()
      .then((d) => {
        if (live) setData(d);
      })
      .catch((e) => {
        if (live) setError(message(e));
      });
    return () => {
      live = false;
    };
  }, [api, authorized]);
  return (
    <>
      <h1>Storage</h1>
      <p>
        Director-owned space. User videos are never removed by model cleanup.
      </p>
      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Measuring owned directories·</p>}
      {data && (
        <>
          <Panel>
            <h2>{bytes(data.free_bytes)} available</h2>
            {data.low_disk && (
              <p role="alert">
                Low disk space. Review a specific model removal plan before
                downloading anything.
              </p>
            )}
            <div className="product-controls">
              {Object.entries(data.categories).map(([name, c]) => (
                <div key={name}>
                  <h3>{name.replaceAll("_", " ")}</h3>
                  <p>
                    {bytes(c.bytes)}
                    {!c.complete ? " · partial measurement" : ""}
                  </p>
                  <meter
                    aria-label={`${name} storage share`}
                    min={0}
                    max={Math.max(
                      1,
                      ...Object.values(data.categories).map((c) => c.bytes),
                    )}
                    value={c.bytes}
                  />
                  {c.warnings.map((w) => (
                    <p key={w}>{w}</p>
                  ))}
                </div>
              ))}
            </div>
          </Panel>
          <Panel>
            <h2>Cache and orphan review</h2>
            <p>{data.cleanup_policy}</p>
            <p>
              Automatic cache clearing is disabled. Unknown or unregistered
              files cannot be classified as disposable from their names.
            </p>
            <a href="#model-store">Review exact model removal</a>
            <button
              className="button secondary"
              onClick={() =>
                void api
                  .cachePlan()
                  .then((p) => {
                    setPlan(p);
                    setConfirmed(false);
                  })
                  .catch((e) => setError(message(e)))
              }
            >
              Review unused registered cache
            </button>
            {plan && (
              <>
                <p>
                  {bytes(plan.reclaim_bytes)} can be reclaimed from{" "}
                  {plan.files.length} exact registered files. Unknown and shared
                  files are preserved.
                </p>
                <ul>
                  {plan.files.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
                {plan.blockers.map((b) => (
                  <p key={b}>{b}</p>
                ))}
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={confirmed}
                    onChange={(e) => setConfirmed(e.target.checked)}
                  />
                  I explicitly approve removing only these unused cache files.
                </label>
                <button
                  className="button secondary"
                  disabled={
                    !confirmed || !plan.files.length || !!plan.blockers.length
                  }
                  onClick={() =>
                    void api
                      .clearOwnedCache(plan.digest)
                      .then(() => {
                        setPlan(undefined);
                        return api.storage();
                      })
                      .then(setData)
                      .catch((e) => setError(message(e)))
                  }
                >
                  Remove reviewed cache
                </button>
              </>
            )}
          </Panel>
        </>
      )}
    </>
  );
}
