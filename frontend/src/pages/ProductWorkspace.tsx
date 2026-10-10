import type { InstallationJob } from "../api/types";
import { useCallback, useEffect, useState, useRef } from "react";
import type { Studio, Project } from "../api/studio";
import { AssetLibrary } from "../components/product/AssetLibrary";
import { DownloadCenter } from "../components/product/DownloadCenter";
import { ProjectTools } from "../components/product/ProjectTools";
import type { DirectorApi } from "../api/client";
import type {
  Capability,
  CreativeRequest,
  ProductJob,
  ConsoleReport,
} from "../api/product";
import { ManagerAuthorization } from "../components/ManagerAuthorization";
import { ProductResult as Result } from "../components/product/ProductResult";
import { System } from "./System";
import { Models } from "./Models";
import { useResource } from "../hooks/useResource";
import { Badge, Panel, bytes } from "../components/ui";
import { CreativeForm } from "../components/product/CreativeForm";
import { message } from "../components/product/message";
import { ProductModelStore as Store } from "../components/product/ProductModelStore";
import { ProductStorage as Storage } from "../components/product/ProductStorage";
import {
  ShotPlanner,
  type PlannedShot,
} from "../components/product/ShotPlanner";
export { CreativeForm } from "../components/product/CreativeForm";

const tabs = [
  "Generate",
  "Model Store",
  "Library",
  "Downloads",
  "Job Center",
  "Storage",
  "System",
] as const;
type Tab = (typeof tabs)[number];
const initial = (): Tab =>
  tabs.find(
    (t) => window.location.hash === `#${t.toLowerCase().replaceAll(" ", "-")}`,
  ) ?? "Generate";
