import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { DirectorApi } from "../api/client";
import { DevelopmentTimeline } from "../components/DevelopmentTimeline";

function setup(existing = false, failure = false) {
  const fetcher = vi.fn(async (_url: unknown, options?: RequestInit) => {
    if (options?.method === "POST")
      return failure
        ? Response.json(
            { detail: { message: "Insertion failed; inspect Resolve" } },
            { status: 502 },
          )
        : Response.json({
            development_only: true,
            state: "placed",
            project: "Director Development",
            timeline: "Director AI Test",
            item_id: "item",
            duration_seconds: 1.0833,
          });
    return Response.json({
      development_only: true,
      project: "Director Development",
      media_id: "known",
      current_timeline_id: null,
      timelines: existing ? [{ id: "target", name: "Selected timeline" }] : [],
    });
  });
  const api = new DirectorApi("/api", 45000, fetcher as typeof fetch);
  api.setKey("k".repeat(32));
  render(<DevelopmentTimeline api={api} authorized />);
  return { fetcher, user: userEvent.setup() };
}
it("requires review and unchecked explicit approval before creating a timeline", async () => {
  const { fetcher, user } = setup();
  expect(fetcher).not.toHaveBeenCalled();
  await user.click(
    screen.getByRole("button", { name: "Review Resolve timelines" }),
  );
  const checkbox = await screen.findByRole("checkbox");
  expect(checkbox).not.toBeChecked();
  expect(
    screen.getByRole("button", { name: "Add to Timeline" }),
  ).toBeDisabled();
  await user.click(checkbox);
  await user.click(screen.getByRole("button", { name: "Add to Timeline" }));
  expect(
    await screen.findByText(/Placed the Stage 9 clip/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Add to Timeline" }),
  ).toBeDisabled();
  expect(JSON.parse(String(fetcher.mock.calls[1][1]?.body))).toMatchObject({
    confirmed: true,
    create_new: true,
  });
});
it("requires target selection for an existing timeline", async () => {
  const { user, fetcher } = setup(true);
  await user.click(
    screen.getByRole("button", { name: "Review Resolve timelines" }),
  );
  await user.click(await screen.findByRole("checkbox"));
  expect(
    screen.getByRole("button", { name: "Add to Timeline" }),
  ).toBeDisabled();
  await user.selectOptions(screen.getByLabelText("Target timeline"), "target");
  expect(screen.getByRole("checkbox")).not.toBeChecked();
  await user.click(screen.getByRole("checkbox"));
  await user.click(screen.getByRole("button", { name: "Add to Timeline" }));
  await screen.findByText(/Placed the Stage 9 clip/);
  expect(JSON.parse(String(fetcher.mock.calls[1][1]?.body))).toMatchObject({
    timeline_id: "target",
    create_new: false,
  });
});
it("shows failure without claiming insertion success or retrying", async () => {
  const { user, fetcher } = setup(false, true);
  await user.click(
    screen.getByRole("button", { name: "Review Resolve timelines" }),
  );
  await user.click(await screen.findByRole("checkbox"));
  await user.click(screen.getByRole("button", { name: "Add to Timeline" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Insertion failed",
  );
  expect(
    fetcher.mock.calls.filter(([, options]) => options?.method === "POST"),
  ).toHaveLength(1);
});
