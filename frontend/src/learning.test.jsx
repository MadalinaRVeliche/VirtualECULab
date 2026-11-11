import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import LabEditor from "./LabEditor";
import ToolLab from "./ToolLab";
import { api } from "./api";
import fixtures from "./test/fixtures.json";

vi.mock("./api", async (original) => ({ ...(await original()), api: vi.fn() }));
let progress;
let history;

beforeEach(() => {
  vi.clearAllMocks();
  progress = {};
  history = [];
  api.mockImplementation(async (path, body) => {
    if (path === "/modules") return structuredClone(fixtures.modules);
    if (path === "/learning/progress") return structuredClone(progress);
    if (path.endsWith("/theory-reviewed")) {
      const id = path.split("/")[2];
      progress[id] = { ...progress[id], theory_reviewed: true };
      return { reviewed: true };
    }
    if (path.endsWith("/quiz-history")) return structuredClone(history);
    if (path.includes("/quiz") && body === undefined) {
      return {
        session_id: "00000000-0000-4000-8000-000000000001",
        questions: fixtures.foundation.map(
          ({ correct: _correct, explanation: _explanation, ...question }) =>
            question,
        ),
      };
    }
    if (path.endsWith("/quiz") && body) {
      const feedback = fixtures.foundation.map((q) => ({
        id: q.id,
        correct: body.answers[q.id] === q.correct,
        correct_answer: q.options[q.correct],
        explanation: q.explanation,
        topic: q.topic,
      }));
      const score = feedback.filter((f) => f.correct).length;
      history.push({
        id: history.length + 1,
        score,
        total: 5,
        created_at: "2026-11-10T12:00:00Z",
        missed_topics: feedback.filter((f) => !f.correct).map((f) => f.topic),
      });
      progress[1] = { quiz_attempts: history.length, best_percent: score * 20 };
      return { score, total: 5, feedback };
    }
    if (path === "/lab/run")
      return {
        time_ms: body.actions.reduce((sum, a) => sum + (a.ms || 0), 0),
        frames: [],
        console: [],
        variables: {},
        timers: {},
        events: [],
      };
    if (
      path.endsWith("/scenarios?challenge=false") ||
      path.endsWith("/scenarios?challenge=true")
    )
      return {
        frames: [{ counter: 5, corrupt: false }],
        max_lost: 0,
        cases: [],
      };
    if (path === "/tools/decode") return { raw: 0, physical: 0, unit: "km/h" };
    if (path.endsWith("/check"))
      return { passed: false, message: "Not yet.", checks: [] };
    throw new Error(`Unexpected test API request ${path}`);
  });
});

async function loadApp() {
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole("button", { name: /1\. Your first CAPL event/ });
  return user;
}

async function answerFoundation(user) {
  for (const q of fixtures.foundation)
    await user.click(
      screen.getByRole("radio", { name: q.options[q.correct], exact: true }),
    );
}