export function ProductWorkspace({ api }: { api: DirectorApi }) {
  const [tab, setTab] = useState<Tab>(initial);
  const [authorized, setAuthorized] = useState(api.hasKey());
  const authorize = useCallback((ready: boolean) => setAuthorized(ready), []);
  const [models, setModels] = useState<Capability[]>([]);
  const [jobs, setJobs] = useState<ProductJob[]>([]);
  const [installs, setInstalls] = useState<InstallationJob[]>([]);
  const [selected, setSelected] = useState("");
  const [modelId, setModelId] = useState("wan21-t2v-13b");
  const [draft, setDraft] = useState<CreativeRequest>();
  const [shots, setShots] = useState<PlannedShot[]>([]);
  const [draftVersion, setDraftVersion] = useState(0);
  const [studio, setStudio] = useState<Studio>();
  const [studioError, setStudioError] = useState("");
  const [pipeline, setPipeline] = useState(false);
  const [studioMode, setStudioMode] = useState("video");
  const [category, setCategory] = useState("all");
  const [autoScroll, setAutoScroll] = useState(true);
  const consoleView = useRef<HTMLPreElement>(null);
  const studioLoaded = useRef(false);
  const refreshStudio = useCallback(async () => {
    try {
      const value = await api.studio();
      setStudio(value);
      if (!studioLoaded.current) {
        studioLoaded.current = true;
        const project = value.projects.find((p) => p.id === value.current);
        if (project) {
          setShots(project.shots);
          if (project.draft.model_id) {
            setDraft(project.draft as CreativeRequest);
            setModelId(project.draft.model_id);
            setDraftVersion((v) => v + 1);
          }
        }
      }
      setStudioError("");
    } catch (e) {
      setStudioError(message(e));
    }
  }, [api]);
  useEffect(() => {
    if (authorized) void refreshStudio();
  }, [authorized, refreshStudio]);
  const currentProject = studio?.projects.find((p) => p.id === studio.current);
  useEffect(() => {
    if (!currentProject || !draft) return;
    const timer = setTimeout(() => {
      const value = { ...currentProject, draft, shots };
      void api
        .saveProject(value)
        .then(setStudio)
        .catch((e) => setStudioError(message(e)));
    }, 900);
    return () => clearTimeout(timer);
    // A project switch is explicit; metadata refresh must not continuously retrigger autosave.
  }, [api, draft, shots, studio?.current]);
  async function selectProject(project: Project) {
    try {
      const value = await api.saveProject(project);
      setStudio(value);
      setDraft(
        project.draft.model_id ? (project.draft as CreativeRequest) : undefined,
      );
      setShots(project.shots);
      if (project.draft.model_id) setModelId(project.draft.model_id);
      setDraftVersion((v) => v + 1);
    } catch (e) {
      setStudioError(message(e));
    }
  }
  const rememberDraft = useCallback(
    (value: CreativeRequest) => setDraft(value),
    [],
  );
  const [error, setError] = useState("");
  const [connectionError, setConnectionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [consoleOpen, setConsoleOpen] = useState(false);
  const [events, setEvents] = useState<ConsoleReport>({ events: [] });
  const [filter, setFilter] = useState("");
  const [level, setLevel] = useState("all");
  const load = useCallback((signal: AbortSignal) => api.models(signal), [api]);
  const registered = useResource(load);
  const refresh = useCallback(async () => {
    const [catalog, history, logs, installations] = await Promise.all([
      api.productCatalog(),
      api.productJobs(),
      api.consoleEvents(),
      api.installationJobs(),
    ]);
    setModels(catalog.models);
    setJobs(history.jobs);
    setInstalls(installations.jobs);
    setEvents(logs);
    if (history.jobs.some((j) => j.state === "completed")) void refreshStudio();
    setLoading(false);
  }, [api, refreshStudio]);
  useEffect(() => {
    const change = () => setTab(initial());
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    if (!authorized) return;
    let alive = true;
    let polling = false;
    const poll = async () => {
      if (polling) return;
      polling = true;
      try {
        await refresh();
        if (alive) setConnectionError("");
      } catch (e) {
        if (alive) {
          setConnectionError(message(e));
          setLoading(false);
        }
      } finally {
        polling = false;
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 2500);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [authorized, refresh]);
  const model = models.find((m) => m.id === modelId);
  const active = jobs.find(
    (j) => j.state === "queued" || j.state === "running",
  );
  const job = jobs.find((j) => j.id === selected) ?? jobs[0];
  async function act(action: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await action();
      await refresh();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  const visibleEvents = events.events.filter(
    (e) =>
      (level === "all" || e.level === level) &&
      (category === "all" || e.stage === category) &&
      `${e.stage} ${e.message}`.toLowerCase().includes(filter.toLowerCase()),
  );
  useEffect(() => {
    if (autoScroll && consoleView.current)
      consoleView.current.scrollTop = consoleView.current.scrollHeight;
  }, [events, autoScroll, consoleOpen]);
  return (
    <div className="app-shell product-shell">
      <a className="skip-link" href="#product-main">
        Skip to content
      </a>
      <aside className="sidebar">
        <a href="#generate" className="brand">
          Director<span className="brand-period">.</span>
        </a>
        <div className="workspace-label">YOUR LOCAL VIDEO STUDIO</div>
        <nav aria-label="Main navigation">
          {tabs.map((t) => (
            <a
              key={t}
              href={`#${t.toLowerCase().replaceAll(" ", "-")}`}
              aria-current={tab === t ? "page" : undefined}
            >
              {t}
              {t === "Job Center" && jobs.length > 0 && (
                <span className="nav-count">{jobs.length}</span>
              )}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <Badge>Windows creative studio</Badge>
          <p>
            Private local runtime. Production redistribution is not cleared.
          </p>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            Workspace / <strong>{tab}</strong>
          </span>
          <button
            className="text-button"
            onClick={() => setConsoleOpen(!consoleOpen)}
            aria-expanded={consoleOpen}
          >
            Activity console
          </button>
        </header>
        <main id="product-main" tabIndex={-1}>
          <div className={`product-auth ${authorized ? "connected" : ""}`}>
            <ManagerAuthorization api={api} onChange={authorize} />
          </div>
          {error && (
            <p role="alert" className="inline-error">
              {error}
            </p>
          )}
          {connectionError && (
            <p role="alert" className="inline-error">
              {connectionError}
            </p>
          )}
          {studioError && (
            <p role="alert" className="inline-error">
              Project/Library: {studioError}
            </p>
          )}
          {!authorized && (
            <p>Start Director to connect your local session automatically.</p>
          )}
          {loading && authorized && (
            <p role="status">Loading your workspace·</p>
          )}
          {tab === "Generate" && (
            <>
              <div className="page-heading">
                <div>
                  <span className="eyebrow">CREATE ON YOUR COMPUTER</span>
                  <h1>Turn an idea into a scene.</h1>
                  <p>
                    Choose a model, describe a shot, then send the result to
                    Resolve.
                  </p>
                </div>
                <Badge tone="green">Local generation</Badge>
              </div>
              <div className="studio-modes" aria-label="Creative workspace">
                <button
                  className={`studio-mode ${studioMode === "video" ? "selected" : ""}`}
                  aria-pressed={studioMode === "video"}
                  onClick={() => setStudioMode("video")}
                >
                  <span className="mode-symbol" aria-hidden="true">
                    ▷
                  </span>
                  <strong>Create a video</strong>
                  <span>A prompt becomes a moving scene</span>
                </button>
                <button
                  className={`studio-mode image-mode ${studioMode === "image" ? "selected" : ""}`}
                  aria-pressed={studioMode === "image"}
                  onClick={() => setStudioMode("image")}
                >
                  <span className="mode-symbol" aria-hidden="true">
                    ◇
                  </span>
                  <strong>Image studio</strong>
                  <span>References and future image adapters</span>
                </button>
              </div>
              {studioMode === "image" && (
                <Panel>
                  <h2>Start with an image</h2>
                  <p>
                    Store image references in your Library, then check
                    compatible handoffs. No image generation adapter is
                    installed; no generation request is sent from this
                    workspace.
                  </p>
                  <div className="product-inline">
                    <a className="button secondary" href="#library">
                      Open image Library
                    </a>
                    <a className="button secondary" href="#model-store">
                      Discover image models
                    </a>
                    <button className="button primary" disabled>
                      Generate image · adapter required
                    </button>
                  </div>
                  <p className="field-hint">
                    Text-to-image, image-to-image, reference and inpainting
                    modes are represented in capability schemas. They require a
                    reviewed adapter and separately approved weights.
                  </p>
                </Panel>
              )}
              <div hidden={studioMode !== "video"}>
                <div
                  className="library-drop"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const id = e.dataTransfer.getData(
                      "application/x-director-asset",
                    );
                    if (
                      currentProject &&
                      studio?.media.some((a) => a.id === id) &&
                      !currentProject.references.includes(id)
                    )
                      void api
                        .saveProject({
                          ...currentProject,
                          references: [...currentProject.references, id],
                        })
                        .then(setStudio)
                        .catch((e) => setStudioError(message(e)));
                  }}
                >
                  <strong>Project references</strong>
                  <p>
                    Drag an owned Library asset here to keep it with this
                    project. Wan T2V does not consume reference media.
                  </p>
                  {currentProject?.references.map((id) => (
                    <Badge key={id}>
                      {studio?.media.find((a) => a.id === id)?.title ??
                        "Missing reference"}
                    </Badge>
                  ))}
                </div>
                <div className="product-layout">
                  <Panel>
                    <label className="field">
                      Model
                      <select
                        value={modelId}
                        onChange={(e) => {
                          setModelId(e.target.value);
                          const next = models.find(
                            (m) => m.id === e.target.value,
                          );
                          setDraft(
                            draft && next
                              ? {
                                  ...draft,
                                  model_id: next.id,
                                  workspace: next.workspaces.includes(
                                    draft.workspace,
                                  )
                                    ? draft.workspace
                                    : next.workspaces[0],
                                  resolution: next.resolutions.some(
                                    (r) => r.id === draft.resolution,
                                  )
                                    ? draft.resolution
                                    : next.default_resolution,
                                  duration: next.durations.some(
                                    (d) => d.seconds === draft.duration,
                                  )
                                    ? draft.duration
                                    : next.default_duration,
                                  quality: next.qualities[draft.quality]
                                    ? draft.quality
                                    : Object.keys(next.qualities)[0],
                                  export_fps: next.fps,
                                }
                              : undefined,
                          );
                        }}
                      >
                        {models.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name}
                            {!m.runnable ? " · unavailable" : ""}
                          </option>
                        ))}
                      </select>
                    </label>
                    {model && (
                      <CreativeForm
                        key={model.id + "-" + draftVersion}
                        model={model}
                        initial={
                          draft?.model_id === model.id ? draft : undefined
                        }
                        onDraft={rememberDraft}
                        disabled={
                          !authorized || busy || !!active || !model.runnable
                        }
                        onGenerate={async (body) => {
                          await act(async () => {
                            const created = await api.creativeGenerate(body);
                            setSelected(created.id);
                          });
                        }}
                      />
                    )}
                    {!models.length && !loading && (
                      <p>
                        No usable model catalog. Check the backend connection.
                      </p>
                    )}
                  </Panel>
                  <Panel className="product-preview">
                    <h2>Your result</h2>
                    {job ? (
                      <Result api={api} job={job} authorized={authorized} />
                    ) : (
                      <div className="preview-placeholder">
                        <span className="preview-orbit" />
                        <h3>Your next scene starts here</h3>
                        <p>
                          A completed video will appear here. No downloads start
                          when you visit.
                        </p>
                      </div>
                    )}
                  </Panel>
                </div>
                <ProjectTools
                  studio={studio}
                  draft={draft}
                  save={selectProject}
                  restore={(value) => {
                    setModelId(value.model_id);
                    setDraft(value);
                    setDraftVersion((v) => v + 1);
                  }}
                />
                <button
                  className="text-button"
                  aria-expanded={pipeline}
                  onClick={() => setPipeline(!pipeline)}
                >
                  Inspect pipeline
                </button>
                {pipeline && (
                  <Panel>
                    <h2>Validated native Wan pipeline</h2>
                    <div className="pipeline-flow">
                      Prompt → UMT5 text encoder → Wan diffusion / sampler → Wan
                      VAE → 16 fps video → controlled H.264 conversion → Resolve
                    </div>
                    <p>
                      Read-only inspection. Graph editing, arbitrary nodes and
                      remote code are not enabled.
                    </p>
                    <pre>
                      {JSON.stringify(
                        {
                          model: model?.id,
                          adapter: model?.adapter,
                          settings: draft,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </Panel>
                )}
                {model && (
                  <ShotPlanner
                    model={model}
                    draft={draft}
                    jobs={jobs}
                    shots={shots}
                    onChange={setShots}
                  />
                )}
              </div>
            </>
          )}
          {tab === "Job Center" && (
            <>
              <h1>Job Center</h1>
              <p>
                Your recent work stays visible as you move between pages. Live
                control applies to this session. A durable history and managed
                output copies remain in the Library after restart.
              </p>
              {!jobs.length && (
                <Panel>No jobs yet. Generate a scene to begin.</Panel>
              )}
              <div className="product-layout">
                <div>
                  {jobs.map((j, index) => (
                    <Panel key={j.id}>
                      <button
                        className="text-button"
                        onClick={() => setSelected(j.id)}
                      >
                        Scene {jobs.length - index} ·{" "}
                        {j.creative?.prompt?.slice(0, 90) || "Wan generation"}
                      </button>
                      <p role="status">
                        {j.state} · {j.message}
                      </p>
                      {j.tracking_warning && <p>{j.tracking_warning}</p>}
                      {j.progress !== null ? (
                        <progress value={j.progress} max={1} />
                      ) : (
                        <p className="field-hint">
                          {["queued", "running"].includes(j.state)
                            ? "Waiting for actual execution status; no percentage estimate."
                            : ""}
                        </p>
                      )}
                      {["queued", "running"].includes(j.state) ? (
                        <button
                          className="button secondary"
                          disabled={busy}
                          onClick={() =>
                            void act(() => api.cancelGeneration(j.id))
                          }
                        >
                          Cancel generation
                        </button>
                      ) : (
                        <button
                          className="text-button"
                          disabled={busy}
                          onClick={() =>
                            void act(() => api.forgetGeneration(j.id))
                          }
                        >
                          Remove from history · keep video
                        </button>
                      )}
                      {j.state === "failed" && j.creative && (
                        <button
                          className="button secondary"
                          disabled={busy || !!active}
                          onClick={() =>
                            void act(async () => {
                              const c = j.creative!;
                              const created = await api.creativeGenerate({
                                model_id: c.model_id,
                                workspace: c.workspace,
                                prompt: c.prompt,
                                resolution: c.resolution,
                                duration: c.duration,
                                quality: c.quality,
                                seed: c.seed,
                                camera: c.camera,
                                steps: c.steps,
                                cfg: c.cfg,
                                shift: c.shift,
                                negative_prompt: c.negative_prompt,
                                export_fps: c.export_fps,
                              });
                              setSelected(created.id);
                            })
                          }
                        >
                          Retry reviewed settings
                        </button>
                      )}
                      {j.creative && (
                        <button
                          className="text-button"
                          onClick={() => {
                            setModelId(j.creative!.model_id);
                            setDraft(j.creative);
                            setDraftVersion((v) => v + 1);
                            window.location.hash = "#generate";
                          }}
                        >
                          Use these settings and seed
                        </button>
                      )}
                      <details>
                        <summary>Technical details</summary>
                        <p>Job {j.id}</p>
                        <p>Seed {j.creative?.seed ?? "Legacy workflow"}</p>
                      </details>
                    </Panel>
                  ))}
                </div>
                <Panel>
                  {job && (
                    <Result
                      key={job.id}
                      api={api}
                      job={job}
                      authorized={authorized}
                    />
                  )}
                </Panel>
              </div>
              <details>
                <summary>Model installation jobs · developer tools</summary>
                {installs.length === 0 ? (
                  <p>No model installation jobs.</p>
                ) : (
                  installs.map((i) => (
                    <Panel key={i.id}>
                      <h3>{i.model_id}</h3>
                      <p role="status">
                        {i.state} {i.error?.message}
                      </p>
                      <p>
                        Transferred candidate bytes: {bytes(i.candidate_bytes)}{" "}
                        · verified bytes: {bytes(i.verified_bytes)} /{" "}
                        {bytes(i.total_expected_bytes)}
                      </p>
                      {i.total_expected_bytes > 0 && (
                        <progress
                          max={i.total_expected_bytes}
                          value={i.verified_bytes}
                          aria-label="Verified installation bytes"
                        />
                      )}
                      {![
                        "ready",
                        "failed",
                        "cancelled",
                        "corrupted",
                        "not_installed",
                      ].includes(i.state) && (
                        <button
                          className="button secondary"
                          disabled={busy}
                          onClick={() => void act(() => api.cancel(i.id))}
                        >
                          Cancel installation
                        </button>
                      )}
                    </Panel>
                  ))
                )}
                <p>
                  Existing fixture installation jobs remain available through
                  the model manager. Real downloads are disabled.
                </p>
              </details>
              <details>
                <summary>
                  Archived generation history ({studio?.history.length ?? 0})
                </summary>
                {studio?.history.map((j) => (
                  <Panel key={j.id}>
                    <p>
                      {j.state} · {j.creative?.prompt ?? j.message}
                    </p>
                    <small>
                      {j.created} · {j.id}
                    </small>
                    <p>
                      Use Library for saved output previews. Archived jobs
                      cannot mutate Resolve or restart automatically.
                    </p>
                    {j.creative && (
                      <div className="product-inline">
                        <button
                          className="text-button"
                          onClick={() => {
                            setModelId(j.creative!.model_id);
                            setDraft(j.creative);
                            setDraftVersion((v) => v + 1);
                            window.location.hash = "#generate";
                          }}
                        >
                          Reuse archived settings
                        </button>
                        <button
                          className="text-button"
                          onClick={() => {
                            setModelId(j.creative!.model_id);
                            setDraft({ ...j.creative!, seed: null });
                            setDraftVersion((v) => v + 1);
                            window.location.hash = "#generate";
                          }}
                        >
                          Prepare a variation
                        </button>
                      </div>
                    )}
                  </Panel>
                ))}
              </details>
            </>
          )}
          {tab === "Model Store" && (
            <Store
              api={api}
              models={models}
              disabled={!authorized || busy || !!active}
              useModel={(id) => {
                setModelId(id);
                window.location.hash = "#generate";
              }}
              changed={refresh}
              act={act}
            />
          )}
          {tab === "Storage" && <Storage api={api} authorized={authorized} />}
          {tab === "Library" && (
            <AssetLibrary api={api} studio={studio} refresh={refreshStudio} />
          )}
          {tab === "Downloads" && <DownloadCenter api={api} />}
          {tab === "System" && (
            <>
              <System api={api} />
              <details>
                <summary>Developer Mode · terminal design</summary>
                <p>
                  Terminal execution is not enabled. A future local PTY must use
                  normal user permissions, a reviewed working directory and a
                  scrubbed environment without session credentials. See the V1.1
                  architecture document.
                </p>
              </details>
            </>
          )}
          {tab === "Model Store" && (
            <details>
              <summary>
                Existing model manager and fixture installation review
              </summary>
              <Models
                api={api}
                result={registered}
                remember={() => {}}
                allowFixtures={
                  import.meta.env.DEV &&
                  import.meta.env.VITE_ENABLE_FIXTURES === "1"
                }
              />
            </details>
          )}
        </main>
        <footer className="app-footer">
          <a href="#job-center" role="status">
            {active
              ? `${active.state} · ${active.message}`
              : jobs.length
                ? `${jobs.length} recent scenes · Job Center`
                : "Ready when you are · no active jobs"}
          </a>
          <span>Windows only · no cloud generation</span>
        </footer>
        {consoleOpen && (
          <section className="product-console" aria-label="Activity console">
            <div className="product-inline">
              <h2>Activity console</h2>
              <input
                aria-label="Search activity"
                placeholder="Search activity·"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
              <select
                aria-label="Activity level"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
              >
                <option value="all">All levels</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Errors</option>
              </select>
              <select
                aria-label="Activity category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="all">All categories</option>
                {Array.from(new Set(events.events.map((e) => e.stage))).map(
                  (stage) => (
                    <option key={stage}>{stage}</option>
                  ),
                )}
              </select>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                />
                Auto-scroll
              </label>
              <button
                className="text-button"
                onClick={() =>
                  void navigator.clipboard
                    .writeText(
                      visibleEvents
                        .map((e) => `${e.time} ${e.stage}: ${e.message}`)
                        .join("\n"),
                    )
                    .catch(() => setError("Clipboard access is unavailable"))
                }
              >
                Copy filtered
              </button>
              <button
                className="text-button"
                onClick={() => void act(() => api.clearConsole())}
              >
                Clear activity
              </button>
              <button
                className="text-button"
                onClick={() => setConsoleOpen(false)}
              >
                Close
              </button>
            </div>
            <pre ref={consoleView}>
              {visibleEvents
                .map(
                  (e) =>
                    `${e.time} [${e.level}] ${e.stage}: ${e.message}${e.count ? ` (×${e.count})` : ""}`,
                )
                .join("\n") ||
                "No matching events. This panel does not run commands."}
            </pre>
          </section>
        )}
      </div>
    </div>
  );
}
