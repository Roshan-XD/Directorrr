import { useEffect, useState } from "react";
import type { DirectorApi } from "../api/client";
import { Badge, Panel } from "./ui";

export function ManagerAuthorization({
  api,
  onChange,
}: {
  api: DirectorApi;
  onChange: (available: boolean) => void;
}) {
  const [key, setKey] = useState("");
  const [available, setAvailable] = useState(api.hasKey());
  const [automatic, setAutomatic] = useState(api.isAutomatic());
  useEffect(() => {
    const controller = new AbortController();
    api
      .launcherSession(controller.signal)
      .then((ready) => {
        if (!controller.signal.aborted && ready) {
          setAutomatic(true);
          setAvailable(true);
          onChange(true);
        }
      })
      .catch(() => {
        /* Standalone development retains explicit key entry. */
      });
    return () => controller.abort();
  }, [api, onChange]);
  function update(value: string) {
    api.setKey(value);
    setKey("");
    setAvailable(api.hasKey());
    onChange(api.hasKey());
  }
  if (automatic)
    return (
      <Panel className="key-panel">
        <h2>Local session connected</h2>
        <p className="field-hint">
          Director handles local authorization automatically. No key entry is
          needed.
        </p>
        <Badge tone="green">Authorized for this Director session</Badge>
      </Panel>
    );
  return (
    <Panel className="key-panel">
      <h2>Local manager authorization</h2>
      <p className="field-hint">
        Acknowledgement, installation and cancellation require your backend
        manager key. It stays in memory and is cleared on reload. No Hugging
        Face token is requested.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (key.length >= 32) update(key);
        }}
      >
        <label className="field">
          Manager key
          <input
            type="password"
            value={key}
            autoComplete="off"
            onChange={(event) => setKey(event.target.value)}
            placeholder="At least 32 characters"
          />
        </label>
        <button className="button secondary" disabled={key.length < 32}>
          Use key
        </button>
        {available && (
          <button
            className="text-button"
            type="button"
            onClick={() => update("")}
          >
            Clear key
          </button>
        )}
      </form>
      {available && <Badge tone="green">Key set for this app session</Badge>}
    </Panel>
  );
}
