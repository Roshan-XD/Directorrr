import { useEffect, useState } from "react";
import type { Capability, CreativeRequest } from "../../api/product";
export function CreativeForm({
  model,
  disabled,
  onGenerate,
  initial,
  onDraft,
}: {
  model: Capability;
  disabled: boolean;
  onGenerate: (body: CreativeRequest) => Promise<void>;
  initial?: CreativeRequest;
  onDraft?: (body: CreativeRequest) => void;
}) {
  // Model-specific settings must not leak from a previously selected family.
  initial = initial?.model_id === model.id ? initial : undefined;
  const [prompt, setPrompt] = useState(initial?.prompt ?? "");
  const [workspace, setWorkspace] = useState(
    initial?.workspace ?? model.workspaces[0],
  );
  const [duration, setDuration] = useState(
    initial?.duration ?? model.default_duration,
  );
  const [resolution, setResolution] = useState(
    initial?.resolution ?? model.default_resolution,
  );
  const [quality, setQuality] = useState(
    initial?.quality ?? Object.keys(model.qualities)[0],
  );
  const [camera, setCamera] = useState(initial?.camera ?? "none");
  const [locked, setLocked] = useState(initial?.seed != null);
  const [seed, setSeed] = useState(String(initial?.seed ?? 20261009));
  const [advanced, setAdvanced] = useState(false);
  const [steps, setSteps] = useState(
    initial?.steps ? String(initial.steps) : "",
  );
  const [cfg, setCfg] = useState(initial?.cfg ?? 6);
  const [shift, setShift] = useState(initial?.shift ?? 8);
  const [negative, setNegative] = useState(
    initial?.negative_prompt ??
      "low quality, blurry, static, distorted, watermark, subtitles",
  );
  useEffect(() => {
    onDraft?.({
      model_id: model.id,
      workspace,
      prompt,
      resolution,
      duration,
      quality,
      seed: locked && Number.isSafeInteger(Number(seed)) ? Number(seed) : null,
      camera,
      steps: steps ? Number(steps) : undefined,
      cfg,
      shift,
      negative_prompt: negative,
      export_fps: model.fps,
    });
  }, [
    onDraft,
    model.id,
    model.fps,
    workspace,
    prompt,
    resolution,
    duration,
    quality,
    locked,
    seed,
    camera,
    steps,
    cfg,
    shift,
    negative,
  ]);
  const d = model.durations.find((d) => d.seconds === duration)!;
  const r = model.resolutions.find((r) => r.id === resolution)!;
  const validSeed =
    !locked ||
    (/^\d+$/.test(seed) &&
      Number.isSafeInteger(Number(seed)) &&
      Number(seed) >= 0);
  const experimental =
    resolution !== "preview" ||
    duration !== 1 ||
    quality !== "Fast" ||
    cfg !== 6 ||
    shift !== 8 ||
    !!steps;
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void onGenerate({
          model_id: model.id,
          workspace,
          prompt,
          resolution,
          duration,
          quality,
          seed: locked ? Number(seed) : null,
          camera,
          steps: steps ? Number(steps) : undefined,
          cfg,
          shift,
          negative_prompt: negative,
          export_fps: model.fps,
        });
      }}
    >
      <label className="field">
        Workspace
        <select
          value={workspace}
          disabled={!model.runnable}
          onChange={(e) => setWorkspace(e.target.value as typeof workspace)}
        >
          {model.workspaces.map((w) => (
            <option key={w} value={w}>
              {w.replaceAll("-", " ")}
            </option>
          ))}
        </select>
      </label>
      {model.blockers.length > 0 && (
        <div role="status" className="notice">
          {model.blockers.map((b) => (
            <p key={b}>{b}</p>
          ))}
          <p>Discovering a model does not make it runnable.</p>
        </div>
      )}
      <label className="field">
        Describe your scene
        <textarea
          rows={5}
          maxLength={1800}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ocean waves at sunset, warm light, gentle motion·"
          required
        />
      </label>
      <div className="product-inline">
        <button
          className="text-button"
          type="button"
          onClick={() =>
            setPrompt(
              "A cinematic shot of ocean waves at sunset, warm golden light, gentle camera movement.",
            )
          }
        >
          Try a scene prompt
        </button>
        <button
          className="text-button"
          type="button"
          onClick={() => void navigator.clipboard.writeText(prompt)}
        >
          Copy prompt
        </button>
      </div>
      <div className="product-controls">
        <label className="field">
          Duration
          <select
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          >
            {model.durations.map((d) => (
              <option key={d.seconds} value={d.seconds}>
                {d.seconds} second{d.seconds !== 1 ? "s" : ""}
                {d.seconds === 1 ? " · preview" : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          Aspect and resolution
          <select
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
          >
            {model.resolutions.map((r) => (
              <option key={r.id} value={r.id}>
                {r.aspect} · {r.width} x {r.height}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          Quality
          <select value={quality} onChange={(e) => setQuality(e.target.value)}>
            {Object.keys(model.qualities).map((q) => (
              <option key={q}>{q}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Camera guidance
          <select value={camera} onChange={(e) => setCamera(e.target.value)}>
            {[
              "none",
              "static",
              "pan-left",
              "pan-right",
              "push-in",
              "pull-out",
              "orbit",
            ].map((c) => (
              <option key={c} value={c}>
                {c.replaceAll("-", " ")}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="field-hint">
        Camera choices add wording to your prompt; they do not guarantee camera
        movement. Native and export frame rate: {model.fps} fps. No
        interpolation.
      </p>
      {experimental && model.runnable && (
        <p className="notice">
          Experimental settings: longer/larger scenes need more memory and time.
          Only the short preview baseline has been tested on this machine.
        </p>
      )}
      <label className="check-row">
        <input
          type="checkbox"
          checked={locked}
          onChange={(e) => setLocked(e.target.checked)}
        />
        Lock seed for repeatable comparisons
      </label>
      {locked && (
        <label className="field">
          Seed
          <input
            inputMode="numeric"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
          />
        </label>
      )}
      {!locked && (
        <p className="field-hint">
          A fresh random seed is selected for each new generation.
        </p>
      )}
      {model.id !== "minimax-h3-optimized" && (
        <button
          type="button"
          className="text-button"
          aria-expanded={advanced}
          onClick={() => setAdvanced(!advanced)}
        >
          Advanced settings
        </button>
      )}
      {model.id === "minimax-h3-optimized" && (
        <p className="notice">
          Native audio is included. Fixed euler/simple T2VA settings use
          video/audio shifts 12/3 and no CFG or negative prompt. First execution
          of this exact quantization remains experimental.
        </p>
      )}
      {advanced && model.id !== "minimax-h3-optimized" && (
        <div className="product-controls">
          <label className="field">
            Steps override
            <input
              type="number"
              min={1}
              max={32}
              value={steps}
              placeholder={String(model.qualities[quality])}
              onChange={(e) => setSteps(e.target.value)}
            />
          </label>
          <label className="field">
            Guidance (CFG)
            <input
              type="number"
              min={1}
              max={10}
              step={0.5}
              value={cfg}
              onChange={(e) => setCfg(Number(e.target.value))}
            />
          </label>
          <label className="field">
            Sampling shift
            <input
              type="number"
              min={1}
              max={12}
              step={0.5}
              value={shift}
              onChange={(e) => setShift(Number(e.target.value))}
            />
          </label>
          <label className="field">
            Negative prompt
            <textarea
              maxLength={2000}
              value={negative}
              onChange={(e) => setNegative(e.target.value)}
            />
          </label>
        </div>
      )}
      <details>
        <summary>Technical details</summary>
        <p>
          {r.width} x {r.height} · {d.frames} frames ·{" "}
          {(d.frames / model.fps).toFixed(3)} seconds exact ·{" "}
          {steps || model.qualities[quality]} steps
        </p>
        <p>
          {model.adapter
            ? model.id === "minimax-h3-optimized"
              ? "euler / simple · batch 1 · "
              : "uni_pc / simple · batch 1 · "
            : "Adapter not implemented · "}
          {model.native_audio
            ? "Native audio published; adapter unvalidated"
            : "Video only; no audio track"}
        </p>
        {model.evidence.map((e) => (
          <p key={e}>{e}</p>
        ))}
      </details>
      <button
        className="button primary product-generate"
        disabled={disabled || !prompt.trim() || !validSeed || !model.runnable}
      >
        Generate scene
      </button>
    </form>
  );
}
