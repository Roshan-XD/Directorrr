import { useEffect, useState } from "react";
import type { DirectorApi } from "../../api/client";
import type { Asset, Studio } from "../../api/studio";
import { Panel, Badge, bytes } from "../ui";
import { message } from "./message";
function Preview({
  api,
  asset,
  thumbnail = false,
}: {
  api: DirectorApi;
  asset: Asset;
  thumbnail?: boolean;
}) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    let object = "";
    void api
      .libraryFile(asset.id, thumbnail && asset.thumbnail)
      .then((blob) => {
        object = URL.createObjectURL(blob);
        if (alive) setUrl(object);
        else URL.revokeObjectURL(object);
      })
      .catch((e) => {
        if (alive) setError(message(e));
      });
    return () => {
      alive = false;
      if (object) URL.revokeObjectURL(object);
    };
  }, [api, asset.id, asset.thumbnail, thumbnail]);
  if (error) return <p role="alert">{error}</p>;
  if (!url)
    return (
      <div className="asset-placeholder" role="status">
        Loading preview…
      </div>
    );
  if (thumbnail || asset.type === "image")
    return <img loading="lazy" src={url} alt={asset.title} />;
  if (asset.type === "audio") return <audio controls src={url} />;
  return <video controls preload="metadata" src={url} />;
}
export function AssetLibrary({
  api,
  studio,
  refresh,
}: {
  api: DirectorApi;
  studio?: Studio;
  refresh: () => Promise<void>;
}) {
  const [type, setType] = useState("all");
  const [origin, setOrigin] = useState("all");
  const [query, setQuery] = useState("");
  const [favorites, setFavorites] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [detail, setDetail] = useState<Asset>();
  const [confirm, setConfirm] = useState(false);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [handoff, setHandoff] = useState("");
  const [limit, setLimit] = useState(24);
  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function upload(files: FileList | null) {
    if (!files) return;
    await act(async () => {
      for (const file of Array.from(files).slice(0, 12))
        await api.uploadAsset(file);
    });
  }
  const assets =
    studio?.media.filter(
      (a) =>
        (type === "all" || a.type === type) &&
        (origin === "all" ||
          (origin === "references" &&
            studio.projects.some((p) => p.references.includes(a.id))) ||
          a.origin === origin) &&
        (!favorites || a.favorite) &&
        `${a.title} ${a.model_id ?? ""}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    ) ?? [];
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">YOUR CREATIVE MATERIAL</span>
          <h1>Library</h1>
          <p>Inputs and generated outputs, saved on this computer.</p>
        </div>
        <label className="button secondary">
          Add media
          <input
            className="file-input"
            aria-label="Upload Library media"
            type="file"
            multiple
            accept=".png,.jpg,.jpeg,.webm,.mp4,.wav"
            disabled={busy}
            onChange={(e) => void upload(e.target.files)}
          />
        </label>
      </div>
      <div
        className="library-drop"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          void upload(e.dataTransfer.files);
        }}
      >
        Drop images, video or WAV audio here. Up to 64 MiB per file. Files are
        decoded and copied into owned storage.
      </div>
      <div className="product-inline">
        <input
          aria-label="Search Library"
          placeholder="Search your assets"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          aria-label="Library type"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          <option value="all">All assets</option>
          <option value="image">Images</option>
          <option value="video">Videos</option>
          <option value="audio">Audio</option>
        </select>
        <select
          aria-label="Library origin"
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
        >
          <option value="all">Inputs and outputs</option>
          <option value="input">Inputs</option>
          <option value="output">Outputs</option>
          <option value="references">Project references</option>
        </select>
        <label className="check-row">
          <input
            type="checkbox"
            checked={favorites}
            onChange={(e) => setFavorites(e.target.checked)}
          />
          Favorites
        </label>
        <button
          className="text-button"
          disabled={busy}
          onClick={() => void act(() => api.recoverOutputs())}
        >
          Index existing Director videos
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
      {!studio && (
        <p role="status">
          Library unavailable. Check the local backend connection.
        </p>
      )}
      {studio && !assets.length && (
        <Panel>
          <h2>A home for every scene</h2>
          <p>
            Add a reference or generate a video. Original generated files are
            always retained when a Library copy is removed.
          </p>
        </Panel>
      )}
      {selected.length === 2 && (
        <Panel>
          <h2>Compare selected assets</h2>
          <div className="product-layout">
            {selected.map((id) => {
              const a = studio?.media.find((a) => a.id === id);
              return a ? (
                <div key={id}>
                  <Preview api={api} asset={a} />
                  <p>
                    {a.title} · {a.width ?? "?"}×{a.height ?? "?"} ·{" "}
                    {a.duration ?? "?"} s
                  </p>
                </div>
              ) : null;
            })}
          </div>
          <button className="text-button" onClick={() => setSelected([])}>
            Close comparison
          </button>
        </Panel>
      )}
      <div className="asset-grid">
        {assets.slice(0, limit).map((a) => (
          <Panel key={a.id}>
            <button
              className="asset-open"
              aria-label={`Open ${a.title}`}
              draggable
              onDragStart={(e) =>
                e.dataTransfer.setData("application/x-director-asset", a.id)
              }
              onClick={() => {
                setDetail(a);
                setTitle(a.title);
                setConfirm(false);
                setHandoff("");
              }}
            >
              <Preview api={api} asset={a} thumbnail />
              <h3>{a.title}</h3>
            </button>
            <Badge>
              {a.type} · {a.origin}
            </Badge>
            <p>
              {bytes(a.bytes)} ·{" "}
              {a.width && a.height
                ? `${a.width}×${a.height}`
                : "Dimensions not applicable"}
            </p>
            <small>
              {new Date(a.created).toLocaleDateString()} ·{" "}
              {a.model_id ?? "Imported reference"}
            </small>
            <div className="product-inline">
              <button
                className="text-button"
                aria-label={`${a.favorite ? "Unfavorite" : "Favorite"} ${a.title}`}
                disabled={busy}
                onClick={() =>
                  void act(() => api.editAsset(a.id, { favorite: !a.favorite }))
                }
              >
                {a.favorite ? "★" : "☆"} Favorite
              </button>
              <label className="check-row">
                <input
                  type="checkbox"
                  aria-label={`Compare ${a.title}`}
                  checked={selected.includes(a.id)}
                  disabled={!selected.includes(a.id) && selected.length >= 2}
                  onChange={() =>
                    setSelected((s) =>
                      s.includes(a.id)
                        ? s.filter((id) => id !== a.id)
                        : [...s, a.id],
                    )
                  }
                />
                Compare
              </label>
            </div>
          </Panel>
        ))}
      </div>
      {assets.length > limit && (
        <button
          className="button secondary"
          onClick={() => setLimit((v) => v + 24)}
        >
          Show more assets
        </button>
      )}
      {detail && (
        <section
          className="library-detail"
          role="dialog"
          aria-modal="false"
          aria-label="Asset details"
        >
          <Panel>
            <div className="product-inline">
              <h2>{detail.title}</h2>
              <button
                className="text-button"
                onClick={() => setDetail(undefined)}
              >
                Close asset
              </button>
            </div>
            <Preview api={api} asset={detail} />
            <p>
              {detail.codec ?? "Unknown codec"} · {detail.duration ?? "Unknown"}{" "}
              seconds · {detail.model_id ?? "Imported input"}
            </p>
            <label className="field">
              Asset title
              <input
                value={title}
                maxLength={160}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <div className="product-inline">
              <button
                className="button secondary"
                disabled={busy || !title.trim()}
                onClick={() =>
                  void act(async () => {
                    const a = await api.editAsset(detail.id, { title });
                    setDetail(a);
                  })
                }
              >
                Save title
              </button>
              <button
                className="text-button"
                disabled={busy}
                onClick={() => void act(() => api.revealAsset(detail.id))}
              >
                Reveal in Explorer
              </button>
              <button
                className="text-button"
                onClick={() =>
                  void act(async () => {
                    const blob = await api.libraryFile(detail.id);
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = detail.filename;
                    link.click();
                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                  })
                }
              >
                Download copy
              </button>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() =>
                  void act(async () => {
                    const value = await api.assetHandoffs(detail.id);
                    setHandoff(
                      value.actions.length
                        ? value.actions
                            .map((a) => `${a.model_name}: ${a.workspace}`)
                            .join(" · ")
                        : `No compatible installed adapter. ${value.message}`,
                    );
                  })
                }
              >
                {detail.type === "image"
                  ? "Animate / use as reference"
                  : "Check compatible handoffs"}
              </button>
            </div>
            {handoff && (
              <p role="status" className="notice">
                {handoff}
              </p>
            )}
            <details>
              <summary>Technical metadata</summary>
              <pre>{JSON.stringify(detail, null, 2)}</pre>
            </details>
            {studio && (
              <button
                className="text-button"
                disabled={busy}
                onClick={() =>
                  void act(async () => {
                    const project = studio.projects.find(
                      (p) => p.id === studio.current,
                    )!;
                    await api.saveProject({
                      ...project,
                      references: project.references.includes(detail.id)
                        ? project.references.filter((id) => id !== detail.id)
                        : [...project.references, detail.id],
                    });
                  })
                }
              >
                {studio.projects
                  .find((p) => p.id === studio.current)
                  ?.references.includes(detail.id)
                  ? "Remove project reference"
                  : "Keep as project reference"}
              </button>
            )}
            <label className="check-row">
              <input
                type="checkbox"
                checked={confirm}
                onChange={(e) => setConfirm(e.target.checked)}
              />
              Remove only this Library copy. Preserve original generated output.
            </label>
            <button
              className="button secondary"
              disabled={!confirm || busy}
              onClick={() =>
                void act(async () => {
                  await api.deleteAsset(detail.id);
                  setDetail(undefined);
                  setSelected([]);
                })
              }
            >
              Delete Library copy
            </button>
          </Panel>
        </section>
      )}
    </>
  );
}
