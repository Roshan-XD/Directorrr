import { useState } from "react";
import { H3InstallReview } from "./H3InstallReview";
import { OptimizedH3Install } from "./OptimizedH3Install";
import type { DirectorApi } from "../../api/client";
import type {
  Capability,
  DiscoveryResult,
  ModelCard,
  RemovalPlan,
} from "../../api/product";
import { Badge, Panel, bytes } from "../ui";
import { message } from "./message";
import type { DownloadPlan } from "../../api/studio";
import type { ModelFiles } from "../../api/studio";
export function ProductModelStore({
  api,
  models,
  disabled,
  useModel,
  changed,
  act,
}: {
  api: DirectorApi;
  models: Capability[];
  disabled: boolean;
  useModel: (id: string) => void;
  changed: () => Promise<void>;
  act: (a: () => Promise<unknown>) => Promise<void>;
}) {
  const [query, setQuery] = useState("");
  const [discovery, setDiscovery] = useState<DiscoveryResult>();
  const [error, setError] = useState("");
  const [searching, setSearching] = useState(false);
  const [card, setCard] = useState<ModelCard>();
  const [detail, setDetail] = useState<Capability>();
  const [plan, setPlan] = useState<RemovalPlan>();
  const [confirmed, setConfirmed] = useState(false);
  const [author, setAuthor] = useState("");
  const [task, setTask] = useState("");
  const [sort, setSort] = useState("downloads");
  const [files, setFiles] = useState<string[]>([]);
  const [download, setDownload] = useState<DownloadPlan>();
  const [downloadConsent, setDownloadConsent] = useState(false);
  const [inventory, setInventory] = useState<ModelFiles>();
  const [inspection, setInspection] = useState("");
  const [catalogFilter, setCatalogFilter] = useState("all");
  async function search(cursor?: string) {
    setSearching(true);
    setError("");
    try {
      const result = await api.discover(query, {
        author,
        task,
        sort,
        ...(cursor ? { cursor } : {}),
      });
      setDiscovery((old) =>
        cursor && old
          ? {
              ...result,
              items: [
                ...old.items,
                ...result.items.filter(
                  (i) => !old.items.some((o) => o.id === i.id),
                ),
              ],
            }
          : result,
      );
    } catch (e) {
      setError(message(e));
    } finally {
      setSearching(false);
    }
  }
  return (
    <>
      <h1>Model Store</h1>
      <p>
        Installed models are available offline. Browse published models without
        downloading their weights.
      </p>
      <div className="model-grid">
        {models
          .filter(
            (m) =>
              catalogFilter === "all" ||
              (catalogFilter === "installed" && m.installed) ||
              (catalogFilter === "ready" && m.runnable) ||
              (catalogFilter === "adapter" && !m.adapter),
          )
          .map((m) => (
            <Panel key={m.id}>
              <div className="model-art" aria-hidden="true" />
              <Badge tone={m.runnable ? "green" : "neutral"}>
                {m.runnable
                  ? "Ready for local generation"
                  : m.installed
                    ? "Downloaded · adapter unavailable"
                    : "Candidate · not installed"}
              </Badge>
              <h2>{m.name}</h2>
              {m.id === "minimax-h3-optimized" && !m.installed && (
                <OptimizedH3Install
                  api={api}
                  changed={changed}
                  disabled={disabled}
                />
              )}
              <p>
                {m.workspaces.join(" · ")} ·{" "}
                {m.native_audio ? "Native audio published" : "Silent video"}
              </p>
              <p>
                {m.model_bytes
                  ? bytes(m.model_bytes)
                  : "See exact download plan"}
              </p>
              <button
                className="button secondary"
                onClick={() => {
                  setDetail(m);
                  setInventory(undefined);
                  setInspection("");
                  setPlan(undefined);
                  setConfirmed(false);
                }}
              >
                Model details
              </button>
              <button
                className="button primary"
                disabled={!m.runnable}
                onClick={() => useModel(m.id)}
              >
                Use model
              </button>
            </Panel>
          ))}
      </div>
      {detail && (
        <Panel>
          <div className="product-inline">
            <h2>{detail.name}</h2>
            <button
              className="text-button"
              onClick={() => {
                setDetail(undefined);
                setPlan(undefined);
              }}
            >
              Close details
            </button>
          </div>
          <p>
            Source:{" "}
            <a
              href={`https://huggingface.co/${detail.repository}`}
              target="_blank"
              rel="noreferrer"
            >
              {detail.repository}
            </a>
          </p>
          <p>
            <a href={detail.license_source} target="_blank" rel="noreferrer">
              Authoritative license
            </a>{" "}
            · licenses are never accepted automatically.
          </p>
          <p>
            Compatibility: {detail.compatibility}. Downloaded files and
            execution readiness are separate.
          </p>
          {detail.installed && (
            <div className="product-inline">
              <button
                className="text-button"
                onClick={() =>
                  void api
                    .modelFiles(detail.id)
                    .then(setInventory)
                    .catch((e) => setError(message(e)))
                }
              >
                View owned files
              </button>
              <button
                className="text-button"
                disabled={disabled}
                onClick={() =>
                  void act(async () => {
                    const report = await api.verifyModel(detail.id);
                    setInspection(
                      report.valid
                        ? "Exact current sizes and SHA-256 verified. This is artifact integrity, not a new inference test."
                        : "Artifact verification failed; inspect technical reports.",
                    );
                  })
                }
              >
                Verify artifacts
              </button>
              <button
                className="text-button"
                onClick={() =>
                  void api
                    .modelUpdates(detail.id)
                    .then((r) =>
                      setInspection(
                        `${r.message} ${JSON.stringify(r.components)}`,
                      ),
                    )
                    .catch((e) => setError(message(e)))
                }
              >
                Check repository updates
              </button>
            </div>
          )}
          {inspection && <p role="status">{inspection}</p>}
          {inventory && (
            <details open>
              <summary>Owned installation inventory</summary>
              <p>
                {inventory.location} · Last used{" "}
                {inventory.last_used ?? "not recorded"}
              </p>
              <p>{inventory.integrity}</p>
              {inventory.files.map((f) => (
                <p key={f.path}>
                  {f.path} · {bytes(f.bytes)} ·{" "}
                  {f.present ? "present" : "missing"} · shared references:{" "}
                  {f.shared_with.join(", ") || "none"}
                </p>
              ))}
            </details>
          )}
          {detail.evidence.map((e) => (
            <p key={e}>{e}</p>
          ))}
          {detail.blockers.map((b) => (
            <p className="notice" key={b}>
              {b}
            </p>
          ))}
          {detail.id === "minimax-h3" && <H3InstallReview api={api} />}
          {!detail.installed && detail.id !== "minimax-h3" && (
            <button className="button secondary" disabled>
              Install · blocked pending reviewed plan and approval
            </button>
          )}
          {detail.installed && (
            <button
              className="button secondary"
              disabled={disabled}
              onClick={() =>
                void act(async () => {
                  setPlan(await api.removalPlan(detail.id));
                  setConfirmed(false);
                })
              }
            >
              Review model removal
            </button>
          )}
          {plan && (
            <section role="region" aria-label="Model removal review">
              <h3>Remove only this model's owned assets?</h3>
              <p>
                Reclaim {bytes(plan.reclaim_bytes)}. Shared files preserved:{" "}
                {plan.shared_files.length}. Generated videos and runtime
                software are preserved.
              </p>
              <ul>
                {plan.files.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              {plan.blockers.map((b) => (
                <p role="alert" key={b}>
                  {b}
                </p>
              ))}
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                I reviewed these files and explicitly want to remove this model.
              </label>
              <button
                className="button secondary"
                disabled={disabled || !confirmed || !!plan.blockers.length}
                onClick={() =>
                  void act(async () => {
                    await api.removeModel(detail.id, plan.digest);
                    setPlan(undefined);
                    setDetail(undefined);
                    await changed();
                  })
                }
              >
                Confirm model removal
              </button>
              <button
                className="text-button"
                onClick={() => setPlan(undefined)}
              >
                Keep model
              </button>
            </section>
          )}
        </Panel>
      )}
      {card && (
        <Panel>
          <h2>{card.repository}</h2>
          {card.repository === "MiniMaxAI/MiniMax-H3" && (
            <H3InstallReview api={api} />
          )}
          <p>
            Published metadata, not compatibility validation. Revision{" "}
            {card.revision}
          </p>
          <p>
            Unknown repositories are inspectable as data. Generation requires a
            reviewed installed adapter.
          </p>
          <details>
            <summary>Select exact files for a data-only download plan</summary>
            {card.files.map((file) => (
              <label className="check-row" key={file.name}>
                <input
                  type="checkbox"
                  checked={files.includes(file.name)}
                  disabled={!files.includes(file.name) && files.length >= 32}
                  onChange={() => {
                    setDownload(undefined);
                    setFiles((old) =>
                      old.includes(file.name)
                        ? old.filter((n) => n !== file.name)
                        : [...old, file.name],
                    );
                  }}
                />
                {file.name} · {bytes(file.size)}
              </label>
            ))}
            <button
              className="button secondary"
              disabled={!files.length}
              onClick={() =>
                void api
                  .downloadPlan(card.repository, files)
                  .then((p) => {
                    setDownload(p);
                    setDownloadConsent(false);
                  })
                  .catch((e) => setError(message(e)))
              }
            >
              Review selected download
            </button>
          </details>
          {download && (
            <section aria-label="Download review">
              <h3>Data-only download review</h3>
              <p>
                {bytes(download.total_bytes)} download ·{" "}
                {bytes(download.required_free_bytes)} free-space reserve ·{" "}
                {download.destination}
              </p>
              {download.blockers.map((b) => (
                <p className="notice" key={b}>
                  {b}
                </p>
              ))}
              {download.warnings.map((b) => (
                <p key={b}>{b}</p>
              ))}
              <details>
                <summary>
                  Exact accompanying license · {download.license}
                </summary>
                <pre className="model-card-text">
                  {download.license_text ?? "License text unavailable"}
                </pre>
                <small>SHA-256 {download.license_sha256 ?? "unknown"}</small>
              </details>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={downloadConsent}
                  onChange={(e) => setDownloadConsent(e.target.checked)}
                />
                I reviewed the pinned files and accompanying terms and
                explicitly confirm this data transfer.
              </label>
              <button
                className="button primary"
                disabled={
                  !downloadConsent || !!download.blockers.length || disabled
                }
                onClick={() =>
                  void act(async () => {
                    await api.startDownload(download);
                    setDownload(undefined);
                    window.location.hash = "#downloads";
                  })
                }
              >
                Confirm download
              </button>
            </section>
          )}
          <p>{card.message}</p>
          <p>
            Publisher: {card.publisher} · {card.pipeline} · license:{" "}
            {card.license}
            {card.cached ? " · cached offline metadata" : ""}
          </p>
          <p>
            Updated: {card.updated ?? "Unknown"}. Tags:{" "}
            {card.tags.join(", ") || "Not published"}.
          </p>
          <p>
            Whole-repository size:{" "}
            {card.repository_bytes === null
              ? "Unknown"
              : bytes(card.repository_bytes)}
            . This includes all published variants; it is not a required
            download size.
          </p>
          <details>
            <summary>Published file inventory ({card.files.length})</summary>
            <ul>
              {card.files.map((file) => (
                <li key={file.name}>
                  {file.name} ·{" "}
                  {file.size === null ? "Unknown size" : bytes(file.size)}
                  {file.sha256 && <small> · SHA-256 {file.sha256}</small>}
                </li>
              ))}
            </ul>
          </details>
          <pre className="model-card-text">{card.card_text}</pre>
          <button className="text-button" onClick={() => setCard(undefined)}>
            Close model card
          </button>
        </Panel>
      )}
      <Panel>
        <h2>Discover on Hugging Face</h2>
        <label className="field">
          Local catalog filter
          <select
            value={catalogFilter}
            onChange={(e) => setCatalogFilter(e.target.value)}
          >
            <option value="all">All candidates</option>
            <option value="installed">Installed</option>
            <option value="ready">Director Ready</option>
            <option value="adapter">Adapter Required</option>
          </select>
        </label>
        <form
          className="product-inline"
          onSubmit={(e) => {
            e.preventDefault();
            void search();
          }}
        >
          <label className="field">
            Search models
            <input
              maxLength={80}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Wan, MiniMax, video·"
            />
          </label>
          <label className="field">
            Publisher
            <input
              value={author}
              maxLength={96}
              placeholder="Any publisher"
              onChange={(e) => setAuthor(e.target.value)}
            />
          </label>
          <label className="field">
            Task
            <select value={task} onChange={(e) => setTask(e.target.value)}>
              <option value="">All tasks</option>
              {[
                "text-to-video",
                "image-to-video",
                "text-to-image",
                "image-to-image",
                "text-to-audio",
              ].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Sort
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="downloads">Downloads</option>
              <option value="likes">Likes</option>
              <option value="lastModified">Recently updated</option>
              <option value="trendingScore">Trending</option>
            </select>
          </label>
          <button
            className="button secondary"
            disabled={!api.hasKey() || searching}
          >
            {searching ? "Searching metadata·" : "Search"}
          </button>
        </form>
        {error && <p role="alert">{error}</p>}
        {discovery && (
          <>
            <p>{discovery.message}</p>
            {!discovery.items.length && <p>No matching repositories.</p>}
            {discovery.items.map((item) => (
              <article key={item.id} className="discovery-row">
                <a href={item.source} target="_blank" rel="noreferrer">
                  {item.title}
                </a>
                <p>
                  {item.pipeline} · license metadata: {item.license}
                </p>
                <p>
                  {item.gated
                    ? "Gated / authorization required"
                    : item.license_state === "unknown" ||
                        item.license === "unknown"
                      ? "License unknown / review required"
                      : item.license_state ===
                          "restricted_or_other_terms_review_required"
                        ? "Restricted or other terms / review required"
                        : "Published license declaration; review accompanying terms"}{" "}
                  · {item.downloads ?? "?"} downloads · {item.likes ?? "?"}{" "}
                  likes
                </p>
                <Badge>
                  {models.some(
                    (model) => model.repository === item.id && model.runnable,
                  )
                    ? "Director adapter available · use the installed model above"
                    : "Discovered · not a runnable Director adapter"}
                </Badge>
                <button
                  className="text-button"
                  onClick={() =>
                    void navigator.clipboard
                      .writeText(item.id)
                      .catch((e) => setError(message(e)))
                  }
                >
                  Copy repository ID
                </button>
                <button
                  className="text-button"
                  onClick={() =>
                    void api
                      .modelCard(item.id)
                      .then((value) => {
                        setCard(value);
                        setFiles([]);
                        setDownload(undefined);
                      })
                      .catch((e) => setError(message(e)))
                  }
                >
                  Read published model card
                </button>
              </article>
            ))}
            {discovery.next_cursor && (
              <button
                className="button secondary"
                disabled={searching}
                onClick={() => void search(discovery.next_cursor!)}
              >
                Load more models
              </button>
            )}
          </>
        )}
      </Panel>
    </>
  );
}
