import { useState } from "react";
import { api, hexBytes } from "./api";

export default function LabEditor({ module, challenge = false, onUpdate, onFrames }) {
  const starter = challenge ? module.challenge_code : module.code;
  const [code, setCode] = useState(starter);
  const [actions, setActions] = useState([]);
  const [result, setResult] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [key, setKey] = useState("a");
  const [advance, setAdvance] = useState(100);
  const [rxId, setRxId] = useState("300");
  const [rxData, setRxData] = useState("01");

  function clearRun() { setActions([]); setResult(null); setAssessment(null); setError(""); }

  async function run(action = null) {
    const next = action ? [...actions, action] : [];
    setBusy(true); setError(""); setAssessment(null);
    try {
      const outcome = await api("/lab/run", { code, actions: next });
      setActions(next); setResult(outcome); onFrames(outcome.frames);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function receive() {
    try {
      const text = rxId.trim().replace(/^0x/i, "");
      if (!/^[0-9a-f]{1,3}$/i.test(text) || Number.parseInt(text, 16) > 0x7ff) throw new Error("Rx identifier must be hexadecimal 000–7FF.");
      await run({ type: "rx", identifier: Number.parseInt(text, 16), data: hexBytes(rxData) });
    } catch (err) { setError(err.message); }
  }

  async function check() {
    setBusy(true); setError("");
    try {
      const outcome = await api(`/modules/${module.id}/check`, { code, challenge });
      setAssessment(outcome); if (outcome.passed) onUpdate();
    } catch (err) { setError(err.message); setAssessment(null); }
    finally { setBusy(false); }
  }

  const prefix = challenge ? "challenge" : "practice";
  return <article className="lab-editor">
    <div className="panel-title"><h2>{challenge ? "Independent challenge" : "CAPL workbench"}</h2><span className="chip">Virtual time · bounded subset</span></div>
    <p><strong>{challenge ? "Challenge" : "Exercise"}:</strong> {challenge ? module.challenge : module.task}</p>
    <label htmlFor={`${prefix}-code`}>{challenge ? "Challenge program" : "CAPL code"}</label>
    <textarea id={`${prefix}-code`} value={code} rows={16} spellCheck={false} disabled={busy} onChange={(event) => { setCode(event.target.value); clearRun(); }} />
    <div className="toolbar">
      <button onClick={() => run()} disabled={busy}>{challenge ? "Start challenge simulation" : "Start simulation"}</button>
      <button onClick={check} disabled={busy}>{challenge ? "Check challenge" : "Check exercise"}</button>
      <button onClick={() => { setCode(starter); clearRun(); }} disabled={busy}>Reset program</button>
    </div>
    <p className="muted">Start resets time and state. Edits invalidate the action history. Changing learning sections preserves this workbench. No real hardware is accessed.</p>
    <fieldset disabled={busy || !result}><legend>Simulation controls</legend>
      <div className="control-grid">
        <label htmlFor={`${prefix}-key`}>Key character<input id={`${prefix}-key`} value={key} maxLength={1} onChange={(event) => setKey(event.target.value)} /></label>
        <button disabled={!key || busy || !result} onClick={() => run({ type: "key", key })}>Send key</button>
        <label htmlFor={`${prefix}-advance`}>Advance time (ms)<input id={`${prefix}-advance`} type="number" min="0" max="60000" step="1" value={advance} onChange={(event) => setAdvance(event.target.value)} /></label>
        <button onClick={() => run({ type: "advance", ms: Number(advance) })}>Advance clock</button>
        <label htmlFor={`${prefix}-rxid`}>Receive ID (hex)<input id={`${prefix}-rxid`} value={rxId} onChange={(event) => setRxId(event.target.value)} /></label>
        <label htmlFor={`${prefix}-rxdata`}>Receive bytes (hex)<input id={`${prefix}-rxdata`} value={rxData} onChange={(event) => setRxData(event.target.value)} /></label>
        <button onClick={receive}>Inject Rx frame</button>
      </div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
    {result && <>
      <div className="milestone-grid"><div><small>Virtual clock</small><strong data-testid="virtual-clock">{result.time_ms} ms</strong></div><div><small>Input actions</small><strong>{actions.length}</strong></div><div><small>Frames</small><strong>{result.frames.length}</strong></div></div>
      <h3>Console</h3><div className="console" aria-live="polite"><pre>{result.console.map((entry) => `[${entry.time_ms} ms] ${entry.text}`).join("\n") || "No console output."}</pre></div>
      <details><summary>State and event evidence</summary><pre>{JSON.stringify({ variables: result.variables, timers: result.timers, events: result.events }, null, 2)}</pre></details>
      {challenge && <details><summary>Challenge trace</summary><pre>{JSON.stringify(result.frames, null, 2)}</pre></details>}
    </>}
    {assessment && <div className="assessment"><p role="status" className={assessment.passed ? "success" : "warning"}>{assessment.message}</p><ul>{assessment.checks.map((item, index) => <li key={index}><strong>{item.passed ? "PASS" : "FAIL"}</strong> · {item.name}{!item.passed && <pre>{JSON.stringify({ observed: item.actual, expected: item.expected }, null, 2)}</pre>}</li>)}</ul><p className="muted">Checks run a separate, fresh scenario replay. They do not add traffic to your interactive trace.</p></div>}
  </article>;
}
