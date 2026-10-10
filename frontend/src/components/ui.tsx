import type { ReactNode } from "react";

export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    generate: (
      <>
        <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z" />
        <path d="m20 3 1 2m-1-2-2 1" />
      </>
    ),
    models: (
      <>
        <path d="m12 3 9 5-9 5-9-5Z" />
        <path d="m3 12 9 5 9-5M3 16l9 5 9-5" />
      </>
    ),
    jobs: (
      <>
        <path d="M4 5h16v14H4zM4 9h16" />
        <path d="m9 12 5 3-5 2Z" />
      </>
    ),
    system: (
      <>
        <rect x="5" y="5" width="14" height="14" rx="3" />
        <path d="M9 9h6v6H9zM9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3" />
      </>
    ),
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    lock: (
      <>
        <rect x="5" y="10" width="14" height="11" rx="3" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3" />
      </>
    ),
    play: <path d="m9 5 11 7-11 7Z" />,
    refresh: (
      <>
        <path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5" />
      </>
    ),
    folder: <path d="M3 7V5h7l2 3h9v12H3Z" />,
    info: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v6m0-10v1" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] ?? paths.info}
    </svg>
  );
}
export function Badge({
  children,
  tone = "muted",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
export function Panel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`panel ${className}`}>{children}</section>;
}
export function Notice({
  children,
  danger = false,
}: {
  children: ReactNode;
  danger?: boolean;
}) {
  return (
    <div
      className={`notice ${danger ? "notice-danger" : ""}`}
      role={danger ? "alert" : undefined}
    >
      <Icon name="info" />
      <div>{children}</div>
    </div>
  );
}
export function Loading({
  text = "Loading from Director…",
}: {
  text?: string;
}) {
  return (
    <div className="empty" role="status">
      <span className="spinner" />
      {text}
    </div>
  );
}
export function ErrorState({
  error,
  retry,
}: {
  error: string;
  retry: () => void;
}) {
  return (
    <Panel>
      <Notice danger>{error}</Notice>
      <button className="button secondary" onClick={retry}>
        <Icon name="refresh" />
        Try again
      </button>
    </Panel>
  );
}
export function PageHeading({
  eyebrow,
  title,
  children,
  action,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{children}</p>
      </div>
      {action}
    </div>
  );
}
export function bytes(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) return "Unknown";
  if (value < 1024) return `${value} B`;
  const power = value < 1024 ** 2 ? 1 : value < 1024 ** 3 ? 2 : 3;
  return `${(value / 1024 ** power).toFixed(2)} ${["B", "KiB", "MiB", "GiB"][power]}`;
}
export function gib(value: number | null | undefined) {
  return value == null || !Number.isFinite(value)
    ? "Unknown"
    : `${value.toFixed(2)} GiB`;
}
const assessments: Record<string, { label: string; tone: string }> = {
  verified_compatible: { label: "Verified compatible", tone: "green" },
  potentially_compatible: { label: "Potentially compatible", tone: "amber" },
  unsupported: { label: "Unsupported", tone: "red" },
  unknown: { label: "Compatibility unknown", tone: "muted" },
};
export function Assessment({ value }: { value: string }) {
  const assessment = assessments[value] ?? assessments.unknown;
  return <Badge tone={assessment.tone}>{assessment.label}</Badge>;
}
export function stateLabel(state: string) {
  return state.replaceAll("_", " ");
}
