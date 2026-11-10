import { useState } from "react";

const questions = [
  {
    id: "transmission",
    question: "Which statement transmits a CAN message?",
    options: [
      'write("Message sent");',
      "output(VehicleSpeed);",
      "VehicleSpeed.dlc = 2;",
    ],
    correct: 1,
    explanation:
      "output() transmits. write() displays text. Setting DLC changes the message object but does not transmit it.",
  },
  {
    id: "decoding",
    question:
      "Decode bytes 88 13 as unsigned little-endian speed, with factor 0.01 and offset 0.",
    options: ["50 km/h", "100 km/h", "136.19 km/h"],
    correct: 0,
    explanation: "0x1388 = 5000. Physical speed = 5000 × 0.01 = 50 km/h.",
  },
  {
    id: "trace",
    question:
      "Where do you inspect CAN identifiers, payloads, and message timestamps in CANoe?",
    options: ["Write window", "Trace window", "CAPL editor"],
    correct: 1,
    explanation:
      "Trace shows communication events. Write shows text such as CAPL write() output.",
  },
  {
    id: "e2e",
    question:
      "Counters are 5, 6, 7, 7, 8. All application CRC checks pass, but the specification forbids duplicates. Is the sequence valid?",
    options: [
      "Yes, because every CRC is valid",
      "No, because counter 7 is repeated",
      "Yes, because the final counter is 8",
    ],
    correct: 1,
    explanation:
      "CRC integrity and counter sequence are separate checks. A valid CRC does not make a forbidden duplicate acceptable.",
  },
  {
    id: "verdict",
    question:
      "An ACC command is sent. Activation is required within 100 ms. What should the test do?",
    options: [
      "Check the state immediately and fail if inactive",
      "Wait 500 ms and always report PASS",
      "Wait for the required active state with a 100 ms deadline",
    ],
    correct: 2,
    explanation:
      "Check the required response within its deadline. An immediate check may read an old state. A fixed delay alone does not verify the requirement.",
  },
];

export default function LearningPanel({ mode }) {
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  if (mode === "practice") {
    return null;
  }

  if (mode === "theory") {
    return (
      <section className="learning-panel">
        <h2>CAN frames and CAPL transmission</h2>

        <h3>CAN frames</h3>
        <p>
          A Classical CAN standard data frame uses an 11-bit identifier from
          0x000 to 0x7FF and carries up to 8 data bytes. The identifier is not a
          destination address.
        </p>
        <p>
          Between competing standard data frames, a lower numeric identifier has
          higher arbitration priority.
        </p>

        <h3>Signals and encoding</h3>
        <p>
          A DBC describes message and signal definitions, including bit
          positions, lengths, byte order, signedness, factors, and offsets.
        </p>
        <pre>{"Physical value = raw value × factor + offset"}</pre>
        <p>
          Our example speed uses an unsigned 16-bit little-endian value, factor
          0.01 km/h, and offset 0.
        </p>
        <pre>
          {"10 27 → 0x2710 → 10000 → 100 km/h\n"}
          {"88 13 → 0x1388 → 5000 → 50 km/h"}
        </pre>
        <p>This is our example signal definition, not a universal CAN rule.</p>

        <h3>CAPL: logging versus transmission</h3>
        <ul>
          <li>
            <code>message 0x123 VehicleSpeed;</code> declares a message.
          </li>
          <li>
            <code>VehicleSpeed.dlc = 2;</code> sets the payload length.
          </li>
          <li>
            <code>VehicleSpeed.byte(0) = 0x10;</code> changes a byte.
          </li>
          <li>
            <code>output(VehicleSpeed);</code> transmits the message.
          </li>
          <li>
            <code>write("Sent");</code> displays text.
          </li>
        </ul>
        <p>
          Assigning bytes alone does not transmit. Our simulator captures a
          message snapshot at each output() call.
        </p>

        <h3>CANoe windows</h3>
        <p>
          Trace displays communication events and timestamps. Write displays
          CAPL logs. Graphics displays signal values over time. Our application
          reproduces only a small educational subset.
        </p>

        <h3>E2E protection</h3>
        <p>
          The CAN frame CRC and an application E2E CRC are distinct. Passing an
          application CRC check does not prove that a counter sequence is valid.
        </p>
        <p>
          For a requirement that forbids duplicates, the sequence 5, 6, 7, 7, 8
          fails because 7 repeats. Counter wraparound and lost-message tolerance
          depend on the selected profile and requirements.
        </p>

        <h3>ADAS testing and timing</h3>
        <p>
          If ACC must activate within 100 ms, wait for the required state with
          that deadline. Do not immediately fail on an old state, and do not
          treat a fixed delay as proof of success.
        </p>
        <p>
          Debug in order: preconditions, stimulus, communication, timing,
          verdict. A frame in Trace does not prove that the ECU accepted its
          application data.
        </p>
      </section>
    );
  }

  const score = questions.filter(
    (question) => answers[question.id] === question.correct,
  ).length;

  return (
    <section className="learning-panel">
      <h2>Knowledge check</h2>
      <p>
        Answer all five questions. This self-study score is graded locally and
        is separate from saved practical completion.
      </p>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          setSubmitted(true);
        }}
      >
        {questions.map((question, index) => (
          <fieldset key={question.id}>
            <legend>
              {index + 1}. {question.question}
            </legend>

            {question.options.map((option, optionIndex) => (
              <label className="quiz-option" key={optionIndex}>
                <input
                  type="radio"
                  name={question.id}
                  checked={answers[question.id] === optionIndex}
                  onChange={() => {
                    setAnswers((current) => ({
                      ...current,
                      [question.id]: optionIndex,
                    }));
                    setSubmitted(false);
                  }}
                />
                <span>{option}</span>
              </label>
            ))}

            {submitted && (
              <p>
                <strong>
                  {answers[question.id] === question.correct
                    ? "Correct. "
                    : "Incorrect. "}
                </strong>
                Correct answer: {question.options[question.correct]}{" "}
                {question.explanation}
              </p>
            )}
          </fieldset>
        ))}

        <button
          type="submit"
          disabled={Object.keys(answers).length !== questions.length}
        >
          Grade quiz
        </button>

        <button
          type="button"
          onClick={() => {
            setAnswers({});
            setSubmitted(false);
          }}
        >
          Reset quiz
        </button>
      </form>

      {submitted && (
        <p role="status">
          Score: {score} / {questions.length}
        </p>
      )}
    </section>
  );
}
