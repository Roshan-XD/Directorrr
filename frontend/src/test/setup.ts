import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach } from "vitest";
// jsdom does not implement native dialog layout/focus isolation. Actual browser
// smoke checks separately exercise showModal, Escape and keyboard focus.
HTMLDialogElement.prototype.showModal = function () {
  this.open = true;
  this.querySelector<HTMLElement>("button")?.focus();
};
HTMLDialogElement.prototype.close = function () {
  this.open = false;
};
// Let queued jsdom hashchange events finish between independent app mounts.
beforeEach(async () => {
  window.location.hash = "";
  await new Promise((resolve) => setTimeout(resolve, 0));
});
afterEach(() => {
  cleanup();
  sessionStorage.clear();
  window.location.hash = "";
});
