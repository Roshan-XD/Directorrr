import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DirectorApi } from "../api/client";
import type {
  InstallationJob,
  InstallationPlan,
  RegisteredModel,
} from "../api/types";
import { InstallationWorkflow } from "../components/InstallationWorkflow";
import { ManagerAuthorization } from "../components/ManagerAuthorization";
import { App } from "../App";
import fixture from "./installation-fixture.json";
import registry from "./fixtures.json";

const modelId = "fixture-tiny";
const jobId = "a".repeat(32);
const key = "offline-test-manager-key-1234567890";
function job(state = "ready"): InstallationJob {
  return {
    id: jobId,
    model_id: modelId,
    operation: "install",
    state,
    total_expected_bytes: 60,
    candidate_bytes: state === "downloading" ? 30 : 60,
    verified_bytes: state === "ready" ? 60 : 0,
    cancel_requested: false,
    current_component: "tiny",
    error:
      state === "failed"
        ? {
            code: "interrupted",
            message: "Interrupted job; no automatic transfer resumed.",
          }
        : null,
    created_at: "2026-10-09T00:00:00Z",
    updated_at: "2026-10-09T00:00:00Z",
    generation_ready: false,
  };
}
function setup(
  options: {
    authorized?: boolean;
    allowFixture?: boolean;
    blocker?: boolean;
    state?: string;
    failure?: string;
    changed?: boolean;
    incompleteLicense?: boolean;
  } = {},
) {
  let state = options.state ?? "ready";
  const plan = structuredClone(fixture.plan) as InstallationPlan;
  if (options.blocker) {
    plan.artifact_review!.can_review = false;
    plan.artifact_review!.blockers = [
      {
        code: "insufficient_disk_space",
        message: "Not enough fixture storage",
      },
    ];
  }
  let planCalls = 0;
  const fetcher = vi.fn(
    async (url: string | URL | Request, init?: RequestInit) => {
      const path = String(url);
      let data: unknown;
      let status = 200;
      if (path.endsWith("/installation-plan")) {
        planCalls++;
        data =
          options.changed && planCalls > 1
            ? {
                ...plan,
                artifact_review: {
                  ...plan.artifact_review,
                  can_review: false,
                  blockers: [
                    {
                      code: "installation_busy",
                      message: "Another job is active",
                    },
                  ],
                },
              }
            : plan;
      } else if (path.endsWith("/license-requirements"))
        data = options.incompleteLicense
          ? { ...fixture.license, documents: [] }
          : fixture.license;
      else if (path.endsWith("/license-acknowledgements"))
        data = {
          id: "b".repeat(32),
          model_id: modelId,
          document_set_digest: fixture.license.document_set_digest,
          policy_version: "1",
          accepted_at: "2026-10-09T00:00:00Z",
        };
      else if (path.endsWith("/installations")) {
        if (options.failure) {
          status = 403;
          data = {
            detail: { code: "request_refused", message: options.failure },
          };
        } else {
          status = 202;
          data = job(state);
        }
      } else if (path.endsWith("/cancel")) {
        state = "cancelled";
        data = job(state);
      } else if (path.includes("/installation-jobs/")) data = job(state);
      else if (path === "/api/models")
        data = {
          ...registry.models,
          models: [...registry.models.models, fixture.item],
        };
      else if (path.endsWith("/installation"))
        data = {
          model_id: path.split("/")[3],
          state: "not_installed",
          artifact_ready: false,
          generation_ready: false,
          job_id: null,
          verification: [],
          incomplete_bundles: [],
        };
      else {
        status = 404;
        data = { detail: "Unknown test route" };
      }
      void init;
      return new Response(JSON.stringify(data), { status });
    },
  );
  const api = new DirectorApi("/api", 45000, fetcher);
  if (options.authorized !== false) api.setKey(key);
  const remember = vi.fn();
  const onComplete = vi.fn();
  const props = {
    api,
    item: fixture.item as RegisteredModel,
    plan,
    authorized: api.hasKey(),
    allowFixture: options.allowFixture !== false,
    remember,
    onComplete,
  };
  return { api, fetcher, props, remember, onComplete };
}
async function openReview() {
  const user = userEvent.setup();
  await user.click(
    screen.getByRole("button", { name: "Review license and installation" }),
  );
  await screen.findByRole("checkbox");
  return user;
}
async function accept(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("checkbox"));
  await user.click(
    screen.getByRole("button", { name: "Record acknowledgement" }),
  );
  await screen.findByRole("button", { name: "Acknowledgement recorded" });
}
const mutations = (fetcher: ReturnType<typeof vi.fn>) =>
  fetcher.mock.calls.filter((call) => call[1]?.method === "POST");

