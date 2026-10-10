import { useCallback, useEffect, useState } from "react";
import type { DirectorApi } from "../api/client";
import type {
  InstallationStatus,
  ModelsResponse,
  RegisteredModel,
} from "../api/types";
import { ManagerAuthorization } from "../components/ManagerAuthorization";
import { InstallationWorkflow } from "../components/InstallationWorkflow";
import { useResource } from "../hooks/useResource";
import {
  Assessment,
  Badge,
  bytes,
  ErrorState,
  gib,
  Icon,
  Loading,
  Notice,
  PageHeading,
  Panel,
  stateLabel,
} from "../components/ui";

function ModelDetails({
  api,
  item,
  authorized,
  allowFixture,
  remember,
  onComplete,
}: {
  api: DirectorApi;
  item: RegisteredModel;
  authorized: boolean;
  allowFixture: boolean;
  remember: (id: string) => void;
  onComplete: () => void;
}) {
  const model = item.manifest;
  const load = useCallback(
    (signal: AbortSignal) => api.plan(model.id, signal),
    [api, model.id],
  );
  const plan = useResource(load);
  const completed = useCallback(() => {
    plan.reload();
    onComplete();
  }, [plan.reload, onComplete]);
  const info = model.license_info;
  return (
    <Panel className="model-details">
      <div className="panel-heading">
        <h2>Installation review</h2>
        <Badge>Read only</Badge>
      </div>
      <h3>{model.name}</h3>
      <div className="detail-section">
        <span className="eyebrow">COMPATIBILITY EVIDENCE</span>
        <Assessment value={item.compatibility.assessment} />
        <p className="field-hint">
          Capacity result: {item.compatibility.status}. A capacity match is not
          proof of generation support.
        </p>
        <details>
          <summary>Hardware and runtime compatibility reasons</summary>
          <ul className="reason-list">
            {[
              ...item.compatibility.checks,
              ...item.compatibility.profile_checks,
            ].map((check, index) => (
              <li key={index}>
                <span className={`check-dot check-${check.status}`} />
                <div>
                  <strong>
                    {check.resource.replaceAll("_", " ")} · {check.status}
                  </strong>
                  <p>{check.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        </details>
        <details>
          <summary>Evidence limits and research notes</summary>
          {item.compatibility.notes.map((note, index) => (
            <p className="field-hint" key={index}>
              {note}
            </p>
          ))}
        </details>
      </div>
      <div className="detail-section">
        <span className="eyebrow">LICENSE & USAGE</span>
        <h3>{info?.identifier ?? model.license}</h3>
        {!model.is_fixture &&
          info?.source &&
          /^https?:\/\//.test(info.source) && (
            <a href={info.source} target="_blank" rel="noreferrer">
              View publisher license ↗
            </a>
          )}
        <ul className="reason-list">
          {info?.usage_restrictions.map((text, index) => (
            <li key={`r${index}`}>{text}</li>
          ))}
          {info?.acknowledgement_requirements.map((text, index) => (
            <li key={`a${index}`}>{text}</li>
          ))}
        </ul>
        <p className="field-hint">
          {model.artifact_installation_reviewed
            ? "Inventory marked reviewed. Every installation review still requires your explicit license acknowledgement."
            : "Complete artifact and license review is outstanding. Installation is blocked."}
        </p>
      </div>
      {plan.loading ? (
        <Loading text="Checking installation plan…" />
      ) : plan.error ? (
        <ErrorState error={plan.error} retry={plan.reload} />
      ) : (
        plan.data && (
          <>
            <div className="detail-section">
              <span className="eyebrow">STORAGE PLAN</span>
              <dl className="detail-list">
                <div>
                  <dt>Exact download</dt>
                  <dd>{bytes(plan.data.total_expected_download_bytes)}</dd>
                </div>
                <div>
                  <dt>Estimated download</dt>
                  <dd>{bytes(plan.data.total_estimated_download_bytes)}</dd>
                </div>
                <div>
                  <dt>Required storage incl. overhead</dt>
                  <dd>{bytes(plan.data.required_storage_bytes)}</dd>
                </div>
                <div>
                  <dt>Destination drive free</dt>
                  <dd>{bytes(plan.data.storage.free_bytes)}</dd>
                </div>
              </dl>
              <p className="field-hint break-word">{plan.data.storage.root}</p>
              <p className="field-hint">
                These are logical planning paths. The manager isolates
                installations in Director-owned bundles.
              </p>
              {plan.data.components.length > 0 && (
                <details>
                  <summary>
                    Required files ({plan.data.components.length})
                  </summary>
                  {plan.data.components.map(({ component }) => (
                    <div className="component-row" key={component.id}>
                      <strong>{component.role.replaceAll("_", " ")}</strong>
                      <code>{component.filename}</code>
                      <span>
                        {bytes(component.expected_size_bytes)}
                        {component.expected_size_bytes === null &&
                          component.estimated_size_bytes !== null &&
                          ` · estimated ${bytes(component.estimated_size_bytes)}`}
                      </span>
                    </div>
                  ))}
                </details>
              )}
            </div>
            <div className="detail-section">
              <span className="eyebrow">
                GENERATION PREREQUISITES & WARNINGS
              </span>
              {plan.data.blockers.length > 0 && (
                <ul className="issue-list">
                  {plan.data.blockers.map((issue, index) => (
                    <li key={index}>
                      <Badge tone="red">Blocker</Badge>
                      <p>{issue.message}</p>
                    </li>
                  ))}
                </ul>
              )}
              {plan.data.warnings.map((warning, index) => (
                <Notice key={index}>{warning}</Notice>
              ))}
              {plan.data.missing_metadata.length > 0 && (
                <details>
                  <summary>
                    Missing metadata ({plan.data.missing_metadata.length})
                  </summary>
                  <ul className="reason-list">
                    {plan.data.missing_metadata.map((field) => (
                      <li key={field}>
                        <code>{field}</code>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
              {!plan.data.blockers.length && !plan.data.warnings.length && (
                <p>
                  No plan issues reported. This interface still does not enable
                  installation.
                </p>
              )}
            </div>
          </>
        )
      )}
      <InstallationWorkflow
        api={api}
        item={item}
        plan={plan.data}
        authorized={authorized}
        allowFixture={allowFixture}
        remember={remember}
        onComplete={completed}
      />
    </Panel>
  );
}

export function Models({
  api,
  result,
  remember,
  allowFixtures = false,
}: {
  api: DirectorApi;
  result: {
    data?: ModelsResponse;
    loading: boolean;
    error?: string;
    reload: () => void;
  };
  remember: (id: string) => void;
  allowFixtures?: boolean;
}) {
  const [selection, setSelection] = useState("");
  const [query, setQuery] = useState("");
  const [statuses, setStatuses] = useState<
    Record<string, InstallationStatus | string>
  >({});
  const [authorized, setAuthorized] = useState(api.hasKey());
  const [statusVersion, setStatusVersion] = useState(0);
  const complete = useCallback(
    () => setStatusVersion((value) => value + 1),
    [],
  );
  const models = result.data?.models;
  const permitted = models?.filter(
    (item) =>
      !item.manifest.is_fixture ||
      (allowFixtures && item.manifest.id === "fixture-tiny"),
  );
  useEffect(() => {
    const controller = new AbortController();
    setStatuses({});
    for (const item of models ?? []) {
      api
        .installation(item.manifest.id, controller.signal)
        .then((status) => {
          if (controller.signal.aborted) return;
          setStatuses((previous) => ({
            ...previous,
            [item.manifest.id]: status,
          }));
          if (status.job_id) remember(status.job_id);
        })
        .catch((error) => {
          if (!controller.signal.aborted)
            setStatuses((previous) => ({
              ...previous,
              [item.manifest.id]:
                error instanceof Error ? error.message : "Status unavailable",
            }));
        });
    }
    return () => controller.abort();
  }, [api, models, remember, statusVersion]);
  const visible = permitted?.filter((item) =>
    `${item.manifest.name} ${item.manifest.description}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  const selected =
    permitted?.find((item) => item.manifest.id === selection) ?? visible?.[0];
  return (
    <>
      <PageHeading
        eyebrow="MODEL LIBRARY"
        title="Find your creative engine"
        action={
          <button
            className="button secondary"
            onClick={result.reload}
            disabled={result.loading}
          >
            <Icon name="refresh" />
            Refresh
          </button>
        }
      >
        Explore capabilities, hardware evidence, and the requirements behind
        each model.
      </PageHeading>
      <Notice>
        Model information comes from your backend registry. Research and
        installed files do not establish generation readiness.
      </Notice>
      <ManagerAuthorization api={api} onChange={setAuthorized} />
      {allowFixtures && (
        <Notice>
          Local development fixture mode is enabled. Offline fixtures are test
          utilities, not model recommendations.
        </Notice>
      )}
      {result.loading ? (
        <Loading text="Reading model registry…" />
      ) : result.error ? (
        <ErrorState error={result.error} retry={result.reload} />
      ) : (
        <>
          <div className="library-toolbar">
            <label className="search-field">
              <span className="sr-only">Search models</span>
              <input
                placeholder="Search models…"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setSelection("");
                }}
              />
            </label>
            <span>{visible?.length ?? 0} models</span>
          </div>
          {!permitted?.length ? (
            <Panel>
              <div className="empty">
                <Icon name="models" size={32} />
                <h2>Your registry is empty</h2>
                <p>
                  Add validated manifests to the backend registry, then restart
                  it.
                </p>
              </div>
            </Panel>
          ) : !visible?.length ? (
            <Panel>
              <div className="empty">No models match your search.</div>
            </Panel>
          ) : (
            <div className="models-layout">
              <div className="model-list">
                {visible.map((item) => {
                  const model = item.manifest;
                  const status = statuses[model.id];
                  const exact =
                    model.components.length &&
                    model.components.every(
                      (c) => c.expected_size_bytes !== null,
                    )
                      ? model.components.reduce(
                          (sum, c) => sum + (c.expected_size_bytes ?? 0),
                          0,
                        )
                      : null;
                  return (
                    <button
                      className={`model-card panel ${selected?.manifest.id === model.id ? "model-selected" : ""}`}
                      key={model.id}
                      onClick={() => setSelection(model.id)}
                      aria-pressed={selected?.manifest.id === model.id}
                    >
                      <div className="panel-heading">
                        <div className="model-symbol">
                          <Icon name="models" size={24} />
                        </div>
                        <Badge tone={model.is_mock ? "muted" : "accent"}>
                          {model.is_mock
                            ? model.is_fixture
                              ? "Offline fixture"
                              : "Mock metadata"
                            : "Researched model"}
                        </Badge>
                      </div>
                      <h2>{model.name}</h2>
                      <p>{model.description}</p>
                      <div className="tag-row">
                        {model.tasks.map((task) => (
                          <Badge key={task}>{task.replaceAll("-", " ")}</Badge>
                        ))}
                      </div>
                      <Assessment value={item.compatibility.assessment} />
                      <div className="model-specs">
                        <span>
                          Download <strong>{bytes(exact)}</strong>
                        </span>
                        <span>
                          RAM minimum{" "}
                          <strong>{gib(model.requirements.min_ram_gb)}</strong>
                        </span>
                      </div>
                      <div className="model-footer">
                        <span>
                          Artifact installation:{" "}
                          {typeof status === "string"
                            ? "Unknown · status request failed"
                            : status
                              ? `${stateLabel(status.state)} · Generation unavailable`
                              : "Checking…"}
                        </span>
                        <Icon name="arrow" size={16} />
                      </div>
                      {typeof status === "string" && (
                        <span className="inline-error">{status}</span>
                      )}
                    </button>
                  );
                })}
              </div>
              {selected && (
                <ModelDetails
                  api={api}
                  item={selected}
                  authorized={authorized}
                  allowFixture={allowFixtures}
                  remember={remember}
                  onComplete={complete}
                  key={selected.manifest.id}
                />
              )}
            </div>
          )}
          {result.data?.hardware_warnings.map((warning, index) => (
            <Notice key={index}>{warning}</Notice>
          ))}
        </>
      )}
    </>
  );
}
