import { useState } from "react";
import { programs, testModuleExample } from "./workbenchData";

const languageKey = "virtualeculab.theory.language";

const copy = {
  ro: {
    title: "Teorie CAN, CAPL și ADAS",
    intro:
      "Începe cu traseul unui mesaj CAN: cadrul apare în Trace, semnalul este decodat din DBC, iar testul verifică dacă răspunsul respectă cerința.",
    overview: "Noțiuni de bază",
    contents: "Cuprins",
    applied: "Teorie aplicată",
    example: "Exemplu",
    observe: "Ce verifici",
    references: "Referințe",
    basics: [
      [
        "CAN — Controller Area Network",
        "ECU-urile schimbă cadre pe magistrală. ID-ul identifică mesajul și participă la arbitraj. Între cadre de același format, ID-ul numeric mai mic are prioritate. Un cadru standard CAN clasic are ID de 11 biți și până la 8 octeți de date. CAN FD poate transporta până la 64.",
      ],
      [
        "CANoe — simulare și analiză",
        "Simulation Setup configurează nodurile. Trace afișează cadrele și timestamp-urile. Graphics arată evoluția semnalelor decodate, iar Write Window afișează logurile CAPL.",
      ],
      [
        "CAPL — cod bazat pe evenimente",
        "Scrii funcții care rulează la pornire, la apăsarea unei taste, la recepția unui mesaj sau la expirarea unui timer. Programul reacționează la evenimente în timpul măsurării.",
      ],
      [
        "Testare și verdict",
        "Un test pornește de la o cerință. Pregătești condițiile inițiale, aplici stimulul și compari răspunsul observat cu valoarea și termenul cerut.",
      ],
    ],
  },
  en: {
    title: "CAN, CAPL and ADAS Theory",
    intro:
      "Follow a CAN message through the workflow: the frame appears in Trace, the DBC defines how to decode its signal, and a test checks whether the response meets a requirement.",
    overview: "Foundations",
    contents: "Contents",
    applied: "Applied theory",
    example: "Example",
    observe: "What to check",
    references: "References",
    basics: [
      [
        "CAN — Controller Area Network",
        "ECUs exchange frames on the bus. The identifier identifies the message and participates in arbitration. Among frames of the same format, the lower numerical ID has priority. A standard Classical CAN frame has an 11-bit ID and up to 8 data bytes. CAN FD can carry up to 64.",
      ],
      [
        "CANoe — simulation and analysis",
        "Simulation Setup configures the nodes. Trace displays frames and timestamps. Graphics shows how decoded signals change over time, and the Write Window displays CAPL logs.",
      ],
      [
        "CAPL — event-driven code",
        "Write handlers that run when measurement starts, a key is pressed, a message arrives, or a timer expires. The program reacts to events during measurement.",
      ],
      [
        "Testing and verdicts",
        "A test starts with a requirement. Set up the initial conditions, apply the stimulus, and compare the observed response with the required value and deadline.",
      ],
    ],
  },
};

