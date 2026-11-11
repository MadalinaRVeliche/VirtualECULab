import { useState } from "react";
import { API_URL } from "./api";

export default function LessonEditor({ lesson, onComplete, onTransmit }) {
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

