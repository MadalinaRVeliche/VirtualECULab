import { useEffect, useState } from "react";
import { api, hexBytes } from "./api";
import TraceGraph from "./TraceGraph";
import {
  canId,
  checkTrace,
  parseDbc,
  programs,
  testModuleExample,
} from "./workbenchData";

const hex = (value, width) =>
  value.toString(16).toUpperCase().padStart(width, "0");

export default function Workbench() {
  const [preset, setPreset] = useState("relay");
  const [code, setCode] = useState(programs.relay.code);

  // Keep the input history separate from the last successful simulation result.
  // The history is sent to FastAPI; the result drives the console, trace, and graph.
  const [actions, setActions] = useState([]);
  const [measurement, setMeasurement] = useState(null);
  const [lastInput, setLastInput] = useState(null);
  const [key, setKey] = useState("a");
  const [advance, setAdvance] = useState("100");
  const [rxId, setRxId] = useState("120");
  const [rxBytes, setRxBytes] = useState("10 27");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Keep the editable DBC text separate from the last valid signal definitions.
  // The graph changes only after a DBC is loaded or successfully applied.
  const [dbc, setDbc] = useState("");
  const [signals, setSignals] = useState([]);
  const [signalId, setSignalId] = useState("");
  const [dbcError, setDbcError] = useState("");
  const [test, setTest] = useState({
    origin: "last",
    direction: "Tx",
    id: "123",
    deadline: "100",
    bytes: "",
  });
  const [verdict, setVerdict] = useState(null);
  const [testError, setTestError] = useState("");

  useEffect(() => {
    // The sample DBC is bundled with the frontend. Load it when the
    // Workbench mounts so the default relay can be plotted as vehicle speed.
    const controller = new AbortController();
    fetch(`${import.meta.env.BASE_URL}VehicleSpeed.dbc`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error("Could not load the sample DBC.");
        return response.text();
      })
      .then((text) => {
        const parsed = parseDbc(text);
        setDbc(text);
        setSignals(parsed);
        setSignalId(parsed[0].id);
      })
      .catch((err) => {
        if (err.name !== "AbortError") setDbcError(err.message);
      });
    return () => controller.abort();
  }, []);

  function editCode(next) {
    // The old trace belongs to the previous program. Clear it and require
    // a new measurement after an edit, preset change, or example reset.
    setCode(next);
    setActions([]);
    setMeasurement(null);
    setLastInput(null);
    setVerdict(null);
    setError("");
  }

  async function run(action = null) {
    // FastAPI replays the program from time zero on each request. Starting
    // a measurement sends an empty history; other controls append one action.
    const next = action ? [...actions, action] : [];
    setBusy(true);
    setError("");
    try {
      const result = await api("/lab/run", { code, actions: next });
      if (!action) setLastInput(null);
      else if (action.type === "rx" || action.type === "key") {
        // Capture the timestamp and frame count from before this stimulus.
        // Earlier frames can share its timestamp, so the frame index matters.
        setLastInput({
          time: measurement.time_ms,
          frameIndex: measurement.frames.length,
        });
      }

      // Save the new action only after a successful replay. If an input
      // fails, the previous trace and action history remain usable.
      setActions(next);
      setMeasurement(result);
      setVerdict(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function addRx(event) {
    event.preventDefault();
    try {
      // Convert the hex text from the form to numeric CAN ID and data bytes
      // before sending the Rx action to the simulation API.
      void run({
        type: "rx",
        identifier: canId(rxId),
        data: hexBytes(rxBytes),
      });
    } catch (err) {
      setError(err.message);
    }
  }

  function applyDbc(event) {
    event.preventDefault();
    try {
      // Reinterpret the frames already in memory. Applying a DBC does not
      // rerun the CAPL program or change the raw trace.
      const parsed = parseDbc(dbc);
      setSignals(parsed);
      setSignalId(
        parsed.some((signal) => signal.id === signalId)
          ? signalId
          : parsed[0].id,
      );
      setDbcError("");
    } catch (err) {
      setDbcError(err.message);
    }
  }

  function check(event) {
    event.preventDefault();
    setTestError("");
    setVerdict(null);
    try {
      // The check reads the current trace. It starts either at time zero
      // or at the latest Rx/key stimulus. Advancing time keeps that origin.
      const origin =
        test.origin === "start" ? { time: 0, frameIndex: 0 } : lastInput;
      if (measurement && !origin)
        throw new Error(
          "Send a key or inject Rx to mark the stimulus, or select Start of measurement.",
        );
      setVerdict(
        checkTrace({
          measurement,
          origin,
          identifier: canId(test.id),
          direction: test.direction,
          deadline: Number(test.deadline),
          payload: test.bytes.trim() ? hexBytes(test.bytes) : null,
        }),
      );
    } catch (err) {
      setTestError(err.message);
    }
  }

  const frames = measurement?.frames ?? [];
  const signal = signals.find((entry) => entry.id === signalId);

  // A stimulus needs an active measurement. Disable the controls during a
  // replay so two inputs cannot be submitted against the same history.
  const locked = busy || !measurement;
  return (
    <div className="workbench">
      <article>
        <div className="panel-title">
          <h2>Simulation Setup</h2>
          <label>
            CAPL example
            <select
              value={preset}
              disabled={busy}
              onChange={(event) => {
                const next = event.target.value;
                setPreset(next);
                editCode(programs[next].code);
              }}
            >
              {Object.entries(programs).map(([id, entry]) => (
                <option key={id} value={id}>
                  {entry.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p>{programs[preset].hint}</p>
        <div className="workbench-grid">
          <div>
            <label htmlFor="workbench-code">CAPL node program</label>
            <textarea
              id="workbench-code"
              rows={15}
              value={code}
              disabled={busy}
              spellCheck={false}
              onChange={(event) => editCode(event.target.value)}
            />
            <div className="toolbar">
              <button disabled={busy || !code.trim()} onClick={() => run()}>
                Start measurement
              </button>
              <button
                disabled={busy}
                onClick={() => editCode(programs[preset].code)}
              >
                Reset example
              </button>
            </div>
          </div>
          <div>
            <h3>Measurement controls</h3>
            <p>
              Virtual clock <strong>{measurement?.time_ms ?? 0} ms</strong>
              {!measurement && " · Start measurement to enable inputs."}
            </p>
            <fieldset disabled={locked}>
              <legend>Stimulus and time</legend>
              <form
                className="workbench-action"
                onSubmit={(event) => {
                  event.preventDefault();
                  void run({ type: "key", key });
                }}
              >
                <label>
                  Key
                  <input
                    value={key}
                    maxLength={1}
                    onChange={(event) => setKey(event.target.value)}
                    required
                  />
                </label>
                <button>Send key</button>
              </form>
              <form
                className="workbench-action"
                onSubmit={(event) => {
                  event.preventDefault();
                  void run({ type: "advance", ms: Number(advance) });
                }}
              >
                <label>
                  Advance (ms)
                  <input
                    type="number"
                    min="1"
                    max="60000"
                    value={advance}
                    onChange={(event) => setAdvance(event.target.value)}
                    required
                  />
                </label>
                <button>Advance clock</button>
              </form>
              <form className="workbench-action rx-action" onSubmit={addRx}>
                <label>
                  Rx ID (hex)
                  <input
                    value={rxId}
                    onChange={(event) => setRxId(event.target.value)}
                    required
                  />
                </label>
                <label>
                  Rx bytes (hex)
                  <input
                    value={rxBytes}
                    onChange={(event) => setRxBytes(event.target.value)}
                  />
                </label>
                <button>Inject Rx</button>
              </form>
            </fieldset>
            {error && <p role="alert">{error}</p>}
            <h3>Write console</h3>
            <pre aria-live="polite">
              {measurement?.console
                .map((entry) => `[${entry.time_ms} ms] ${entry.text}`)
                .join("\n") || "No output yet."}
            </pre>
          </div>
        </div>
      </article>

      <article aria-label="Trace and Graphics">
        <div className="panel-title">
          <h2>Trace &amp; Graphics</h2>
          <label>
            Graph signal
            <select
              value={signalId}
              onChange={(event) => setSignalId(event.target.value)}
            >
              <option value="">Rx and Tx timeline</option>
              {signals.map((entry) => (
                <option value={entry.id} key={entry.id}>
                  {entry.message.name}.{entry.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <TraceGraph
          frames={frames}
          time={measurement?.time_ms ?? 0}
          signal={signal}
        />
        <details open>
          <summary>CAN Trace · {frames.length} frames</summary>
          <div className="trace-table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Time (ms)</th>
                  <th>Direction</th>
                  <th>ID (hex)</th>
                  <th>DLC</th>
                  <th>Data (hex)</th>
                </tr>
              </thead>
              <tbody>
                {frames.map((frame, index) => (
                  <tr key={index}>
                    <td>{frame.time_ms}</td>
                    <td>{frame.direction}</td>
                    <td>{hex(frame.identifier, 3)}</td>
                    <td>{frame.dlc}</td>
                    <td>{frame.data.map((byte) => hex(byte, 2)).join(" ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
        <details>
          <summary>DBC editor</summary>
          <p>
            Apply a DBC to decode the existing trace. Supports byte-aligned
            standard CAN signals, signed or unsigned, up to 6 bytes.
          </p>
          <form onSubmit={applyDbc}>
            <label htmlFor="dbc-text">DBC source</label>
            <textarea
              id="dbc-text"
              rows={8}
              value={dbc}
              onChange={(event) => setDbc(event.target.value)}
              spellCheck={false}
            />
            <button>Apply DBC</button>
            {dbcError && <p role="alert">{dbcError}</p>}
          </form>
        </details>
      </article>

      <article aria-label="Test Module">
        <h2>Test Module</h2>
        <p>
          Check the first matching frame after the chosen stimulus. Use the
          clock to finish the wait if the result is pending.
        </p>
        <form onSubmit={check}>
          <div className="control-grid">
            <label>
              Start waiting at
              <select
                value={test.origin}
                onChange={(event) => updateTest("origin", event.target.value)}
              >
                <option value="last">Last key or Rx</option>
                <option value="start">Start of measurement</option>
              </select>
            </label>
            <label>
              Expected direction
              <select
                value={test.direction}
                onChange={(event) =>
                  updateTest("direction", event.target.value)
                }
              >
                <option>Tx</option>
                <option>Rx</option>
              </select>
            </label>
            <label>
              Expected ID (hex)
              <input
                value={test.id}
                onChange={(event) => updateTest("id", event.target.value)}
                required
              />
            </label>
            <label>
              Deadline (ms)
              <input
                type="number"
                min="0"
                max="60000"
                value={test.deadline}
                onChange={(event) => updateTest("deadline", event.target.value)}
                required
              />
            </label>
            <label>
              Expected bytes (optional)
              <input
                value={test.bytes}
                onChange={(event) => updateTest("bytes", event.target.value)}
              />
            </label>
          </div>
          <button disabled={busy}>Run trace check</button>
        </form>
        {testError && <p role="alert">{testError}</p>}
        {verdict && (
          <p
            role="status"
            className={verdict.verdict === "PASS" ? "success" : "warning"}
          >
            <strong>{verdict.verdict}</strong> · {verdict.reason}
          </p>
        )}
        <details>
          <summary>See the equivalent CANoe CAPL structure</summary>
          <p>
            This example runs in a CANoe Test Module with VehicleSpeed defined
            in its database. The browser executes the trace check above.
          </p>
          <pre>{testModuleExample}</pre>
        </details>
      </article>
    </div>
  );

  function updateTest(name, value) {
    // A displayed verdict applies only to the settings used when it ran.
    setTest((previous) => ({ ...previous, [name]: value }));
    setVerdict(null);
    setTestError("");
  }
}
