import "./App.css";
import { useEffect, useState } from "react";

function LessonEditor({ lesson }) {
  const [code, setCode] = useState(lesson.code);
  const [output, setOutput] = useState([]);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  async function runCode() {
    setRunning(true);
    setOutput([]);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Simularea a eșuat."
        );
      }

      setOutput(data.output);
    } catch (err) {
      setError(err.message || "Nu am putut contacta simulatorul.");
    } finally {
      setRunning(false);
    }
  }

  function resetCode() {
    setCode(lesson.code);
    setOutput([]);
    setError("");
  }

  return (
    <article>
      <h2>{lesson.title}</h2>
      <p>{lesson.description}</p>

      <label htmlFor={`code-${lesson.id}`}>Cod CAPL</label>

      <textarea
        id={`code-${lesson.id}`}
        value={code}
        onChange={(event) => setCode(event.target.value)}
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

      <button onClick={runCode} disabled={running}>
        {running ? "Se rulează..." : "Rulează"}
      </button>

      <button onClick={resetCode} disabled={running}>
        Resetează codul
      </button>

      <h3>Consolă</h3>

      <div aria-live="polite">
        {error && <p role="alert">{error}</p>}

        {output.length > 0 ? (
          <pre>{output.join("\n")}</pre>
        ) : (
          !error && <p>Niciun rezultat încă.</p>
        )}
      </div>
    </article>
  );
}

function App() {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadLessons() {
      try {
        const response = await fetch("http://127.0.0.1:8000/lessons");

        if (!response.ok) {
          throw new Error("Nu am putut încărca lecțiile.");
        }

        const data = await response.json();
        setLessons(data);
      } catch {
        setError("Nu am putut încărca lecțiile. Verifică backendul.");
      } finally {
        setLoading(false);
      }
    }

    loadLessons();
  }, []);

  return (
    <main>
      <h1>Virtual ECU Lab</h1>
      <p>Învață CAPL pas cu pas.</p>

      {loading && <p>Se încarcă lecțiile...</p>}
      {error && <p role="alert">{error}</p>}

      {lessons.map((lesson) => (
        <LessonEditor key={lesson.id} lesson={lesson} />
      ))}
    </main>
  );
}

export default App;