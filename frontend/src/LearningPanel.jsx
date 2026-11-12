import { useEffect, useState } from "react";
import { api } from "./api";
import TheoryDetails from "./TheoryDetails";

export default function LearningPanel({ module, mode }) {
  const [quiz, setQuiz] = useState(null);

  // Store the selected option index by question ID. The server keeps
  // the answer key and returns the explanations after grading.
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    // Opening Quiz for the first time creates a session on the backend.
    // Keep that session and its answers when the user switches tabs.
    if (mode !== "Quiz" || loaded) return;

    const controller = new AbortController();
    api(`/modules/${module.id}/quiz`, undefined, controller.signal)
      .then((data) => {
        setQuiz(data);
        setLoaded(true);
        setError("");
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setBusy(false);
      });
    return () => controller.abort();
  }, [mode, loaded, module.id]);

  useEffect(() => {
    if (mode !== "Quiz") return;

    // Refresh saved attempts when Quiz opens or the displayed result changes.
    // A history request can fail while the current quiz is still usable.
    const controller = new AbortController();
    api(`/modules/${module.id}/quiz-history`, undefined, controller.signal)
      .then((entries) => {
        setHistory(entries);
        setHistoryError("");
      })
      .catch((err) => {
        if (err.name !== "AbortError") setHistoryError(err.message);
      });
    return () => controller.abort();
  }, [mode, module.id, result]);

  async function newQuiz(revision = false) {
    setBusy(true);
    setError("");
    try {
      const params = new URLSearchParams({ revision: String(revision) });

      // Tell the server which set is on screen so normal rotation can
      // exclude its questions even if another session was created later.
      if (quiz) params.set("previous_session", quiz.session_id);

      setQuiz(await api(`/modules/${module.id}/quiz?${params}`));

      // Clear answers and feedback only after the new set has arrived.
      // If the request fails, the user can still work on the current quiz.
      setAnswers({});
      setResult(null);
      setLoaded(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function grade(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      // The session identifies the exact question set to grade.
      // The submission ID identifies this individual attempt.
      const graded = await api(`/modules/${module.id}/quiz`, {
        session_id: quiz.session_id,
        submission_id: crypto.randomUUID(),
        answers,
      });
      setResult(graded);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (mode === "Theory") {
    return <TheoryDetails sources={module.sources} />;
  }

  if (mode !== "Quiz") return null;

  return (
    <section className="learning-panel" aria-label="Course quiz">
      <h2>Knowledge check</h2>
      <p>
        10 questions from the full course. Answer every question to see your
        score and explanations.
      </p>
      <div className="toolbar">
        <button onClick={() => newQuiz(false)} disabled={busy || !loaded}>
          New quiz
        </button>
        <button onClick={() => newQuiz(true)} disabled={busy || !loaded}>
          Revise missed topics
        </button>
      </div>
      {error && (
        <p role="alert">
          {error} <button onClick={() => newQuiz(false)}>Retry quiz</button>
        </p>
      )}
      {!quiz && !error && <p>Loading quiz...</p>}
      {quiz && (
        <form onSubmit={grade} aria-label="Quiz answers">
          {quiz.questions.map((question, index) => {
            // Match feedback by question ID so it stays tied to the
            // question regardless of where that question appears in the set.
            const feedback = result?.feedback.find(
              (entry) => entry.id === question.id,
            );
            return (
              <fieldset key={question.id}>
                <legend>
                  {index + 1}. {question.prompt}
                </legend>
                {question.options.map((option, optionIndex) => (
                  <label className="quiz-option" key={optionIndex}>
                    <input
                      type="radio"
                      name={`${module.id}-${question.id}`}
                      checked={answers[question.id] === optionIndex}
                      disabled={busy}
                      onChange={() => {
                        setAnswers((previous) => ({
                          ...previous,
                          [question.id]: optionIndex,
                        }));

                        // The score applies to the submitted answers.
                        // Hide it as soon as the selection changes.
                        setResult(null);
                      }}
                    />
                    <span>{option}</span>
                  </label>
                ))}
                {feedback && (
                  <p className={feedback.correct ? "success" : "warning"}>
                    <strong>
                      {feedback.correct ? "Correct. " : "Incorrect. "}
                    </strong>
                    Correct answer: {feedback.correct_answer}.{" "}
                    {feedback.explanation}
                  </p>
                )}
              </fieldset>
            );
          })}
          <button
            type="submit"
            disabled={
              busy || Object.keys(answers).length !== quiz.questions.length
            }
          >
            {busy ? "Saving..." : "Grade quiz"}
          </button>
          <button
            type="button"
            onClick={() => {
              // Reset the form while keeping the same quiz session.
              setAnswers({});
              setResult(null);
            }}
            disabled={busy}
          >
            Reset quiz
          </button>
        </form>
      )}
      {result && (
        <p role="status" className="score">
          Score: {result.score} / {result.total}
        </p>
      )}
      <p className="muted">
        New quiz changes all 10 questions from the current set. Revise missed
        topics brings back questions you missed.
      </p>
      <details className="quiz-history">
        <summary>Quiz history</summary>
        {historyError ? (
          <p role="alert">{historyError}</p>
        ) : !history.length ? (
          <p>No attempts yet.</p>
        ) : (
          <ol>
            {history.map((attempt) => (
              <li key={attempt.id}>
                {attempt.score}/{attempt.total} ·{" "}
                {new Date(attempt.created_at).toLocaleString()}
              </li>
            ))}
          </ol>
        )}
      </details>
    </section>
  );
}
