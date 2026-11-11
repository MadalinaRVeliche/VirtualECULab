const details = [
  {
    title: "Cadre CAN și semnale DBC",
    text: "Trace arată cadrul brut: momentul recepției sau transmisiei, ID-ul și octeții. DBC explică ce reprezintă acei octeți. În exemplul nostru, BO_ folosește ID-ul 291 în zecimal (0x123), iar Speed are 16 biți, @1 pentru Intel și + pentru unsigned. Octeții 10 27 dau raw 10000, deci 100 km/h la factor 0,01 și offset 0. Pentru Motorola, bitul de start marchează capătul cel mai semnificativ al câmpului. Verifică decodarea cu cel puțin două valori cunoscute.",
    code: 'BO_ 291 VehicleSpeed: 2 SpeedECU\n SG_ Speed : 0|16@1+ (0.01,0) [0|655.35] "km/h" DisplayECU',
    source: "https://www.csselectronics.com/pages/can-dbc-file-database-intro",
  },
  {
    title: "Nod CAPL și evenimente de magistrală",
    text: "Într-un nod de simulare, folosești on start pentru inițializare, on message pentru recepție și output() pentru transmitere. Poți copia datele primite din this într-un obiect message separat. Un msTimer expiră o dată. Dacă ai nevoie de trafic periodic, îl reprogramezi în on timer. În Workbench, injectează explicit un Rx pentru a declanșa handlerul de recepție și avansează ceasul pentru a testa un timer.",
    source: "https://support.vector.com/sys_attachment.do?sys_id=b1d992aa1bcca094d2cd97de1d4bcb4b",
  },
  {
    title: "Test Module în CANoe",
    text: "Un Test Module se configurează în Test Setup. MainTest() stabilește ordinea cazurilor. Un testcase pregătește condițiile, aplică stimulul, așteaptă un răspuns cu o limită și verifică datele observate înainte să emită verdictul. În Workbench configurezi aceeași verificare pentru cadrele simulate: ID, direcție, payload opțional și timp maxim. Exemplul CAPL din Workbench arată forma de cod pentru CANoe.",
    source: "https://support.vector.com/sys_attachment.do?sys_id=b1d992aa1bcca094d2cd97de1d4bcb4b",
  },
  {
    title: "E2E, watchdog și dovezi",
    text: "E2E verifică integritatea și secvența la nivel de aplicație. Un CRC valid poate însoți un contor repetat. Profilul configurat determină câmpurile protejate, regula contorului și utilizarea Data ID. Un watchdog verifică altă proprietate: dacă un mesaj a lipsit prea mult după ultima recepție relevantă. La depanare, notează ID-ul, timestamp-ul, statusul CRC și contorul acceptat înainte să interpretezi verdictul.",
    source: "https://www.autosar.org/fileadmin/standards/R21-11/FO/AUTOSAR_PRS_E2EProtocol.pdf",
  },
];

export default function TheoryDetails({ modules }) {
  return <section className="theory-details">
    <h2>Teorie aplicată</h2>
    {details.map(({ title, text, code, source }) => <section key={title}>
      <h3>{title}</h3>
      <p>{text}</p>
      {code && <pre>{code}</pre>}
      <a href={source} target="_blank" rel="noreferrer">Referință</a>
    </section>)}
    <h3>Subiecte de aprofundat</h3>
    {modules.filter((module) => module.kind !== "theory").map((module) => (
      <details key={module.id}>
        <summary>{module.title}</summary>
        {module.theory.map(({ title, text, example }) => <section key={title}>
          <h4>{title}</h4>
          <p>{text}</p>
          {example && <pre>{example}</pre>}
        </section>)}
      </details>
    ))}
  </section>;
}
