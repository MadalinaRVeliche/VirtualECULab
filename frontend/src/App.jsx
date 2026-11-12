import { useEffect, useState } from "react";
import { api } from "./api";
import LearningPanel from "./LearningPanel";
import Workbench from "./Workbench";
import "./App.css";

const sections = ["Theory", "Quiz", "Workbench"];

export default function App() {
  const [active, setActive] = useState("Theory");
  const [modules, setModules] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    // Load the course metadata when the app mounts. Abort the request
    // during cleanup if the component goes away before the response arrives.
    const controller = new AbortController();
    api("/modules", undefined, controller.signal)
      .then(setModules)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => controller.abort();
  }, []);

  // The backend uses module 0 for the course overview and shared quiz bank.
  // LearningPanel uses this module ID when requesting quizzes and history.
  const overview = modules.find((module) => module.id === 0);

  return (
    <main>
      <header className="workspace-header">
        <h1>Virtual ECU Lab</h1>
        <span className="workspace-topics">CAN · CANoe · CAPL · ADAS</span>
      </header>
      <nav className="learning-navigation" aria-label="Learning sections">
        {sections.map((section) => (
          <button
            key={section}
            className={active === section ? "selected" : ""}
            aria-pressed={active === section}
            onClick={() => setActive(section)}
          >
            {section}
          </button>
        ))}
      </nav>

      {/* Course metadata errors belong to Theory and Quiz. Workbench loads independently. */}
      {active !== "Workbench" && error && <p role="alert">{error}</p>}
      {active !== "Workbench" && !overview && !error && <p>Loading course…</p>}
      {overview && <LearningPanel module={overview} mode={active} />}

      {/* Keep Workbench mounted so switching tabs preserves the CAPL draft and trace. */}
      <section hidden={active !== "Workbench"} aria-label="CAN workbench">
        <Workbench />
      </section>
    </main>
  );
}
