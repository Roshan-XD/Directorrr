import { ProductWorkspace } from "./pages/ProductWorkspace";
import { useCallback, useEffect, useRef, useState } from "react";
import { DirectorApi } from "./api/client";
import { Badge, Icon } from "./components/ui";
import { useResource } from "./hooks/useResource";
import { jobIdPattern, readHistory, writeHistory } from "./hooks/history";
import { Generate } from "./pages/Generate";
import { Models } from "./pages/Models";
import { Jobs } from "./pages/Jobs";
import { System } from "./pages/System";

const pages = ["Generate", "Models", "Jobs", "System"] as const;
type Page = (typeof pages)[number];
function currentPage(): Page {
  return (
    pages.find((page) => `#${page.toLowerCase()}` === window.location.hash) ??
    "Generate"
  );
}
export function App({
  api,
  allowDevelopment = import.meta.env.DEV &&
    import.meta.env.VITE_DEV_GENERATION === "1",
  allowFixtures = import.meta.env.DEV &&
    import.meta.env.VITE_ENABLE_FIXTURES === "1",
}: {
  api: DirectorApi;
  allowDevelopment?: boolean;
  allowFixtures?: boolean;
}) {
  const [page, setPage] = useState<Page>(currentPage);
  const [ids, setIds] = useState(readHistory);
  const main = useRef<HTMLElement>(null);
  const load = useCallback((signal: AbortSignal) => api.models(signal), [api]);
  const models = useResource(load);
  const remember = useCallback((id: string) => {
    if (!jobIdPattern.test(id)) return;
    setIds((previous) =>
      previous.includes(id) ? previous : [id, ...previous].slice(0, 12),
    );
  }, []);
  const forget = useCallback(
    (id: string) =>
      setIds((previous) => previous.filter((item) => item !== id)),
    [],
  );
  useEffect(() => writeHistory(ids), [ids]);
  useEffect(() => {
    const change = () => {
      setPage(currentPage());
      main.current?.focus();
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  if (import.meta.env.DEV && import.meta.env.VITE_PRODUCT_WORKSPACE === "1")
    return <ProductWorkspace api={api} />;
  return (
    <div className="app-shell">
      <a
        href="#main-content"
        className="skip-link"
        onClick={(event) => {
          event.preventDefault();
          main.current?.focus();
        }}
      >
        Skip to content
      </a>
      <aside className="sidebar">
        <a className="brand" href="#generate" aria-label="Director home">
          <span className="brand-mark">
            <span />
            <span />
            <span />
          </span>
          Director<span className="brand-period">.</span>
        </a>
        <div className="workspace-label">LOCAL CREATIVE WORKSPACE</div>
        <nav aria-label="Main navigation">
          {pages.map((item) => (
            <a
              href={`#${item.toLowerCase()}`}
              key={item}
              aria-current={page === item ? "page" : undefined}
            >
              <Icon name={item.toLowerCase()} />
              <span>{item}</span>
              {item === "Jobs" && ids.length > 0 && (
                <span className="nav-count">{ids.length}</span>
              )}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-note">
            <Icon name="lock" size={16} />
            <span>Designed for local creation</span>
          </div>
          <div className="version-line">
            <span>Installation workspace</span>
            <Badge>3B</Badge>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{page}</strong>
          </div>
          <div className="connection-indicator" role="status">
            <span
              className={`status-dot ${models.error ? "dot-error" : models.loading ? "dot-pending" : ""}`}
            />
            {models.loading
              ? "Connecting to backend"
              : models.error
                ? "Backend unavailable"
                : "Backend connected"}
          </div>
        </header>
        <main id="main-content" tabIndex={-1} ref={main}>
          {page === "Generate" && (
            <Generate
              api={api}
              allowDevelopment={import.meta.env.DEV && allowDevelopment}
              models={models.data}
              loading={models.loading}
              error={models.error}
            />
          )}
          {page === "Models" && (
            <Models
              api={api}
              result={models}
              remember={remember}
              allowFixtures={import.meta.env.DEV && allowFixtures}
            />
          )}
          {page === "Jobs" && (
            <Jobs api={api} ids={ids} remember={remember} forget={forget} />
          )}
          {page === "System" && <System api={api} />}
        </main>
        <footer className="app-footer">
          <span>Director · Local AI video workspace</span>
          <span>
            {import.meta.env.DEV && allowDevelopment
              ? "Local development generation · Resolve checked on explicit result actions."
              : "Generation and Resolve integration are not connected."}
          </span>
        </footer>
      </div>
    </div>
  );
}
