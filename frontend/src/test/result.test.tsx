import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { DirectorApi, validateResponse } from "../api/client";
import { DevelopmentResult } from "../components/DevelopmentResult";

const id = "c".repeat(32);
function setup(error = false) {
  let state = "generated";
  const fetcher = vi.fn(async (url: unknown, options?: RequestInit) => {
    const path = String(url);
    if (error && path.endsWith("/import"))
      return Response.json(
        { detail: { message: "Media Pool import failed" } },
        { status: 502 },
      );
    if (path.endsWith("/timelines"))
      return Response.json({
        development_only: true,
        project: "Director Development",
        media_id: "historical",
        current_timeline_id: null,
        timelines: [{ id: "target", name: "Director AI Test" }],
      });
    if (path.endsWith("/import") && options?.method === "POST")
      state = "imported";
    if (path.endsWith("/placement") && options?.method === "POST")
      state = "placed";
    return Response.json({
      development_only: true,
      job_id: id,
      state,
      filename: `Director_${id}.mp4`,
      media_id: "new-media",
      message: state === "placed" ? "Placed on timeline" : "Ready for timeline",
      placement:
        state === "placed"
          ? {
              development_only: true,
              state: "placed",
              project: "Director Development",
              timeline: "Director AI Test",
              item_id: "new-item",
              duration_seconds: 1.041667,
            }
          : undefined,
    });
  });
  const api = new DirectorApi("/api", 45000, fetcher as typeof fetch);
  api.setKey("k".repeat(32));
  render(<DevelopmentResult api={api} jobId={id} authorized />);
  return { fetcher, user: userEvent.setup() };
}
it("imports the new job and requires selection and confirmation before placement", async () => {
  const { user, fetcher } = setup();
  expect(fetcher).not.toHaveBeenCalled();
  expect(
    screen.queryByRole("button", { name: "Add to Timeline" }),
  ).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Import to Resolve" }));
  await screen.findByText(/Media Pool item: new-media/);
  expect(
    screen.getByRole("button", { name: "Import to Resolve" }),
  ).toBeDisabled();
  await user.click(
    screen.getByRole("button", { name: "Review Resolve timelines" }),
  );
  expect(await screen.findByRole("checkbox")).not.toBeChecked();
  expect(
    screen.getByRole("button", { name: "Add to Timeline" }),
  ).toBeDisabled();
  await user.selectOptions(screen.getByLabelText("Target timeline"), "target");
  await user.click(screen.getByRole("checkbox"));
  await user.click(screen.getByRole("button", { name: "Add to Timeline" }));
  await screen.findByText("Placed on Director AI Test.");
  const mutations = fetcher.mock.calls.filter(
    ([, options]) => options?.method === "POST",
  );
  expect(mutations).toHaveLength(2);
  expect(String(mutations[0][0])).toContain(`/jobs/${id}/import`);
  expect(String(mutations[1][0])).toContain(`/jobs/${id}/placement`);
  expect(JSON.parse(String(mutations[1][1]?.body))).toMatchObject({
    confirmed: true,
    timeline_id: "target",
    create_new: false,
  });
});
it("declining placement leaves the imported job unchanged", async () => {
  const { user, fetcher } = setup();
  await user.click(screen.getByRole("button", { name: "Import to Resolve" }));
  await user.click(
    await screen.findByRole("button", { name: "Review Resolve timelines" }),
  );
  await user.click(
    await screen.findByRole("button", { name: "Decline placement" }),
  );
  await screen.findByText("Placement declined; no timeline change requested.");
  expect(
    fetcher.mock.calls.filter(([, options]) => options?.method === "POST"),
  ).toHaveLength(1);
});
it("shows an import error and prevents blind duplicate requests", async () => {
  const { user, fetcher } = setup(true);
  await user.click(screen.getByRole("button", { name: "Import to Resolve" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Media Pool import failed",
  );
  expect(
    screen.getByRole("button", { name: "Import to Resolve" }),
  ).toBeDisabled();
  expect(fetcher.mock.calls).toHaveLength(1);
});
it("rejects a result for an arbitrary output filename", () => {
  expect(() =>
    validateResponse(
      {
        development_only: true,
        job_id: id,
        state: "imported",
        media_id: "new",
        filename: "../../secret.mp4",
      },
      "resolveResult",
    ),
  ).toThrow();
});
