import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function LessonEditor({ lesson }) {
  const [code, setCode] = useState(lesson.code);
  const [output, setOutput] = useState([]);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState(null);

  async function submitCode(checkExercise) {
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
        body: JSON.stringify({ code }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string" ? data.detail : "The request failed.",
        );
      }

      setOutput(data.output);

      if (checkExercise) {
        setFeedback({
          passed: data.passed,
          message: data.message,
        });
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
  const [selectedLessonId, setSelectedLessonId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadLessons() {
      try {
        const response = await fetch(`${API_URL}/lessons`);

        if (!response.ok) {
          throw new Error("Failed to load lessons.");
        }

        const data = await response.json();
        setLessons(data);
        setSelectedLessonId(data[0]?.id ?? null);
      } catch {
        setError("Cannot load lessons. Make sure the backend is running.");
      } finally {
        setLoading(false);
      }
    }

    loadLessons();
  }, []);

  const selectedLesson = lessons.find(
    (lesson) => lesson.id === selectedLessonId,
  );

  return (
    <main>
      <h1>Virtual ECU Lab</h1>
      <p>Learn CAPL step by step.</p>

      {loading && <p>Loading lessons...</p>}
      {error && <p role="alert">{error}</p>}

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
            </button>
          ))}
        </nav>
      )}

      {selectedLesson && (
        <LessonEditor key={selectedLesson.id} lesson={selectedLesson} />
      )}
    </main>
  );
}

export default App;
