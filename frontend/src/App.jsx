import { useEffect, useState } from "react";
import "./App.css";
import { api } from "./api";
import CanTrace from "./CanTrace";
import LessonEditor from "./LessonEditor";
import LearningPanel from "./LearningPanel";
import LabEditor from "./LabEditor";
import ToolLab from "./ToolLab";

const sections = ["theory", "practice", "quiz", "challenges", "progress"];

export default function App() {
  const [modules, setModules] = useState([]);
  const [selectedId, setSelectedId] = useState(1);
  const [activeTab, setActiveTab] = useState("practice");
  const [progress, setProgress] = useState({});
  const [frames, setFrames] = useState([]);
  const [error, setError] = useState("");
  const [progressError, setProgressError] = useState("");

  async function refreshProgress() {
    try {
      setProgress(await api("/learning/progress"));
      setProgressError("");
    } catch (err) {
      setProgressError(`Saved progress unavailable: ${err.message}`);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    api("/modules", undefined, controller.signal).then(setModules).catch((err) => {
      if (err.name !== "AbortError") setError(err.message);
    });
    api("/learning/progress", undefined, controller.signal).then(setProgress).catch((err) => {
      if (err.name !== "AbortError") setProgressError(`Saved progress unavailable: ${err.message}`);
    });
    return () => controller.abort();
  }, []);

  function recordFrames(newFrames, source) {
    setFrames((current) => [...current, ...newFrames.map((frame) => ({
      ...frame, rowId: crypto.randomUUID(), source,
    }))]);
  }

  function replaceLabFrames(newFrames) {
    setFrames((current) => [
      ...current.filter((frame) => !frame.lab),
      ...newFrames.map((frame) => ({ ...frame, rowId: crypto.randomUUID(), lab: true, source: `Lab ${frame.direction}` })),
    ]);
  }

  const module = modules.find((entry) => entry.id === selectedId);
  const current = progress[selectedId] || {};
  const completed = modules.filter((entry) => progress[entry.id]?.practical_completed).length;

  function complete(id) {
    setProgress((previous) => ({ ...previous, [id]: { ...previous[id], practical_completed: true } }));
    refreshProgress();
  }

  return (
    <div className="app-shell">
      <aside className="course-sidebar">
        <div className="brand"><span className="brand-symbol">VL</span><div>VIRTUAL ECU LAB<small>Automotive learning workspace</small></div></div>
        <p className="eyebrow">LEARNING PATH</p>
        <nav className="module-list" aria-label="Lessons">
          {modules.map((entry) => (
            <button key={entry.id} className={entry.id === selectedId ? "selected" : ""}
              aria-pressed={entry.id === selectedId} onClick={() => { setSelectedId(entry.id); }}>
              <span className="module-number">{String(entry.id).padStart(2, "0")}</span>
              <span><span className="module-title">{entry.id}. {entry.title}</span><small>{entry.level}</small>
                {progress[entry.id]?.practical_completed && <span className="completion-badge">Completed</span>}
              </span>
            </button>
          ))}
        </nav>
        <div className="sidebar-foot"><strong>{completed} / {modules.length || 11} practicals complete</strong>
          <progress value={completed} max={modules.length || 11} />
          <small>One local learner · PostgreSQL progress</small>
        </div>
      </aside>
      <main>
        <header className="workspace-header"><div><p className="eyebrow">CAN · CANoe · CAPL · ADAS</p><h1>Virtual ECU Lab</h1><p>Understand the requirement. Build the stimulus. Inspect the evidence.</p></div><span className="environment-pill">SIMULATED ENVIRONMENT</span></header>
        <p className="scope-note">Educational CAPL subset and offline models. No physical CAN bus, Vector runtime, or production ADAS controller.</p>
        {error && <p role="alert">{error}</p>}
        {progressError && <p role="alert">{progressError} <button onClick={refreshProgress}>Retry progress</button></p>}
        {!module && !error && <p>Loading lessons...</p>}
        {module && <>
          <div className="module-heading"><span className="eyebrow">MODULE {String(module.id).padStart(2, "0")} / {module.level.toUpperCase()}</span><h2>{module.title}</h2><p>{module.description}</p></div>
          <nav className="learning-navigation" aria-label="Learning sections">
            {sections.map((section) => <button key={section} className={activeTab === section ? "selected" : ""} aria-pressed={activeTab === section} onClick={() => setActiveTab(section)}>{section.charAt(0).toUpperCase() + section.slice(1)}</button>)}
          </nav>
          <LearningPanel key={module.id} module={module} mode={activeTab} progress={current} courseProgress={progress} onUpdate={refreshProgress} />
          <section hidden={activeTab !== "practice"} aria-label="Practice workspace">
            {module.id <= 3 ? <LessonEditor key={module.id} lesson={module} onComplete={complete} onTransmit={(newFrames) => recordFrames(newFrames, "CAPL Tx")} /> :
              module.kind === "capl" ? <LabEditor key={module.id} module={module} onUpdate={refreshProgress} onFrames={replaceLabFrames} /> :
                <ToolLab key={module.id} module={module} onUpdate={refreshProgress} />}
            <CanTrace frames={frames} onInspectFrame={(frame) => recordFrames([frame], "Preview")} onClear={() => setFrames([])} />
          </section>
          <section hidden={activeTab !== "challenges"} aria-label="Challenge workspace">
            <p className="scope-note">Independent challenge · different targets · graded by scenario evidence</p>
            {module.kind === "capl" ? <LabEditor key={`${module.id}-challenge`} module={module} challenge onUpdate={refreshProgress} onFrames={replaceLabFrames} /> : <ToolLab key={`${module.id}-challenge`} module={module} challenge onUpdate={refreshProgress} />}
            <CanTrace frames={frames} onInspectFrame={(frame) => recordFrames([frame], "Preview")} onClear={() => setFrames([])} />
          </section>
        </>}
      </main>
    </div>
  );
}
