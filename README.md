# VirtualECULab
[Live Demo](https://virtualeculab.onrender.com) · [Source Code](https://github.com/MadalinaRVeliche/VirtualECULab) · [CI Tests](https://github.com/MadalinaRVeliche/VirtualECULab/actions)

**Try the demo:** Open Workbench, start a measurement, and inject the default CAN frame. Inspect the Rx and Tx entries in CAN Trace and the decoded speed in Graphics.

##

VirtualECULab is an interactive browser lab for learning CAN communication, event-driven CAPL programming, and the fundamentals of ADAS testing. It brings together a Romanian-language theory reference, a course-wide quiz, and a simulator where learners can inspect the evidence behind a test verdict.

| Area | What you can do |
| --- | --- |
| **Theory** | Study CAN frames, CAPL events and timers, DBC signal definitions, watchdogs, E2E protection, and CANoe Test Modules. |
| **Quiz** | Answer 10 questions drawn from a pool of 250. Start a new set or revisit missed questions, with scores and attempt history saved in PostgreSQL. |
| **Workbench** | Edit a CAPL node, inject Rx frames, observe Tx traffic, plot decoded signals, and check whether a frame meets a deadline. |

## Workbench walkthrough

The default **Receive and transmit** example copies a two-byte payload from incoming ID `0x120` to outgoing ID `0x123`. The sample DBC decodes the outgoing payload as vehicle speed.

1. Open **Workbench** and select **Start measurement**.
2. Under **Stimulus and time**, inject Rx ID `120` with bytes `10 27`. **CAN Trace** shows an Rx frame and a Tx frame at 0 ms. **Graphics** plots 100 km/h.
3. Advance the clock by 100 ms, change the Rx bytes to `88 13`, and inject again. Graphics adds a 50 km/h sample at 100 ms.
4. In **Test Module**, select **Last key or Rx**, expected direction **Tx**, and ID `123`. Enter a 100 ms deadline and expected bytes `88 13`, then select **Run trace check**. The relay passes because the matching frame appears at the stimulus timestamp.

To inspect raw frame timing, select **Rx and Tx timeline** under **Graph signal**. To see how a DBC definition changes interpretation, open **DBC editor**, change the sample factor from `0.01` to `0.02`, and apply it to the captured trace.

## Local development

**Requirements:** Python 3.12 or newer, Node.js 24 with npm, and a local PostgreSQL instance. GitHub Actions runs the backend on Python 3.14.

### 1. Configure PostgreSQL

Create a login role named `virtualeculab_app` and a database named `virtualeculab` owned by that role. From the repository root, copy the example environment file and set `DB_PASSWORD` to the role password. Keep `.env` out of Git.

```powershell
Copy-Item .env.example .env
```

### 2. Install dependencies and initialize the schema

Run these commands from the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m backend.init_db --local-only
npm.cmd --prefix frontend ci
```

### 3. Start the application

Start FastAPI and Vite in separate terminals from the repository root.

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

```powershell
npm.cmd --prefix frontend run dev -- --port 5173 --strictPort
```

Open [the application](http://localhost:5173) or explore the [API documentation](http://127.0.0.1:8000/docs).

## Architecture

| Component | Responsibility |
| --- | --- |
| [React and Vite](frontend/) | Theory, quiz, CAPL editor, DBC decoding, trace visualization, and configurable trace checks. |
| [FastAPI and Python](backend/) | Quiz selection and grading, API validation, and deterministic replay of CAPL programs against virtual input events. |
| [PostgreSQL and SQLAlchemy](backend/models.py) | Quiz sessions, attempt history, and progress records. |

The simulation API replays the CAPL source and its ordered input history. The virtual clock advances through explicit controls, so the same program and input sequence produce the same trace. The current editor draft stays in memory while switching tabs. Reloading the page resets the Workbench.

## Testing

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
```

With both servers running, install Chromium and run the browser suite:

```powershell
Push-Location frontend
npx.cmd playwright install chromium
npx.cmd playwright test
Pop-Location
```

Backend API tests use SQLite by default. Set `POSTGRES_TEST_URL` to a disposable PostgreSQL database to run the integration test. The [GitHub Actions workflow](.github/workflows/tests.yml) runs backend and frontend checks and Playwright against PostgreSQL. See the [validation report](docs/VALIDATION.md) for test coverage and results.

## Simulator scope

- **CAPL:** The browser lab models an educational subset of CAPL with startup, keyboard, receive, and timer handlers. It supports standard 11-bit Classical CAN identifiers and payloads of up to eight bytes. Rx is injected explicitly and there is no connection to a physical CAN bus.
- **DBC:** The editor supports signed and unsigned byte-aligned Intel and Motorola signals from 1 to 6 bytes, with factor and offset. Multiplexed and non-byte-aligned signals are outside the supported subset.
- **Test Module:** The lab evaluates simulated frames by direction, ID, optional exact payload, and an inclusive deadline. The included `MainTest()` example illustrates how to structure a test in Vector CANoe.

## References

- [Vector CANoe Test Feature Set tutorial](https://support.vector.com/sys_attachment.do?sys_id=b1d992aa1bcca094d2cd97de1d4bcb4b)
- [CSS Electronics DBC signal encoding guide](https://www.csselectronics.com/pages/can-dbc-file-database-intro)
- [AUTOSAR E2E protocol specification](https://www.autosar.org/fileadmin/standards/R21-11/FO/AUTOSAR_PRS_E2EProtocol.pdf)
