import { useEffect, useState } from "react";
import { api } from "./api";

const canoeWindows = [
  ["Trace Window", "Mesaje CAN, ID-uri, payload, timestamp-uri, erori"],
  ["Graphics Window", "Evoluția semnalelor în timp"],
  ["Write Window", "Loguri și mesaje CAPL"],
  ["Simulation Setup", "Configurarea nodurilor simulate"],
  ["Measurement Setup", "Fluxul de procesare a datelor"],
  ["Test Modules", "Execuția testelor automate și raportarea verdictelor"],
];

const caplTimeout = `variables {
  msTimer t;
}

on start {
  setTimer(t, 500);
}

on message 0x300 {
  setTimer(t, 500);
}

on timer t {
  write("Communication timeout");
}`;

const caplTransmit = `variables {
  message 0x123 VehicleSpeed;
}

on start {
  VehicleSpeed.dlc = 2;
  VehicleSpeed.byte(0) = 0x10;
  VehicleSpeed.byte(1) = 0x27;
  output(VehicleSpeed);  // transmite mesajul
  write("Sent");        // doar log
}`;

function TheoryTable({ headings, rows }) {
  return (
    <div className="theory-table-wrap">
      <table className="theory-table">
        <thead>
          <tr>
            {headings.map((heading) => (
              <th key={heading}>{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([term, meaning]) => (
            <tr key={term}>
              <td>
                <strong>{term}</strong>
              </td>
              <td>{meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RomanianTheoryReference() {
  return (
    <section className="theory-panel" lang="ro">
      <style>{`
        .theory-panel { line-height: 1.65; }
        .theory-panel h2 { margin: 0 0 0.4rem; }
        .theory-panel h3 { margin: 1.8rem 0 0.6rem; }
        .theory-panel h4 { margin: 1rem 0 0.35rem; }
        .theory-panel p { margin: 0.65rem 0; }
        .theory-panel ul, .theory-panel ol { padding-left: 1.5rem; }
        .theory-panel li { margin: 0.35rem 0; }
        .theory-panel pre { max-width: 100%; overflow-x: auto; padding: 0.9rem 1rem;
          background: #172033; color: #eef4ff; border-radius: 9px; line-height: 1.5; font-size: 0.86rem; }
        .theory-panel code { font-size: 0.92em; }
        .theory-table-wrap { width: 100%; overflow-x: auto; }
        .theory-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.94rem; }
        .theory-table th, .theory-table td { padding: 0.55rem 0.7rem; border-bottom: 1px solid #b8c2d355; vertical-align: top; }
        .theory-table th { background: #8fa2bc22; }
        .theory-panel .theory-note { border-left: 3px solid #6487bb; padding: 0.45rem 0.8rem; background: #829fc412; }
        .theory-panel .theory-divider { margin: 1.7rem 0; border: 0; border-top: 1px solid #8fa2bc66; }
      `}</style>

      <h2>Theory</h2>

      <h3>1. CAN — Controller Area Network</h3>
      <p>
        CAN este un protocol de comunicație între ECU-uri. Identificatorul CAN
        nu este o adresă de destinație.
      </p>
      <ul>
        <li>
          <strong>CAN ID:</strong> identifică mesajul și participă la arbitraj;
          între cadre de același format, ID-ul numeric mai mic are prioritate
          mai mare.
        </li>
        <li>
          <strong>DLC:</strong> indică lungimea datelor pentru Classical CAN; la
          CAN FD codifică lungimea conform mapării DLC.
        </li>
        <li>
          <strong>Payload:</strong> octeții care transportă semnalele.
        </li>
        <li>
          <strong>DBC:</strong> descrie ID-urile, semnalele, pozițiile biților,
          lungimile, signedness, byte order, factor și offset.
        </li>
        <li>
          <strong>Classical CAN:</strong> maximum 8 octeți de date; un cadru
          standard are ID de 11 biți (0x000–0x7FF).
        </li>
        <li>
          <strong>CAN FD:</strong> maximum 64 octeți de date.
        </li>
        <li>
          <strong>ACK:</strong> confirmare la nivel de cadru CAN, nu acceptare
          de către logica aplicației.
        </li>
        <li>
          <strong>Bus-off:</strong> un nod încetează transmiterea pe bus după
          acumularea excesivă de erori.
        </li>
      </ul>
      <h4>Decodarea semnalelor</h4>
      <pre>{"Valoare fizică = Raw × Factor + Offset"}</pre>
      <p>
        Exemplu: Raw = 100, Factor = 0,5, Offset = −10 →{" "}
        <strong>40 km/h</strong>.
      </p>
      <p>
        Pentru un semnal{" "}
        <strong>unsigned, 16 biți, little-endian, factor 0,01, offset 0</strong>
        :
      </p>
      <pre>
        {"10 27 → 0x2710 → 10000 → 100 km/h\n88 13 → 0x1388 →  5000 →  50 km/h"}
      </pre>
      <p>
        Aceste valori reprezintă definiția semnalului nostru de exemplu, nu o
        regulă universală CAN.
      </p>

      <h3>2. CANoe — instrument Vector</h3>
      <p>
        CANoe permite simularea, analiza, monitorizarea și testarea automată a
        comunicației și ECU-urilor.
      </p>
      <TheoryTable headings={["Componentă", "Rol"]} rows={canoeWindows} />
      <p>
        <strong>La debugging:</strong> verific ID-ul, canalul CAN, DLC-ul,
        DBC-ul, valorile semnalelor, timestamp-urile și eventualele erori. Un
        mesaj vizibil în Trace nu garantează că ECU l-a acceptat la nivel de
        aplicație.
      </p>

      <hr className="theory-divider" />

      <h3>3. CAPL — Communication Access Programming Language</h3>
      <p>Limbaj asemănător cu C, bazat pe evenimente, utilizat în CANoe.</p>
      <ul>
        <li>
          <code>on start</code> — la pornirea măsurării.
        </li>
        <li>
          <code>on message</code> — la recepția unui mesaj.
        </li>
        <li>
          <code>on timer</code> — când expiră un timer.
        </li>
        <li>
          <code>setTimer()</code> — pornește sau reprogramează timerul.
        </li>
        <li>
          <code>cancelTimer()</code> — anulează timerul.
        </li>
        <li>
          <code>output(msg)</code> — transmite mesajul.
        </li>
        <li>
          <code>write()</code> — afișează text în Write Window.
        </li>
      </ul>
      <h4>Transmitere CAN versus logare</h4>
      <pre>{caplTransmit}</pre>
      <p>
        Setarea DLC-ului și a octeților modifică obiectul mesaj, dar{" "}
        <strong>nu îl transmite</strong>. Transmiterea se produce la{" "}
        <code>output()</code>. Simulatorul educațional poate captura un snapshot
        al mesajului la fiecare apel <code>output()</code>.
      </p>
      <h4>Exemplu: detectarea pierderii comunicației</h4>
      <pre>{caplTimeout}</pre>
      <p>
        Fiecare mesaj cu ID-ul <code>0x300</code> reprogramează timerul la 500
        ms. Dacă nu mai vine mesajul în acest interval, se afișează timeout.
      </p>
      <p className="theory-note">
        <strong>Atenție:</strong> timerul CAPL este one-shot, deci nu se repetă
        automat.
      </p>

      <h3>4. Test Modules și verdict</h3>
      <p>
        <strong>Structura testului:</strong> Precondiții → Stimul → Așteptare
        răspuns → Verificare → PASS/FAIL.
      </p>
      <ul>
        <li>
          <code>testcase</code> — definește un caz de test.
        </li>
        <li>
          <code>testStepPass()</code> — raportează un pas reușit.
        </li>
        <li>
          <code>testStepFail()</code> — raportează un pas eșuat.
        </li>
        <li>
          <code>testWaitForTimeout()</code> — așteptare temporizată.
        </li>
        <li>
          <code>testWaitForMessage()</code> — așteaptă un mesaj în contextul
          funcțiilor de test CANoe.
        </li>
      </ul>
      <p>
        <strong>Important:</strong> <code>write("PASS")</code> nu setează
        verdictul. Un test robust verifică atât valoarea, cât și precondițiile
        și timpul de răspuns.
      </p>

      <h3>5. E2E — End-to-End Protection</h3>
      <p>
        E2E protejează datele aplicației împotriva unor erori de comunicație.
        CRC-ul cadrului CAN și CRC-ul E2E la nivel de aplicație sunt mecanisme
        diferite.
      </p>
      <ul>
        <li>
          <strong>CRC:</strong> Cyclic Redundancy Check — verifică integritatea
          datelor.
        </li>
        <li>
          <strong>Alive counter:</strong> contor care avansează conform
          specificației.
        </li>
        <li>
          <strong>Data ID:</strong> identificator ce poate participa la calculul
          CRC E2E.
        </li>
        <li>
          <strong>Timeout:</strong> detectează absența mesajelor.
        </li>
        <li>
          <strong>Freshness / sequence:</strong> verifică prospețimea și
          succesiunea datelor.
        </li>
      </ul>
      <p>
        Exemplu contor pe 4 biți: <code>13 → 14 → 15 → 0 → 1</code> este valid
        la incrementare modulo 16. Secvența <code>5 → 6 → 7 → 7 → 8</code>{" "}
        conține un duplicat și este invalidă{" "}
        <em>dacă specificația interzice duplicatele</em>.
      </p>
      <p className="theory-note">
        <strong>CRC corect ≠ E2E valid.</strong> Counterul, freshness-ul sau
        secvența pot încălca cerința. Toleranța la mesaje pierdute și
        comportamentul la wraparound depind de profil și de specificație.
      </p>

      <h3>6. Testare ACC / AEB</h3>
      <h4>ACC — ce testez?</h4>
      <ul>
        <li>Activare, dezactivare și precondiții.</li>
        <li>Menținerea vitezei și distanței față de vehiculul din față.</li>
        <li>Reacția la frânarea vehiculului din față.</li>
        <li>Dezactivarea la apăsarea frânei, conform cerinței.</li>
        <li>Timpul de reacție, accelerația și confortul.</li>
      </ul>
      <h4>AEB — ce testez?</h4>
      <ul>
        <li>Detectarea obstacolelor valide pe traiectorie.</li>
        <li>Pragul TTC definit de cerințe.</li>
        <li>Momentul corect al cererii de frânare.</li>
        <li>
          Absența frânărilor nejustificate (<em>false positives</em>).
        </li>
        <li>
          Detectarea lipsei unei intervenții necesare (<em>false negatives</em>
          ).
        </li>
      </ul>

      <h3>7. Debugging tips</h3>
      <ol>
        <li>
          <strong>Precondiții:</strong> ECU este READY? Starea inițială e
          corectă?
        </li>
        <li>
          <strong>Stimul:</strong> comanda CAN a fost transmisă corect?
        </li>
        <li>
          <strong>Comunicație:</strong> ID, DBC, DLC, CRC, counter, bus-off.
        </li>
        <li>
          <strong>Timing:</strong> timestamp, timeout, periodicitate, jitter.
        </li>
        <li>
          <strong>Rezultat:</strong> semnalul și comportamentul respectă
          cerința?
        </li>
      </ol>
      <p>
        <strong>Exemplu ACC:</strong> dacă activarea este cerută în maximum 100
        ms, testul așteaptă starea activă până la deadline. O verificare
        imediată poate produce FAIL fals; o așteptare fixă fără verificare nu
        dovedește succesul.
      </p>

      <h3>5 idei de reținut</h3>
      <ol>
        <li>
          CANoe = simulare, analiză și testare; CAPL = automatizare bazată pe
          evenimente.
        </li>
        <li>
          Prezența mesajului în Trace nu garantează acceptarea lui de către ECU.
        </li>
        <li>CRC valid ≠ counter valid ≠ E2E valid.</li>
        <li>
          PASS presupune respectarea cerinței, inclusiv a timpului de reacție.
        </li>
        <li>
          La orice defect: precondiții → stimul → comunicație → timing →
          verdict.
        </li>
      </ol>
    </section>
  );
}

export default function LearningPanel({
  module,
  mode,
  progress,
  courseProgress,
  onUpdate,
}) {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (mode !== "quiz" || loaded) return;
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
    if (mode !== "progress") return;
    const controller = new AbortController();
    api(`/modules/${module.id}/quiz-history`, undefined, controller.signal)
      .then(setHistory)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => controller.abort();
  }, [mode, module.id]);

  async function newQuiz(revision = false) {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setQuiz(await api(`/modules/${module.id}/quiz?revision=${revision}`));
      setAnswers({});
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
      const graded = await api(`/modules/${module.id}/quiz`, {
        session_id: quiz.session_id,
        submission_id: crypto.randomUUID(),
        answers,
      });
      setResult(graded);
      onUpdate();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function reviewed() {
    setBusy(true);
    setError("");
    try {
      await api(`/modules/${module.id}/theory-reviewed`, {});
      onUpdate();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (["practice", "challenges"].includes(mode)) return null;
  if (mode === "theory")
    return (
      <section className="learning-panel">
        <RomanianTheoryReference />
        <h3>Reference reading</h3>
        <ul>
          {module.sources.map((source) => (
            <li key={source.url}>
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.label}
              </a>
            </li>
          ))}
        </ul>
        {error && <p role="alert">{error}</p>}
        <button onClick={reviewed} disabled={busy || progress.theory_reviewed}>
          {progress.theory_reviewed
            ? "Theory reviewed"
            : "Mark theory reviewed"}
        </button>
        <p className="muted">
          Reviewed means you marked it read. Quiz results and practical evidence
          are tracked separately.
        </p>
      </section>
    );

  if (mode === "progress")
    return (
      <section className="learning-panel">
        <h2>Learning record</h2>
        <div className="milestone-grid">
          <div>
            <small>Theory</small>
            <strong>
              {progress.theory_reviewed ? "Reviewed" : "Not reviewed"}
            </strong>
          </div>
          <div>
            <small>Practical</small>
            <strong>
              {progress.practical_completed ? "Completed" : "Not completed"}
            </strong>
          </div>
          <div>
            <small>Challenge</small>
            <strong>
              {progress.challenge_completed ? "Completed" : "Not completed"}
            </strong>
          </div>
          <div>
            <small>Best quiz</small>
            <strong>
              {progress.best_percent == null
                ? "No attempts"
                : `${progress.best_percent}%`}
            </strong>
          </div>
        </div>
        <p>{progress.quiz_attempts || 0} saved quiz attempts</p>
        <p>
          Revision topics:{" "}
          {progress.missed_topics?.join(", ") ||
            "No outstanding missed topics recorded."}
        </p>
        {error && <p role="alert">{error}</p>}
        <h3>Achievements</h3>
        <ul>
          <li>
            {courseProgress[4]?.practical_completed ? "Earned" : "Not yet"} ·
            CAN transmitter — complete the speed transmission practical.
          </li>
          <li>
            {courseProgress[6]?.practical_completed &&
            courseProgress[7]?.challenge_completed
              ? "Earned"
              : "Not yet"}{" "}
            · Timing detective — complete periodic traffic and the watchdog
            challenge.
          </li>
          <li>
            {courseProgress[9]?.practical_completed &&
            courseProgress[9]?.best_percent >= 75
              ? "Earned"
              : "Not yet"}{" "}
            · E2E analyst — complete the E2E practical and score at least 75% on
            its quiz.
          </li>
          <li>
            {courseProgress[10]?.challenge_completed &&
            courseProgress[11]?.practical_completed
              ? "Earned"
              : "Not yet"}{" "}
            · ADAS investigator — complete the deadline challenge and ADAS
            practical.
          </li>
        </ul>
        <h3>Recent attempts</h3>
        {!history.length ? (
          <p>No attempts yet.</p>
        ) : (
          <ol>
            {history.map((attempt) => (
              <li key={attempt.id}>
                {attempt.score}/{attempt.total} ·{" "}
                {new Date(attempt.created_at).toLocaleString()} ·{" "}
                {attempt.missed_topics.join(", ") || "All correct"}
              </li>
            ))}
          </ol>
        )}
        <p className="muted">
          Records belong to one local learner. There is no account isolation
          yet.
        </p>
      </section>
    );

  return (
    <section className="learning-panel" aria-label="Module quiz">
      <h2>Knowledge check</h2>
      <p>
        Answer every question. Grading and attempt history are saved by the
        backend.
      </p>
      <div className="toolbar">
        <button onClick={() => newQuiz(false)} disabled={busy}>
          New quiz
        </button>
        <button onClick={() => newQuiz(true)} disabled={busy}>
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
        <form onSubmit={grade}>
          {quiz.questions.map((question, index) => {
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
              busy ||
              Object.keys(answers).length !== quiz.questions.length
            }
          >
            {busy ? "Saving..." : "Grade quiz"}
          </button>
          <button
            type="button"
            onClick={() => {
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
        New quizzes vary question order and bank selection. Revision prioritizes
        previously missed questions; questions may recur.
      </p>
    </section>
  );
}
