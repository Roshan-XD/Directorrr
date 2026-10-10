import { useEffect, useRef, type ReactNode } from "react";

/** Native modal semantics provide a focus trap, background isolation and Escape. */
export function ReviewDialog({
  children,
  onClose,
  busy,
}: {
  children: ReactNode;
  onClose: () => void;
  busy: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement;
    const dialog = ref.current!;
    dialog.showModal();
    return () => {
      dialog.close();
      if (previous instanceof HTMLElement && previous.isConnected)
        previous.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="review-dialog"
      aria-labelledby="review-title"
      aria-describedby="review-description"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="panel-heading">
        <h2 id="review-title">Review offline fixture installation</h2>
        <button
          className="text-button"
          onClick={onClose}
          disabled={busy}
          aria-label="Close installation review"
        >
          Close
        </button>
      </div>
      <p id="review-description">
        A small synthetic test file only. This cannot download AI weights or
        generate video.
      </p>
      {children}
    </dialog>
  );
}
