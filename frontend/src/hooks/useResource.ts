import { useCallback, useEffect, useState } from "react";

export function useResource<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [version, setVersion] = useState(0);
  const [state, setState] = useState<{
    data?: T;
    error?: string;
    loading: boolean;
  }>({ loading: true });
  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true });
    load(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setState({ loading: false, data });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setState({
            loading: false,
            error: error instanceof Error ? error.message : "Request failed.",
          });
      });
    return () => controller.abort();
  }, [load, version]);
  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { ...state, reload };
}
