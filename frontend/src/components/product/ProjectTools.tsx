import { useState } from "react";
import type { Studio, Project } from "../../api/studio";
import type { CreativeRequest } from "../../api/product";
import { Panel } from "../ui";
export function ProjectTools({
  studio,
  draft,
  save,
  restore,
}: {
  studio?: Studio;
  draft?: CreativeRequest;
  save: (project: Project) => Promise<void>;
  restore: (draft: CreativeRequest) => void;
}) {
  const [name, setName] = useState("");
  const [preset, setPreset] = useState("");
  const [saving, setSaving] = useState(false);
  const current = studio?.projects.find((p) => p.id === studio.current);
  async function commit(project: Project) {
    setSaving(true);
    try {
      await save(project);
    } finally {
      setSaving(false);
    }
  }
  return (
    <Panel>
      <div className="product-inline">
        <h2>Project</h2>
        <select
          aria-label="Current project"
          value={studio?.current ?? ""}
          disabled={!studio || saving}
          onChange={(e) => {
            const project = studio?.projects.find(
              (p) => p.id === e.target.value,
            );
            if (project) void commit(project);
          }}
        >
          {studio?.projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <input
          aria-label="Project name"
          maxLength={80}
          placeholder="New project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="text-button"
          disabled={!studio || !name.trim() || saving}
          onClick={() =>
            void commit({
              id: crypto.randomUUID().replaceAll("-", ""),
              name,
              updated: new Date().toISOString(),
              draft: {},
              shots: [],
              favorites: [],
              presets: [],
              references: [],
            })
          }
        >
          New project
        </button>
        <span className="field-hint">Drafts and shots autosave locally.</span>
      </div>
      {current && (
        <details>
          <summary>Presets and reusable prompts</summary>
          <div className="product-inline">
            <input
              aria-label="Preset name"
              placeholder="Preset name"
              value={preset}
              maxLength={80}
              onChange={(e) => setPreset(e.target.value)}
            />
            <button
              className="button secondary"
              disabled={
                !draft ||
                !preset.trim() ||
                saving ||
                current.presets.length >= 40
              }
              onClick={() =>
                draft &&
                void commit({
                  ...current,
                  draft,
                  presets: [
                    { name: preset, settings: draft },
                    ...current.presets,
                  ],
                })
              }
            >
              Save prompt and settings
            </button>
          </div>
          {current.presets.map((p, index) => (
            <button
              className="text-button"
              key={index}
              onClick={() => restore(p.settings)}
            >
              {p.name}
            </button>
          ))}
        </details>
      )}
    </Panel>
  );
}
