import { useEffect, useState } from "react";
import { api, hexBytes } from "./api";

const E2E_STATUSES = ["INITIAL", "OK", "OK_SOME_LOST", "REPEATED", "WRONG_CRC", "WRONG_SEQUENCE"];
const VERDICTS = ["PASS", "FAIL", "NOT_EXECUTED"];
const ADAS_STATES = ["BRAKE_REQUEST", "MONITORING", "DEGRADED", "OFF", "ACTIVE", "OVERRIDDEN"];

export default function ToolLab({ module, challenge = false, onUpdate }) {
  const [settings, setSettings] = useState({ start_byte: 0, length: 2, byte_order: "little", factor: 0.01, offset: 0 });
  const [data, setData] = useState("10 27");
  const [scenario, setScenario] = useState(null);
  const [predictions, setPredictions] = useState({});
  const [strategy, setStrategy] = useState("immediate");
  const [deadline, setDeadline] = useState(100);
  const [explorer, setExplorer] = useState({ mode: "AEB", distance_m: 20, ego_kmh: 72, target_kmh: 36, threshold_s: 2, sensor_valid: true, obstacle_in_path: true, brake_pressed: false, enabled: true });
  const [result, setResult] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [counters, setCounters] = useState("5,6,7,7,8");
  const [maxLost, setMaxLost] = useState(0);
  const [corruptIndex, setCorruptIndex] = useState(-1);

  useEffect(() => {
    if (module.id < 9) return;
    const controller = new AbortController();
    api(`/modules/${module.id}/scenarios?challenge=${challenge}`, undefined, controller.signal).then(setScenario).catch((err) => { if (err.name !== "AbortError") setError(err.message); });
    return () => controller.abort();
  }, [module.id, challenge]);

  function updateSettings(name, value) { setSettings((previous) => ({ ...previous, [name]: value })); setAssessment(null); setResult(null); }

  function updateExplorer(name, value) { setExplorer((previous) => ({ ...previous, [name]: value })); setResult(null); }

  async function explore() {
    setBusy(true); setError("");
    try {
      if (module.kind === "signals") setResult(await api("/tools/decode", { data: hexBytes(data), settings }));
      if (module.kind === "e2e") {
        if (!/^\s*\d+(\s*,\s*\d+)*\s*$/.test(counters)) throw new Error("Enter decimal counters separated by commas.");
        const frames = counters.split(",").map((counter, index) => ({ counter: Number(counter), corrupt: index === Number(corruptIndex) }));
        setResult(await api("/tools/e2e", { frames, max_lost: Number(maxLost) }));
      }
      if (module.kind === "verdict") {
        const results = await Promise.all(scenario.cases.map((entry) => api("/tools/verdict", { ...entry, deadline_ms: Number(deadline) })));
        setResult(results);
      }
      if (module.kind === "adas") setResult(await api("/tools/adas", explorer));
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function check() {
    setBusy(true); setError("");
    try {
      const count = module.kind === "e2e" ? scenario.frames.length : scenario?.cases.length || 0;
      const payload = module.kind === "signals" ? { settings } : { predictions: Array.from({ length: count }, (_, index) => predictions[index] || ""), strategy, deadline_ms: Number(deadline) };
      const outcome = await api(`/modules/${module.id}/check`, { challenge, payload });
      setAssessment(outcome); if (outcome.passed) onUpdate();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  const options = module.kind === "e2e" ? E2E_STATUSES : module.kind === "verdict" ? VERDICTS : ADAS_STATES;
  const prefix = `${challenge ? "challenge" : "practice"}-${module.id}`;
  const cases = module.kind === "e2e" ? scenario?.frames : scenario?.cases;
  return <article className="tool-lab">
    <div className="panel-title"><h2>{challenge ? "Independent challenge" : "Interactive test bench"}</h2><span className="chip">{module.kind.toUpperCase()} LAB</span></div>
    <p><strong>{challenge ? "Challenge" : "Exercise"}:</strong> {challenge ? module.challenge : module.task}</p>
    {module.kind === "signals" && <>
      <div className="control-grid">
        <label>Payload (hex)<input value={data} onChange={(event) => { setData(event.target.value); setResult(null); }} /></label>
        <label>Start byte<input type="number" min="0" max="7" value={settings.start_byte} onChange={(event) => updateSettings("start_byte", Number(event.target.value))} /></label>
        <label>Signal length (bytes)<input type="number" min="1" max="4" value={settings.length} onChange={(event) => updateSettings("length", Number(event.target.value))} /></label>
        <label>Byte order<select value={settings.byte_order} onChange={(event) => updateSettings("byte_order", event.target.value)}><option value="little">Little-endian</option><option value="big">Big-endian</option></select></label>
        <label>Factor<input type="number" step="any" value={settings.factor} onChange={(event) => updateSettings("factor", Number(event.target.value))} /></label>
        <label>Offset<input type="number" step="any" value={settings.offset} onChange={(event) => updateSettings("offset", Number(event.target.value))} /></label>
      </div><p>Unsigned, byte-aligned decoder. It does not parse arbitrary DBC files.</p>
    </>}
    {module.kind === "e2e" && <fieldset><legend>Fault-injection explorer</legend><div className="control-grid">
      <label>Counter sequence<input value={counters} onChange={(event) => { setCounters(event.target.value); setResult(null); }} /></label>
      <label>Allowed lost frames<input type="number" min="0" max="3" value={maxLost} onChange={(event) => { setMaxLost(event.target.value); setResult(null); }} /></label>
      <label>Corrupt CRC at index (-1 = none)<input type="number" min="-1" value={corruptIndex} onChange={(event) => { setCorruptIndex(event.target.value); setResult(null); }} /></label>
    </div><p>Zero-based index. CRC input: Data ID 01 23, counter byte, data 10 27. Toy modulo-16 profile; not AUTOSAR E2E.</p></fieldset>}
    {module.kind === "verdict" && <div className="control-grid">
      <label>Checking strategy<select value={strategy} onChange={(event) => { setStrategy(event.target.value); setAssessment(null); }}><option value="immediate">Immediate state read</option><option value="delay">Fixed delay only</option><option value="event">Event-based bounded wait</option></select></label>
      <label>Deadline (ms)<input type="number" min="1" max="5000" value={deadline} onChange={(event) => { setDeadline(event.target.value); setAssessment(null); setResult(null); }} /></label>
    </div>}
    {module.kind === "adas" && <fieldset><legend>Offline scenario explorer</legend><div className="control-grid">
      <label>Mode<select value={explorer.mode} onChange={(event) => updateExplorer("mode", event.target.value)}><option>AEB</option><option>ACC</option></select></label>
      {[["distance_m", "Distance (m)"], ["ego_kmh", "Ego speed (km/h)"], ["target_kmh", "Target speed (km/h)"], ["threshold_s", "TTC threshold (s)"]].map(([name, label]) => <label key={name}>{label}<input type="number" min="0" step="any" value={explorer[name]} onChange={(event) => updateExplorer(name, Number(event.target.value))} /></label>)}
      {[["sensor_valid", "Sensors valid"], ["obstacle_in_path", "Obstacle on path"], ["brake_pressed", "Driver braking"], ["enabled", "System enabled"]].map(([name, label]) => <label className="check-option" key={name}><input type="checkbox" checked={explorer[name]} onChange={(event) => updateExplorer(name, event.target.checked)} />{label}</label>)}
    </div><p>Constant-velocity teaching model. No sensor fusion or real vehicle actuation.</p></fieldset>}
    <button onClick={explore} disabled={busy || (module.kind === "verdict" && !scenario)}>{module.kind === "signals" ? "Decode payload" : "Run explorer"}</button>
    {result && <div className="tool-result"><h3>Explorer evidence</h3>
      {module.kind === "signals" ? <p role="status">Raw {result.raw} → {result.physical} {result.unit}</p> : module.kind === "e2e" ? <div className="trace-table-wrapper"><table><thead><tr><th>Counter</th><th>CRC received/expected</th><th>Delta</th><th>Status</th><th>Accepted baseline</th></tr></thead><tbody>{result.rows.map((row, index) => <tr key={index}><td>{row.counter}</td><td>{row.received_crc}/{row.expected_crc}</td><td>{row.delta ?? "—"}</td><td>{row.status}</td><td>{row.accepted_counter ?? "—"}</td></tr>)}</tbody></table></div> : <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>}
    {module.id >= 9 && <>
      <h3>Predict before checking</h3><p>Explorer settings do not change these fixed cases, and results do not fill in your answers. Classify each fixed assessment case below.</p>
      {!cases ? <p>Loading assessment cases...</p> : cases.map((entry, index) => <div className="prediction" key={index}><label htmlFor={`${prefix}-${index}`}>Case {index + 1}{module.kind === "e2e" ? ` · counter ${entry.counter} · CRC ${entry.corrupt ? "corrupt" : "valid"}` : entry.label ? ` · ${entry.label}` : ""}</label>
        {module.kind !== "e2e" && <pre>{JSON.stringify(entry, null, 2)}</pre>}
        <select id={`${prefix}-${index}`} value={predictions[index] || ""} onChange={(event) => { setPredictions((previous) => ({ ...previous, [index]: event.target.value })); setAssessment(null); }}><option value="">Choose classification</option>{options.map((option) => <option key={option}>{option}</option>)}</select>
      </div>)}
      {module.kind === "e2e" && <p>Assessment maxLost: {scenario?.max_lost}. Explorer settings do not change this requirement.</p>}
    </>}
    {error && <p role="alert">{error}</p>}
    <button onClick={check} disabled={busy || (module.id >= 9 && !cases)}>{challenge ? "Check challenge" : "Check exercise"}</button>
    {assessment && <div className="assessment"><p role="status" className={assessment.passed ? "success" : "warning"}>{assessment.message}</p><ul>{assessment.checks.map((item, index) => <li key={index}><strong>{item.passed ? "PASS" : "FAIL"}</strong> · {item.name}{!item.passed && <pre>{JSON.stringify({ observed: item.actual, expected: item.expected }, null, 2)}</pre>}</li>)}</ul></div>}
  </article>;
}
