# VirtualECULab

An English learning workspace for CAN, CANoe concepts, an educational CAPL subset, and ADAS test reasoning. React + FastAPI + local PostgreSQL. One local learner; no account isolation.

## Learning path

| Module | Practical evidence |
|---|---|
| 1. Your first CAPL event | Startup log, distinct from transmission |
| 2. Multiple messages | Exact console order |
| 3. Keyboard events | Matching key dispatch |
| 4. Transmit vehicle speed | ID 0x123, DLC 2, 100 → 50 km/h payloads |
| 5. Multiple events and state | Counter persists across key actions |
| 6. Timers and periodic traffic | Correct intervals, cancellation and restart |
| 7. Reception and watchdogs | Last-Rx deadline, silence and recovery |
| 8. Signals and DBC | Byte-aligned unsigned decoding at multiple values |
| 9. E2E integrity and sequence | Toy CRC/counter state-machine classifications |
| 10. Test verdicts and deadlines | Fresh response, boundary, late, absent and invalid setup |
| 11. ADAS scenario reasoning | Explicit simplified TTC/AEB rules and ACC state explorer |

Each module provides Theory, Practice, Quiz, Challenges and Progress. The bank has 80 question entries across modules, including numeric variants and debugging scenarios. New quizzes sample a bank and reorder questions; questions can recur. Revision prioritizes unresolved missed questions. Quiz grading and attempts are server-side. Reviewed theory, practical completion, independent challenges and quiz scores are distinct records. Achievements have visible evidence-based rules. Interview prompts offer unsaved freeform notes, without unreliable automatic scoring.

## Existing project upgrade

See the supplied `Install-Update.ps1` and installation guide in the update package. The installer makes a source backup, checks base-file hashes, preserves `.env`, `.git`, `.venv` and existing PostgreSQL data, installs dependencies, creates only missing tables, and runs non-browser checks. It does not start/stop PostgreSQL or commit/push anything.

## Setup from source

Use Python 3.12+ (the original project uses 3.14), Node.js 24, npm and local PostgreSQL. Create database `virtualeculab`, owned by `virtualeculab_app`. Copy `.env.example` to `.env` and enter the local application's password. Do not commit `.env`. Leave DATABASE_URL unset for the normal local DB_* configuration; the override exists for explicit disposable test databases.

From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m backend.init_db --local-only
npm.cmd --prefix frontend ci
```

Start the backend in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Start the frontend in another:

```powershell
npm.cmd --prefix frontend run dev -- --port 5173 --strictPort
```

Open http://localhost:5173. Existing VS Code tasks continue working. `scripts/start-servers.ps1` remains available for background startup, but visible tasks are easier to stop with Ctrl+C.

## Verification

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
```

With both servers running:

```powershell
cd frontend
npx.cmd playwright install chromium
npx.cmd playwright test
```

PostgreSQL integration is opt-in via POSTGRES_TEST_URL pointing to a disposable database. CI provides PostgreSQL 18; its E2E job runs the PostgreSQL integration test before browser tests. Backend unit tests isolate each test in in-memory SQLite. Frontend component tests exercise UI with mocked API contracts. Playwright covers the real UI/API/database stack in CI.

Current local validation details are in `docs/VALIDATION.md`. A retained third-party Starlette/httpx deprecation warning is non-blocking; dependency versions were not casually upgraded to suppress it.

## Simulation semantics and supported subset

The original basic lessons and `/simulate` API retain compatibility. Modules 4–7 and CAPL challenges use `/lab/run`, a separate bounded multi-event workbench:

- declarations: `int`, `byte`, `msTimer`, raw standard `message`;
- handlers: `on start`, `on key 'a'`, `on message 0x300`, `on timer name`;
- assignments, integer arithmetic/comparisons, `&&`, `||`, `!`, `if/else`, `++/--`;
- `write("literal")`, `output(message)`, `setTimer(timer,ms)`, `cancelTimer(timer)`;
- message `.dlc`, `.byte(index)` and read-only `.id`; read-only `this` in reception;
- line/block comments; no string escape sequences or formatted write calls;
- no loops, user functions, includes, arbitrary arrays, bitwise operators, native calls, timers in seconds, extended IDs, CAN FD or physical bus access.

Start simulation replays from declarations and invokes on start. Each control action appends to the submitted history. The backend reconstructs the measurement deterministically. Editing code invalidates its history; section changes preserve it. Workbench drafts reset when changing modules or reloading. Trace rows persist across learning sections but clear on reload. Clearing Trace only clears its display; the next replay can restore historical lab frames from the measurement. Press Start simulation to reset measurement history.

Timers are one-shot. Rearming replaces their due time. Due timers execute chronologically and, at equal deadlines, by scheduling order. An expiry exactly at an advance boundary executes before the next injected Rx/key action. This is an explicitly defined teaching rule, not a guarantee about all CANoe scheduling contexts. Tx does not loop back automatically. A received byte beyond DLC raises an error. Message buffers begin zeroed; explicit DLC is required before output. Byte overflow is rejected instead of emulating CAPL casts. Requests are bounded to 20,000 code characters, 200 actions, 60,000 virtual milliseconds and 10,000 executed statements. There is no shared server simulation session.

Exercise checking uses fresh scenario replays, not the interactive history, and does not add frames to the visible trace. Console strings cannot pass a frame or timing exercise.

## Explicit model limits

- No CANoe executable, Vector licensing, physical CAN ACK, bus arbitration, error confinement or bus-off simulation.
- The example DBC describes ID 0x123 speed bytes 0–1, unsigned Intel, factor 0.01, offset 0. The decoder handles unsigned byte-aligned fields, not arbitrary DBC parsing or Motorola start-bit numbering.
- E2E is **not an AUTOSAR profile**. This toy profile uses modulo 16 and CRC-8/SAE-J1850 parameters (poly 0x1D, init/xorout 0xFF, no reflection) over Data ID high byte, Data ID low byte, counter byte and up to six data bytes. The Data ID is CRC metadata; a conceptual Classical CAN payload can contain one CRC byte, one counter byte and those data bytes. CRC check vector `123456789` is 0x4B. Repeated, bad-CRC and wrong-sequence frames do not advance the accepted baseline. `maxLost` controls the permitted counter delta. There is no freshness timeout in this tool; timeouts are taught in the watchdog module. A CAN frame CRC is different from this application CRC.
- Test Bench is a structured model, not an interpreter for CANoe `testcase`/test wait APIs. Observations are fresh, relative to the stimulus, and the deadline boundary is inclusive. NOT_EXECUTED denotes invalid setup in this lab.
- ADAS is a constant-velocity offline model, not a production controller or real driving guidance. Actual thresholds, sensor confidence, actuation and fallback behavior depend on OEM requirements.

## References

- [Vector CANoe Test Feature Set tutorial](https://support.vector.com/sys_attachment.do?sys_id=b1d992aa1bcca094d2cd97de1d4bcb4b)
- [CSS Electronics: DBC signal encoding](https://www.csselectronics.com/pages/can-dbc-file-database-intro)
- [AUTOSAR E2E protocol specification](https://www.autosar.org/fileadmin/standards/R21-11/FO/AUTOSAR_PRS_E2EProtocol.pdf)

Reference specifications explain the real tools/profiles. They do not certify this educational implementation.