const chapters = [
  {
    id: "can-dbc",
    code: [
      "BO_ 291 VehicleSpeed: 2 SpeedECU",
      ' SG_ Speed : 0|16@1+ (0.01,0) [0|655.35] "km/h" DisplayECU',
      "",
      "10 27 → 0x2710 → 10000 → 100 km/h",
      "88 13 → 0x1388 →  5000 →  50 km/h",
    ].join("\n"),
    ro: {
      title: "Din cadrul CAN la viteza din grafic",
      paragraphs: [
        "În Trace vezi ID-ul, direcția Rx/Tx, DLC-ul și octeții. ID-ul CAN identifică mesajul, iar DBC-ul descrie cum sunt interpretate datele. Pentru decodare ai nevoie de poziția și lungimea semnalului, ordinea octeților, semnul, factorul și offset-ul.",
        "În exemplul de mai jos, ID-ul 291 din DBC este 0x123 în hex. Semnalul Speed ocupă 16 biți de la bitul 0. @1 indică Intel (little-endian), iar + indică unsigned. Formula este valoare fizică = raw × factor + offset.",
      ],
      check:
        "În Workbench, transmite ambele payload-uri. Compară octeții din Trace cu 100 și 50 km/h în Graphics. Dacă valoarea raw este corectă, dar viteza diferă, verifică factorul și offset-ul.",
    },
    en: {
      title: "From a CAN frame to speed on the graph",
      paragraphs: [
        "Trace shows the ID, Rx/Tx direction, DLC, and data bytes. The CAN ID identifies the message, and the DBC describes how to interpret its data. Decoding requires the signal position and length, byte order, signedness, factor, and offset.",
        "In the example below, decimal DBC ID 291 is hexadecimal 0x123. Speed occupies 16 bits starting at bit 0. @1 means Intel (little-endian), and + means unsigned. Physical value = raw × factor + offset.",
      ],
      check:
        "In Workbench, transmit both payloads. Compare the Trace bytes with 100 and 50 km/h in Graphics. If the raw value is correct but the speed differs, check the factor and offset.",
    },
  },
  {
    id: "capl",
    code: programs.relay.code,
    ro: {
      title: "Recepție și transmitere în CAPL",
      paragraphs: [
        "Folosește on start pentru inițializare, on key pentru un stimul manual și on message pentru recepție. Într-un handler de recepție, this.byte(0) citește primul octet din cadrul primit.",
        "În exemplul de mai jos, nodul primește 0x120, copiază cei doi octeți în mesajul 0x123 și apelează output(). Fiecare apel output() capturează datele pentru cadrul transmis. write() adaugă o linie în consolă.",
      ],
      check:
        "Pornește exemplul Receive and transmit și injectează ID 120 cu doi octeți. În Trace ar trebui să vezi mai întâi Rx 0x120, apoi Tx 0x123, cu același payload.",
    },
    en: {
      title: "Receiving and transmitting in CAPL",
      paragraphs: [
        "Use on start to initialize, on key for a manual stimulus, and on message for reception. Inside a receive handler, this.byte(0) reads the first byte of the incoming frame.",
        "In the example below, the node receives 0x120, copies two bytes to message 0x123, and calls output(). Each output() call captures the data for that transmitted frame. write() adds a line to the console.",
      ],
      check:
        "Start the Receive and transmit example and inject ID 120 with two bytes. Trace should show Rx 0x120 followed by Tx 0x123 with the same payload.",
    },
  },
  {
    id: "timers",
    code: [
      "variables { msTimer watchdog; }",
      "",
      "on start { setTimer(watchdog, 500); }",
      "on message 0x300 { setTimer(watchdog, 500); }",
      'on timer watchdog { write("Communication timeout"); }',
    ].join("\n"),
    ro: {
      title: "Timere, periodicitate și watchdog",
      paragraphs: [
        "Un msTimer expiră o singură dată. Pentru trafic periodic, programează următoarea expirare din on timer. setTimer() înlocuiește termenul anterior, iar cancelTimer() îl anulează.",
        "Un watchdog de recepție măsoară timpul scurs de la ultimul cadru relevant. Exemplul pornește timerul la inițializare și îl reprogramează la fiecare mesaj 0x300. Dacă traficul se oprește, expirarea apare după 500 ms de liniște.",
      ],
      check:
        "În exemplul Periodic timer, avansează ceasul 300 ms și compară timestamp-urile 100, 200 și 300 ms. Pentru watchdog, folosește codul de mai jos și verifică în consolă când apare timeout-ul.",
    },
    en: {
      title: "Timers, periodic traffic, and watchdogs",
      paragraphs: [
        "An msTimer expires once. To generate periodic traffic, schedule the next expiry inside on timer. setTimer() replaces the previous deadline, and cancelTimer() removes it.",
        "A receive watchdog measures the time since the last relevant frame. This example arms the timer at startup and rearms it on each 0x300 frame. If traffic stops, the timer expires after 500 ms of silence.",
      ],
      check:
        "In Periodic timer, advance the clock by 300 ms and compare the timestamps at 100, 200, and 300 ms. For the watchdog, run the example and use the console to check when the timeout occurs.",
    },
  },
  {
    id: "test-modules",
    code: testModuleExample,
    ro: {
      title: "De la cerință la verdict",
      paragraphs: [
        "Pregătește precondițiile, aplică stimulul și așteaptă un răspuns nou până la termen. Verifică atât valoarea, cât și timpul. De exemplu, pentru o activare în maximum 100 ms, o stare ACTIVE observată la 80 ms trece, iar aceeași stare la 120 ms e prea târzie.",
        "Într-un Test Module CANoe, MainTest() organizează cazurile, testcase definește un caz, iar funcțiile TestStepPass și TestStepFail raportează rezultatul. Exemplul presupune că VehicleSpeed este definit în baza de date CANoe.",
      ],
      check:
        "În Workbench, Test Module verifică traseul simulat după un stimul. Alege direcția, ID-ul, termenul și, opțional, payload-ul. Compară un răspuns la termen cu unul întârziat.",
    },
    en: {
      title: "From requirement to verdict",
      paragraphs: [
        "Set up the preconditions, apply the stimulus, and wait for a fresh response up to the deadline. Check both the value and the timing. For example, for activation within 100 ms, ACTIVE at 80 ms passes and ACTIVE at 120 ms arrives too late.",
        "In a CANoe Test Module, MainTest() organizes the cases, testcase defines a case, and TestStepPass and TestStepFail report the result. The example assumes VehicleSpeed is defined in the CANoe database.",
      ],
      check:
        "In Workbench, Test Module evaluates the simulated trace after a stimulus. Choose the direction, ID, deadline, and optional payload. Compare an on-time response with a late one.",
    },
  },
  {
    id: "e2e",
    code: "13 → 14 → 15 → 0 → 1\n 5 →  6 →  7 → 7 → 8",
    ro: {
      title: "E2E: integritate, secvență și prospețime",
      paragraphs: [
        "CRC-ul CAN verifică integritatea cadrului la nivel de legătură. Protecția E2E verifică datele la nivel de aplicație. Profilul ales stabilește ce câmpuri intră în CRC, cum se folosește Data ID și ce salturi de contor sunt acceptate.",
        "Într-un exemplu modulo 16, trecerea de la 15 la 0 este normală. În a doua secvență, valoarea 7 se repetă. Un CRC corect poate însoți acel duplicat, iar cerința de secvență decide dacă receptorul îl acceptă. Absența completă a cadrelor se verifică prin timeout.",
      ],
      check:
        "Când investighezi un cadru respins, notează separat timestamp-ul, rezultatul CRC și ultimul contor acceptat. Confirmarea ACK a cadrului CAN nu dovedește acceptarea datelor de către aplicație.",
    },
    en: {
      title: "E2E: integrity, sequence, and freshness",
      paragraphs: [
        "The CAN CRC checks frame integrity at the link layer. E2E protection checks data at the application layer. The selected profile defines which fields the CRC covers, how the Data ID is used, and which counter jumps are accepted.",
        "In a modulo-16 example, the counter wraps from 15 to 0. In the second sequence, 7 repeats. That duplicate can have a valid CRC, while the sequence requirement determines whether the receiver accepts it. A timeout detects a complete absence of frames.",
      ],
      check:
        "When investigating a rejected frame, record the timestamp, CRC result, and last accepted counter separately. A CAN frame ACK does not establish application-level acceptance.",
    },
  },
  {
    id: "adas",
    ro: {
      title: "Scenarii ADAS și depanare",
      paragraphs: [
        "La ACC, testează precondițiile de activare, menținerea vitezei sau distanței, reacția la vehiculul din față și comportamentul la apăsarea frânei. La AEB, verifică obstacolul, validitatea senzorilor, momentul intervenției și scenariile în care frânarea ar fi nejustificată.",
        "TTC estimează timpul până la coliziune într-un model simplificat. La 20 m distanță și o viteză de apropiere de 10 m/s, TTC este 2 s. Pragul și comportamentul așteptat vin din cerința sistemului.",
      ],
      check:
        "La un test eșuat, verifică în ordine precondițiile, stimulul, cadrul și semnalul decodat, timpul de răspuns și verdictul. Caută prima observație care diferă de cerință.",
    },
    en: {
      title: "ADAS scenarios and troubleshooting",
      paragraphs: [
        "For ACC, test activation conditions, speed or gap control, the response to the lead vehicle, and behavior when the driver brakes. For AEB, check the obstacle, sensor validity, intervention timing, and scenarios where braking would be unwarranted.",
        "TTC estimates time to collision in a simplified model. At a distance of 20 m and a closing speed of 10 m/s, TTC is 2 s. The threshold and expected behavior come from the system requirement.",
      ],
      check:
        "When a test fails, inspect the preconditions, stimulus, frame and decoded signal, response timing, and verdict in that order. Find the first observation that differs from the requirement.",
    },
  },
];

