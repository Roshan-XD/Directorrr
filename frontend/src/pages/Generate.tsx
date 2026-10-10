import { useState } from "react";
import type { DirectorApi } from "../api/client";
import { DevelopmentGenerate } from "../components/DevelopmentGenerate";
import type { ModelsResponse } from "../api/types";
import { Badge, Icon, Notice, PageHeading, Panel } from "../components/ui";

export function Generate({
  models,
  loading,
  error,
  api,
  allowDevelopment = false,
}: {
  models?: ModelsResponse;
  loading: boolean;
  error?: string;
  api?: DirectorApi;
  allowDevelopment?: boolean;
}) {
  const [mode, setMode] = useState("text-to-video");
  if (allowDevelopment && api) return <DevelopmentGenerate api={api} />;
  return (
    <>
      <PageHeading
        eyebrow="CREATIVE WORKSPACE"
        title="Generate video"
        action={<Badge tone="amber">Preview · inference unavailable</Badge>}
      >
        Start with an idea. Your creative workspace is taking shape.
      </PageHeading>
      <div className="generate-grid">
        <Panel className="prompt-panel">
          <div className="panel-heading">
            <h2>Scene setup</h2>
            <span className="step-number">01</span>
          </div>
          <fieldset className="mode-picker">
            <legend className="sr-only">Generation mode</legend>
            {["text-to-video", "image-to-video"].map((value) => (
              <label key={value} className={mode === value ? "selected" : ""}>
                <input
                  type="radio"
                  name="mode"
                  checked={mode === value}
                  onChange={() => setMode(value)}
                />
                {value === "text-to-video" ? "Text to video" : "Image to video"}
              </label>
            ))}
          </fieldset>
          {mode === "image-to-video" && (
            <div className="image-placeholder">
              <Icon name="folder" />
              <p>Reference image</p>
              <small>Image upload will be available with inference.</small>
              <button className="button secondary" disabled>
                Choose image
              </button>
            </div>
          )}
          <label className="field">
            Your prompt
            <textarea
              rows={6}
              placeholder="A quiet mountain lake at dawn, soft mist drifting over the water. Slow cinematic camera movement…"
              aria-describedby="prompt-hint"
            />
          </label>
          <p className="field-hint" id="prompt-hint">
            Describe the subject, movement, lighting, and camera.
          </p>
          <label className="field">
            Model
            <select
              defaultValue=""
              disabled={loading || !models?.models.length}
            >
              <option value="">
                {loading ? "Loading models…" : "Select a model to explore"}
              </option>
              {models?.models
                .filter((item) => !item.manifest.is_fixture)
                .map(({ manifest }) => (
                  <option key={manifest.id} value={manifest.id}>
                    {manifest.name}
                  </option>
                ))}
            </select>
          </label>
          {error && (
            <p className="inline-error" role="alert">
              Models unavailable: {error}
            </p>
          )}
          {!loading && !error && models?.models.length === 0 && (
            <p className="field-hint">
              No models are registered. Review the Models page.
            </p>
          )}
          <div className="field-row">
            <label className="field">
              Resolution
              <select disabled>
                <option>Not configured</option>
              </select>
            </label>
            <label className="field">
              Duration
              <select disabled>
                <option>Not configured</option>
              </select>
            </label>
          </div>
          <label className="field">
            Seed <span className="optional">Optional draft</span>
            <input
              type="number"
              min="0"
              step="1"
              placeholder="Random when supported"
            />
          </label>
          <Notice>
            Inference is not implemented yet. These inputs are a local draft; no
            generation requests are sent.
          </Notice>
          <button
            className="button primary generate-button"
            disabled
            aria-describedby="generation-disabled"
          >
            <Icon name="lock" />
            Generate video<span>Unavailable</span>
          </button>
          <p className="field-hint center" id="generation-disabled">
            Model installation does not enable generation.
          </p>
        </Panel>
        <div className="preview-column">
          <Panel className="preview-panel">
            <div className="panel-heading">
              <h2>Preview</h2>
              <Badge>Local output</Badge>
            </div>
            <div className="preview-stage">
              <div className="frame-corner corner-a" />
              <div className="frame-corner corner-b" />
              <div className="preview-mark">
                <Icon name="play" size={30} />
              </div>
              <h3>A space for your next scene</h3>
              <p>
                Generated video will appear here once
                <br />
                the local inference runtime is connected.
              </p>
              <Badge>NO OUTPUT YET</Badge>
            </div>
            <div className="transport">
              <span className="timecode">--:--:--:--</span>
              <button aria-label="Play preview" disabled>
                <Icon name="play" size={16} />
              </button>
              <span className="preview-format">
                Resolution · duration unavailable
              </span>
            </div>
          </Panel>
          <Panel className="workflow-note">
            <div className="workflow-icon">
              <Icon name="generate" size={24} />
            </div>
            <div>
              <h3>Your ideas. Your machine.</h3>
              <p>
                Director is being built for local video creation. Explore model
                requirements and check your hardware while generation is under
                development.
              </p>
            </div>
          </Panel>
          <div className="foundation-status">
            <span className="status-dot" />
            Frontend foundation<span>Milestone 3A</span>
          </div>
        </div>
      </div>
    </>
  );
}