describe("fixture installation review", () => {
  it("closes after acknowledgement without installing and resets consent on reopening", async () => {
    const { props, fetcher } = setup();
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await accept(user);
    await user.click(
      screen.getByRole("button", { name: "Close installation review" }),
    );
    expect(mutations(fetcher)).toHaveLength(1);
    await openReview();
    expect(screen.getByRole("checkbox")).not.toBeChecked();
    expect(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    ).toBeDisabled();
  });
  it("blocks a freshly returned plan even if the outer card had an older reviewable snapshot", async () => {
    const { props, fetcher } = setup({ blocker: true });
    render(
      <InstallationWorkflow
        {...props}
        plan={fixture.plan as InstallationPlan}
      />,
    );
    const user = await openReview();
    await user.click(screen.getByRole("checkbox"));
    expect(
      screen.getByRole("button", { name: "Record acknowledgement" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    ).toBeDisabled();
    expect(mutations(fetcher)).toHaveLength(0);
  });
  it("shows acknowledgement API errors without advancing to installation", async () => {
    const { props, fetcher } = setup();
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    fetcher.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          detail: {
            code: "stale_license_documents",
            message: "Reviewed document version changed",
          },
        }),
        { status: 409 },
      ),
    );
    await user.click(screen.getByRole("checkbox"));
    await user.click(
      screen.getByRole("button", { name: "Record acknowledgement" }),
    );
    await screen.findByText("Reviewed document version changed");
    expect(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    ).toBeDisabled();
  });
  it("rejects ambiguous artifact readiness metadata in the API client", async () => {
    const { api, fetcher } = setup();
    fetcher.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          ...fixture.plan,
          artifact_review: {
            ...fixture.plan.artifact_review,
            expected_download_bytes: null,
          },
        }),
      ),
    );
    await expect(api.plan(modelId)).rejects.toMatchObject({
      code: "invalid_response",
    });
  });
  it("never sends a manager key on the license review read", async () => {
    const { api, fetcher } = setup();
    await api.licenses(modelId);
    expect(fetcher.mock.calls[0][1]?.headers).not.toHaveProperty(
      "X-Director-Key",
    );
  });
  it("loads only a read-only plan and never preselects acknowledgement or automatically installs", async () => {
    const { props, fetcher } = setup();
    render(<InstallationWorkflow {...props} />);
    await openReview();
    expect(
      screen.getByRole("dialog", {
        name: "Review offline fixture installation",
      }),
    ).toBeVisible();
    expect(screen.getByRole("checkbox")).not.toBeChecked();
    expect(
      screen.getByRole("button", { name: "Record acknowledgement" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    ).toBeDisabled();
    expect(screen.getByText(fixture.license.documents[0].text)).toBeVisible();
    expect(mutations(fetcher)).toHaveLength(0);
  });
  it("records explicit reviewed acknowledgement and requires a separate confirmation", async () => {
    const { props, fetcher } = setup();
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await accept(user);
    const requests = mutations(fetcher);
    expect(requests).toHaveLength(1);
    expect(JSON.parse(requests[0][1].body)).toEqual({
      accepted: true,
      document_set_digest: fixture.license.document_set_digest,
      policy_version: "1",
    });
    expect(requests[0][1].headers["X-Director-Key"]).toBe(key);
    expect(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    ).toBeEnabled();
  });
  it("installs the fixture, remembers only its job ID and displays verified success", async () => {
    const { props, fetcher, remember, onComplete } = setup();
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await accept(user);
    await user.click(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    );
    await screen.findByText(
      "Fixture files installed and verified. Generation remains unavailable.",
    );
    expect(remember).toHaveBeenCalledWith(jobId);
    expect(onComplete).toHaveBeenCalled();
    const request = mutations(fetcher)[1];
    expect(JSON.parse(request[1].body)).toEqual({
      manifest_digest: fixture.license.manifest_digest,
      acknowledgement_id: "b".repeat(32),
    });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
  it("blocks insufficient space and cannot open the review", () => {
    const { props, fetcher } = setup({ blocker: true });
    render(<InstallationWorkflow {...props} />);
    expect(screen.getByText("Not enough fixture storage")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Review license and installation" }),
    ).toBeDisabled();
    expect(mutations(fetcher)).toHaveLength(0);
  });
  it("requires an in-memory manager key", () => {
    const { props, fetcher } = setup({ authorized: false });
    render(<InstallationWorkflow {...props} />);
    expect(
      screen.getByRole("button", { name: "Review license and installation" }),
    ).toBeDisabled();
    expect(screen.getByText(/Enter your manager key above/)).toBeVisible();
    expect(mutations(fetcher)).toHaveLength(0);
  });
  it("never enables real Wan or non-development fixture installation", () => {
    const { props } = setup({ allowFixture: false });
    render(
      <InstallationWorkflow
        {...props}
        item={registry.models.models[2] as RegisteredModel}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Review license and installation" }),
    ).toBeDisabled();
    expect(
      screen.getByText(/Real-model installation, including Wan, is disabled/),
    ).toBeVisible();
  });
  it("shows backend refusals and does not repeat an uncertain installation mutation", async () => {
    const { props, fetcher } = setup({ failure: "Invalid local manager key" });
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await accept(user);
    await user.click(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    );
    await screen.findByText(/Invalid local manager key/);
    expect(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    ).toBeDisabled();
    expect(mutations(fetcher)).toHaveLength(2);
  });
  it("rechecks preflight before sending installation", async () => {
    const { props, fetcher } = setup({ changed: true });
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await accept(user);
    await user.click(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    );
    await screen.findByText(/preflight changed or is blocked/);
    expect(mutations(fetcher)).toHaveLength(1);
  });
  it("displays transfer and verification separately and can cancel active work", async () => {
    const { props } = setup({ state: "downloading" });
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await accept(user);
    await user.click(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    );
    await screen.findByRole("button", { name: "Cancel installation" });
    expect(
      screen.getByRole("progressbar", {
        name: "Installation transfer progress",
      }),
    ).toHaveAttribute("value", "30");
    expect(
      screen.getByRole("progressbar", {
        name: "Installation verification progress",
      }),
    ).toHaveAttribute("value", "0");
    await user.click(
      screen.getByRole("button", { name: "Cancel installation" }),
    );
    await screen.findByText("cancelled");
  });
  it("shows failure and interrupted recovery messages honestly", async () => {
    const { props } = setup({ state: "failed" });
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await accept(user);
    await user.click(
      screen.getByRole("button", { name: "Confirm offline installation" }),
    );
    await screen.findByText(/Interrupted job; no automatic transfer resumed/);
    expect(
      screen.queryByText(/Fixture files installed and verified/),
    ).not.toBeInTheDocument();
  });
  it("does not accept incomplete license metadata", async () => {
    const { props, fetcher } = setup({ incompleteLicense: true });
    render(<InstallationWorkflow {...props} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Review license and installation" }),
    );
    await screen.findByRole("alert");
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
    expect(mutations(fetcher)).toHaveLength(0);
  });
  it("returns keyboard focus to the invoking button on close", async () => {
    const { props } = setup();
    render(<InstallationWorkflow {...props} />);
    const user = await openReview();
    await user.click(
      screen.getByRole("button", { name: "Close installation review" }),
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Review license and installation" }),
    ).toHaveFocus();
  });
  it("keeps manager credentials out of browser storage and clears them explicitly", async () => {
    const { api } = setup({ authorized: false });
    const changed = vi.fn();
    render(<ManagerAuthorization api={api} onChange={changed} />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Manager key"), key);
    await user.click(screen.getByRole("button", { name: "Use key" }));
    expect(api.hasKey()).toBe(true);
    expect(screen.getByLabelText("Manager key")).toHaveValue("");
    expect(
      JSON.stringify({ ...localStorage, ...sessionStorage }),
    ).not.toContain(key);
    await user.click(screen.getByRole("button", { name: "Clear key" }));
    expect(api.hasKey()).toBe(false);
  });
  it("hides a backend fixture in ordinary frontend mode", async () => {
    window.location.hash = "#models";
    const { api } = setup();
    render(<App api={api} allowFixtures={false} />);
    await screen.findByText("Find your creative engine");
    await waitFor(() =>
      expect(
        screen.queryByText(fixture.item.manifest.name),
      ).not.toBeInTheDocument(),
    );
    expect(
      screen.queryByText(/Local development fixture mode is enabled/),
    ).not.toBeInTheDocument();
  });
  it("exposes the clearly labelled fixture only with explicit development opt-in", async () => {
    window.location.hash = "#models";
    const { api } = setup();
    render(<App api={api} allowFixtures={true} />);
    await screen.findByRole("heading", { name: fixture.item.manifest.name });
    expect(
      screen.getByText(/Local development fixture mode is enabled/),
    ).toBeVisible();
  });
});