export default function TheoryDetails({ sources = [] }) {
  const [language, setLanguage] = useState(() => {
    try {
      return localStorage.getItem(languageKey) === "en" ? "en" : "ro";
    } catch {
      return "ro";
    }
  });

  const text = copy[language];

  function changeLanguage(event) {
    const next = event.target.value;
    setLanguage(next);
    try {
      localStorage.setItem(languageKey, next);
    } catch {
      // The selector still works if browser storage is unavailable.
    }
  }

  return (
    <section className="learning-panel theory-page" lang={language}>
      <label>
        {language === "ro" ? "Limba" : "Language"}
        <select value={language} onChange={changeLanguage}>
          <option value="ro" lang="ro">
            Română
          </option>
          <option value="en" lang="en">
            English
          </option>
        </select>
      </label>
      <header className="theory-header">
        <div>
          <h2>{text.title}</h2>
          <p>{text.intro}</p>
        </div>
      </header>

      <section aria-labelledby="theory-foundations">
        <h3 id="theory-foundations">{text.overview}</h3>
        <dl className="theory-foundations">
          {text.basics.map(([title, description]) => (
            <div key={title}>
              <dt>{title}</dt>
              <dd>{description}</dd>
            </div>
          ))}
        </dl>
      </section>

      <nav className="theory-contents" aria-label={text.contents}>
        <h3>{text.contents}</h3>
        <ul>
          {chapters.map(({ id, ...chapter }) => (
            <li key={id}>
              <a href={`#theory-${id}`}>{chapter[language].title}</a>
            </li>
          ))}
        </ul>
      </nav>

      <section aria-labelledby="theory-applied">
        <h3 id="theory-applied">{text.applied}</h3>
        {chapters.map(({ id, code, ...chapter }) => {
          const section = chapter[language];
          return (
            <section className="theory-chapter" id={`theory-${id}`} key={id}>
              <h4>{section.title}</h4>
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
              {code && (
                <details>
                  <summary>{text.example}</summary>
                  <pre>
                    <code>{code}</code>
                  </pre>
                </details>
              )}
              <p className="theory-check">
                <strong>{text.observe}.</strong> {section.check}
              </p>
            </section>
          );
        })}
      </section>

      <section aria-labelledby="theory-references">
        <h3 id="theory-references">{text.references}</h3>
        <ul>
          {sources.map(({ label, url }) => (
            <li key={url}>
              <a href={url} target="_blank" rel="noreferrer">
                {label}
              </a>
            </li>
          ))}
        </ul>
      </section>
    </section>
  );
}
