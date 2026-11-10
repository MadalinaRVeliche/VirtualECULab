import { useEffect, useState } from "react";
import "./App.css";
import CanTrace from "./CanTrace";
import LearningPanel from "./LearningPanel";

const API_URL = "http://127.0.0.1:8000";

function LessonEditor({ lesson, onComplete, onTransmit }) {
  const [code, setCode] = useState(lesson.code);
  const [output, setOutput] = useState([]);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState(null);

  async function submitCode(checkExercise, event = "start", key = null) {
    setRunning(true);
    setOutput([]);
    setError("");
    setFeedback(null);

    const endpoint = checkExercise
      ? `/lessons/${lesson.id}/check`
      : "/simulate";

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(checkExercise ? { code } : { code, event, key }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string" ? data.detail : "The request failed.",
        );
      }

      setOutput(data.output);
      if (!checkExercise && data.frames?.length) {
        onTransmit(data.frames);
      }

      if (checkExercise) {
        setFeedback({
          passed: data.passed,
          message: data.message,
        });

        if (data.passed) {
          onComplete(lesson.id);
        }
      }
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Cannot reach the simulator. Make sure the backend is running."
          : err.message || "Something went wrong.",
      );
    } finally {
      setRunning(false);
    }
  }

  function resetCode() {
    setCode(lesson.code);
    setOutput([]);
    setError("");
    setFeedback(null);
  }

  return (
    <article>
      <h2>{lesson.title}</h2>
      <p>{lesson.description}</p>

      <p>
        <strong>Exercise:</strong> {lesson.task}
      </p>

      <label htmlFor={`code-${lesson.id}`}>CAPL code</label>

      {lesson.id === 3 && (
        <p>
          Run triggers simulation startup. Press A sends the lowercase key{" "}
          <code>a</code> to the simulator.
        </p>
      )}

      <textarea
        id={`code-${lesson.id}`}
        value={code}
        onChange={(event) => {
          setCode(event.target.value);
          setFeedback(null);
          setOutput([]);
          setError("");
        }}
        rows={8}
        spellCheck={false}
        disabled={running}
        style={{
          display: "block",
          width: "100%",
          boxSizing: "border-box",
          fontFamily: "monospace",
          margin: "12px 0",
        }}
      />

      <button onClick={() => submitCode(false)} disabled={running}>
        {running ? "Processing..." : "Run"}
      </button>

      {lesson.id === 3 && (
        <button
          onClick={() => submitCode(false, "key", "a")}
          disabled={running}
        >
          Press A
        </button>
      )}

      <button onClick={() => submitCode(true)} disabled={running}>
        Check exercise
      </button>

      <button onClick={resetCode} disabled={running}>
        Reset code
      </button>

      {feedback && (
        <p
          role="status"
          style={{ color: feedback.passed ? "#a7f3d0" : "#fcd34d" }}
        >
          {feedback.message}
        </p>
      )}

      <h3>Console</h3>

      <div aria-live="polite">
        {error && <p role="alert">{error}</p>}

        {output.length > 0 ? (
          <pre>{output.join("\n")}</pre>
        ) : (
          !error && <p>{running ? "Processing..." : "No output to display."}</p>
        )}
      </div>
    </article>
  );
}

function App() {
  const [lessons, setLessons] = useState([]);
  const [completedLessonIds, setCompletedLessonIds] = useState([]);
  const [selectedLessonId, setSelectedLessonId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [progressError, setProgressError] = useState("");
  const [frames, setFrames] = useState([]);
  const [activeTab, setActiveTab] = useState("practice");

  useEffect(() => {
    let active = true;

    async function loadLessons() {
      try {
        const response = await fetch(`${API_URL}/lessons`);

        if (!response.ok) {
          throw new Error("Failed to load lessons.");
        }

        const data = await response.json();

        if (active) {
          setLessons(data);
          setSelectedLessonId(data[0]?.id ?? null);
        }
      } catch {
        if (active) {
          setError("Cannot load lessons. Make sure the backend is running.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    async function loadProgress() {
      try {
        const response = await fetch(`${API_URL}/progress`);

        if (!response.ok) {
          throw new Error("Failed to load progress.");
        }

        const data = await response.json();

        if (active) {
          setCompletedLessonIds((current) => [
            ...new Set([...current, ...data.completed_lesson_ids]),
          ]);
        }
      } catch {
        if (active) {
          setProgressError(
            "Saved progress could not be loaded. Refresh to try again.",
          );
        }
      }
    }

    loadLessons();
    loadProgress();

    return () => {
      active = false;
    };
  }, []);

  function recordFrames(newFrames, source) {
    const rows = newFrames.map((frame) => ({
      ...frame,
      rowId: crypto.randomUUID(),
      source,
    }));

    setFrames((current) => [...current, ...rows]);
  }

  function markCompleted(lessonId) {
    setCompletedLessonIds((current) =>
      current.includes(lessonId) ? current : [...current, lessonId],
    );
  }

  const selectedLesson = lessons.find(
    (lesson) => lesson.id === selectedLessonId,
  );

  return (
    <main>
      <h1>Virtual ECU Lab</h1>
      <p>Learn CAPL step by step.</p>

      <nav className="learning-navigation" aria-label="Learning sections">
        {["theory", "practice", "quiz"].map((tab) => (
          <button
            key={tab}
            className={activeTab === tab ? "selected" : ""}
            aria-pressed={activeTab === tab}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      <LearningPanel mode={activeTab} />

      <section hidden={activeTab !== "practice"}>
        {loading && <p>Loading lessons...</p>}
        {error && <p role="alert">{error}</p>}
        {progressError && <p role="alert">{progressError}</p>}

        {!loading && !error && lessons.length > 0 && (
          <nav className="lesson-navigation" aria-label="Lessons">
            {lessons.map((lesson) => (
              <button
                key={lesson.id}
                className={lesson.id === selectedLessonId ? "selected" : ""}
                aria-pressed={lesson.id === selectedLessonId}
                onClick={() => setSelectedLessonId(lesson.id)}
              >
                {lesson.id}. {lesson.title}
                {completedLessonIds.includes(lesson.id) && (
                  <span className="completion-badge"> Completed</span>
                )}
              </button>
            ))}
          </nav>
        )}

        {selectedLesson && (
          <LessonEditor
            key={selectedLesson.id}
            lesson={selectedLesson}
            onComplete={markCompleted}
            onTransmit={(newFrames) => recordFrames(newFrames, "CAPL Tx")}
          />
        )}

        <CanTrace
          frames={frames}
          onInspectFrame={(frame) => recordFrames([frame], "Preview")}
          onClear={() => setFrames([])}
        />
      </section>
    </main>
  );
}

export default App;