describe("learning workspace", () => {
  it("loads all eleven modules and the legacy practice editor", async () => {
    await loadApp();
    expect(
      within(screen.getByRole("navigation", { name: "Lessons" })).getAllByRole(
        "button",
      ),
    ).toHaveLength(11);
    expect(screen.getByLabelText("CAPL code", { exact: true })).toBeVisible();
  });

  it("shows theory and preserves an edited practice program across sections", async () => {
    const user = await loadApp();
    const editor = screen.getByLabelText("CAPL code", { exact: true });
    fireEvent.change(editor, {
      target: { value: 'on start { write("draft"); }' },
    });
    await user.click(
      screen.getByRole("button", { name: "Theory", exact: true }),
    );
    expect(
      screen.getByRole("heading", { name: "Theory", exact: true }),
    ).toBeVisible();
    expect(editor).not.toBeVisible();
    await user.click(
      screen.getByRole("button", { name: "Practice", exact: true }),
    );
    expect(editor).toHaveValue('on start { write("draft"); }');
  });

  it("marks theory reviewed without marking practical completion", async () => {
    const user = await loadApp();
    await user.click(
      screen.getByRole("button", { name: "Theory", exact: true }),
    );
    await user.click(
      screen.getByRole("button", { name: "Mark theory reviewed", exact: true }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Theory reviewed" }),
      ).toBeDisabled(),
    );
    expect(progress[1].theory_reviewed).toBe(true);
    expect(progress[1].practical_completed).toBeUndefined();
  });

  it("requires every quiz answer and sends the selected answers for server grading", async () => {
    const user = await loadApp();
    await user.click(screen.getByRole("button", { name: "Quiz", exact: true }));
    await screen.findByRole("radio", { name: "50 km/h", exact: true });
    const grade = screen.getByRole("button", {
      name: "Grade quiz",
      exact: true,
    });
    expect(grade).toBeDisabled();
    await answerFoundation(user);
    await user.click(grade);
    expect(
      await screen.findByText("Score: 5 / 5", { exact: true }),
    ).toBeVisible();
    const submission = api.mock.calls.find(
      ([path, body]) => path === "/modules/1/quiz" && body,
    );
    expect(submission[1].answers).toEqual(
      Object.fromEntries(fixtures.foundation.map((q) => [q.id, q.correct])),
    );
    expect(history).toHaveLength(1);
  });

  it("clears stale feedback when an answer changes and allows a new attempt", async () => {
    const user = await loadApp();
    await user.click(screen.getByRole("button", { name: "Quiz", exact: true }));
    await screen.findByRole("radio", { name: "50 km/h", exact: true });
    await answerFoundation(user);
    await user.click(
      screen.getByRole("button", { name: "Grade quiz", exact: true }),
    );
    await screen.findByText("Score: 5 / 5", { exact: true });
    await user.click(
      screen.getByRole("radio", { name: "100 km/h", exact: true }),
    );
    expect(
      screen.queryByText("Score: 5 / 5", { exact: true }),
    ).not.toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Grade quiz", exact: true }),
    );
    expect(
      await screen.findByText("Score: 4 / 5", { exact: true }),
    ).toBeVisible();
    expect(history).toHaveLength(2);
  });

  it("starts revision mode and resets selections", async () => {
    const user = await loadApp();
    await user.click(screen.getByRole("button", { name: "Quiz", exact: true }));
    await screen.findByRole("radio", { name: "50 km/h", exact: true });
    await answerFoundation(user);
    await user.click(
      screen.getByRole("button", { name: "Revise missed topics", exact: true }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith("/modules/1/quiz?revision=true"),
    );
    expect(
      screen.getByRole("button", { name: "Grade quiz", exact: true }),
    ).toBeDisabled();
    expect(screen.getAllByRole("radio").every((radio) => !radio.checked)).toBe(
      true,
    );
  });

  it("shows a recoverable backend error when quiz loading fails", async () => {
    const user = await loadApp();
    const original = api.getMockImplementation();
    api.mockImplementation(async (...args) => {
      if (args[0].includes("/quiz")) throw new Error("Database unavailable");
      return original(...args);
    });
    await user.click(screen.getByRole("button", { name: "Quiz", exact: true }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Database unavailable",
    );
    expect(screen.getByRole("button", { name: "Retry quiz" })).toBeVisible();
  });

  it("shows saved attempt history in Progress", async () => {
    const user = await loadApp();
    await user.click(screen.getByRole("button", { name: "Quiz", exact: true }));
    await screen.findByRole("radio", { name: "50 km/h", exact: true });
    await answerFoundation(user);
    await user.click(
      screen.getByRole("button", { name: "Grade quiz", exact: true }),
    );
    await screen.findByText("Score: 5 / 5", { exact: true });
    await user.click(
      screen.getByRole("button", { name: "Progress", exact: true }),
    );
    expect(await screen.findByText(/5\/5 ·/)).toBeVisible();
  });
});

describe("interactive lab controls", () => {
  it("replays accumulated actions rather than resetting state on each key", async () => {
    const user = userEvent.setup();
    render(
      <LabEditor
        module={fixtures.modules[4]}
        onUpdate={vi.fn()}
        onFrames={vi.fn()}
      />,
    );
    const send = screen.getByRole("button", { name: "Send key" });
    expect(send).toBeDisabled();
    await user.click(
      screen.getByRole("button", { name: "Start simulation", exact: true }),
    );
    await waitFor(() => expect(send).toBeEnabled());
    await user.click(send);
    await waitFor(() => expect(send).toBeEnabled());
    await user.click(send);
    const runs = api.mock.calls.filter(([path]) => path === "/lab/run");
    expect(runs.at(-1)[1].actions).toEqual([
      { type: "key", key: "a" },
      { type: "key", key: "a" },
    ]);
  });

  it("invalidates simulation controls after editing code", async () => {
    const user = userEvent.setup();
    render(
      <LabEditor
        module={fixtures.modules[5]}
        onUpdate={vi.fn()}
        onFrames={vi.fn()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Start simulation", exact: true }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Advance clock" }),
      ).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText("CAPL code", { exact: true }), {
      target: { value: "on start {}" },
    });
    expect(
      screen.getByRole("button", { name: "Advance clock" }),
    ).toBeDisabled();
  });

  it("keeps independent challenge code separate from the worked example", async () => {
    const user = userEvent.setup();
    render(
      <LabEditor
        module={fixtures.modules[3]}
        challenge
        onUpdate={vi.fn()}
        onFrames={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByLabelText("Challenge program"), {
      target: { value: "on start {}" },
    });
    await user.click(screen.getByRole("button", { name: "Check challenge" }));
    expect(api).toHaveBeenCalledWith("/modules/4/check", {
      code: "on start {}",
      challenge: true,
    });
  });

  it("decodes a zero payload without losing zero-valued settings", async () => {
    const user = userEvent.setup();
    render(<ToolLab module={fixtures.modules[7]} onUpdate={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Payload (hex)"), {
      target: { value: "00 00" },
    });
    await user.click(screen.getByRole("button", { name: "Decode payload" }));
    expect(api).toHaveBeenCalledWith("/tools/decode", {
      data: [0, 0],
      settings: {
        start_byte: 0,
        length: 2,
        byte_order: "little",
        factor: 0.01,
        offset: 0,
      },
    });
    expect(
      await screen.findByText("Raw 0 → 0 km/h", { exact: true }),
    ).toBeVisible();
  });
});
