import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import { api } from "./api";
import { checkTrace, decodeSignal, parseDbc } from "./workbenchData";

vi.mock("./api", async (original) => ({ ...(await original()), api: vi.fn() }));

const dbc =
  'BO_ 291 VehicleSpeed: 2 SpeedECU\n SG_ Speed : 0|16@1+ (0.01,0) [0|655.35] "km/h" DisplayECU';
const questions = (prefix) =>
  Array.from({ length: 10 }, (_, i) => ({
    id: `${prefix}-${i}`,
    prompt: `${prefix} question ${i + 1}`,
    options: ["A", "B", "C"],
  }));
const tx = {
  direction: "Tx",
  identifier: 0x123,
  time_ms: 100,
  dlc: 2,
  data: [0x10, 0x27],
};

beforeEach(() => {
  vi.clearAllMocks();
  globalThis.fetch = vi.fn(async () => ({ ok: true, text: async () => dbc }));
  api.mockImplementation(async (path, body) => {
    if (path === "/modules")
      return [
        { id: 0, kind: "theory", sources: [] },
        {
          id: 4,
          title: "Transmit vehicle speed",
          theory: [{ title: "Signal definition", text: "A signal example." }],
        },
      ];
    if (path === "/modules/0/quiz-history")
      return [
        { id: 1, score: 10, total: 10, created_at: "2026-11-11T10:00:00Z" },
      ];
    if (path === "/modules/0/quiz" && body)
      return { score: 10, total: 10, feedback: [] };
    if (path === "/modules/0/quiz")
      return { session_id: "first", questions: questions("First") };
    if (path.includes("previous_session=first"))
      return { session_id: "next", questions: questions("Next") };
    if (path === "/lab/run")
      return {
        time_ms: body.actions.reduce(
          (sum, action) => sum + (action.ms ?? 0),
          0,
        ),
        frames: body.actions.some((action) => action.type === "rx")
          ? [{ ...tx, time_ms: 0 }]
          : [],
        console: [{ time_ms: 0, text: "Speed relay ready" }],
      };
    throw new Error(`Unexpected path ${path}`);
  });
});

describe("course navigation", () => {
  it("switches the foundations and applied theory between Romanian and English", async () => {
    localStorage.removeItem("virtualeculab.theory.language");
    const user = userEvent.setup();
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Noțiuni de bază" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Teorie aplicată" }),
    ).toBeVisible();

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Limba teoriei" }),
      "en",
    );

    expect(screen.getByRole("heading", { name: "Foundations" })).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Applied theory" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", {
        name: "From a CAN frame to speed on the graph",
      }),
    ).toBeVisible();

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Theory language" }),
      "ro",
    );

    expect(
      screen.getByRole("heading", { name: "Teorie aplicată" }),
    ).toBeVisible();
  });

  it("grades the course quiz and starts a fresh set through module zero", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Quiz" }));
    const quiz = await screen.findByRole("region", { name: "Course quiz" });
    const form = await within(quiz).findByRole("form", {
      name: "Quiz answers",
    });
    const groups = within(form).getAllByRole("group");
    expect(groups).toHaveLength(10);
    const grade = within(quiz).getByRole("button", { name: "Grade quiz" });
    expect(grade).toBeDisabled();
    for (const group of groups)
      await user.click(within(group).getByRole("radio", { name: "A" }));
    await user.click(grade);
    expect(await within(quiz).findByText("Score: 10 / 10")).toBeVisible();
    await user.click(within(quiz).getByRole("button", { name: "New quiz" }));
    expect(await within(quiz).findByText("1. Next question 1")).toBeVisible();
    expect(grade).toBeDisabled();
    expect(api).toHaveBeenCalledWith(
      "/modules/0/quiz?revision=false&previous_session=first",
    );
  });

  it("keeps a CAPL draft while switching tabs and restarts after edits", async () => {
    const user = userEvent.setup();
    render(<App />);
    const workbench = screen.getByRole("button", { name: "Workbench" });
    await user.click(workbench);
    const code = screen.getByLabelText("CAPL node program");
    fireEvent.change(code, { target: { value: "on start {}" } });
    await user.click(screen.getByRole("button", { name: "Theory" }));
    await user.click(workbench);
    expect(code).toHaveValue("on start {}");
    const inject = screen.getByRole("button", { name: "Inject Rx" });
    expect(inject).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Start measurement" }));
    await user.click(inject);
    expect(await screen.findByText("CAN Trace · 1 frames")).toBeVisible();
    fireEvent.change(code, { target: { value: "on start { }" } });
    expect(inject).toBeDisabled();
    expect(screen.getByText("CAN Trace · 0 frames")).toBeVisible();
  });
});

describe("DBC and trace checks", () => {
  it("decodes the matching little-endian sample and ignores mismatched or short frames", () => {
    const [signal] = parseDbc(dbc);
    expect(decodeSignal(tx, signal)).toBe(100);
    expect(decodeSignal({ ...tx, identifier: 0x120 }, signal)).toBeNull();
    expect(decodeSignal({ ...tx, data: [0x10] }, signal)).toBeNull();
  });

  it("decodes byte-aligned signed Motorola values", () => {
    const [signal] = parseDbc(
      'BO_ 10 Value: 2 Sender\n SG_ Raw : 7|16@0- (0.5,1) [-200|200] "V" Receiver',
    );
    expect(decodeSignal({ identifier: 10, data: [0xff, 0xfc] }, signal)).toBe(
      -1,
    );
  });

  it("rejects overlapping message IDs and unsupported bit alignment", () => {
    expect(() => parseDbc(`${dbc}\nBO_ 291 Repeat: 2 ECU`)).toThrow(
      "already defined",
    );
    expect(() => parseDbc(dbc.replace("0|16", "1|16"))).toThrow("byte-aligned");
  });

  it("accepts the inclusive boundary and ignores earlier same-time frames", () => {
    const args = {
      identifier: 0x123,
      direction: "Tx",
      deadline: 100,
      payload: tx.data,
    };
    expect(
      checkTrace({
        ...args,
        measurement: { time_ms: 100, frames: [tx] },
        origin: { time: 0, frameIndex: 0 },
      }).verdict,
    ).toBe("PASS");
    expect(
      checkTrace({
        ...args,
        measurement: { time_ms: 200, frames: [tx] },
        origin: { time: 100, frameIndex: 1 },
      }).verdict,
    ).toBe("FAIL");
  });

  it("distinguishes pending, timeout, late and wrong payload", () => {
    const args = {
      identifier: 0x123,
      direction: "Tx",
      deadline: 100,
      payload: tx.data,
      origin: { time: 0, frameIndex: 0 },
    };
    expect(
      checkTrace({ ...args, measurement: { time_ms: 50, frames: [] } }).verdict,
    ).toBe("PENDING");
    expect(
      checkTrace({
        ...args,
        measurement: { time_ms: 100, frames: [{ ...tx, data: [0, 0] }] },
      }).verdict,
    ).toBe("FAIL");
    expect(
      checkTrace({
        ...args,
        measurement: { time_ms: 110, frames: [{ ...tx, time_ms: 110 }] },
      }).reason,
    ).toContain("110 ms");
  });
});
