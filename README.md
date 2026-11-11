# VirtualECULab

A browser-based learning workspace for CAN, CAPL, CANoe concepts and ADAS testing. The app has three sections and stores quiz history in PostgreSQL.

| Section | What you can do |
|---|---|
| Theory | Read the Romanian overview, applied examples and linked CANoe, DBC and E2E references. |
| Quiz | Take a 10-question quiz drawn from a shared pool of 250 questions. Use New quiz to replace all ten prompts, or revise missed questions. |
| Workbench | Write or edit a CAPL node, simulate Tx/Rx and timers, decode trace data with a DBC, and check a response against a deadline. |

## Try the Workbench

1. Keep **Receive and transmit** selected and click **Start measurement**. The node initializes its outgoing frame and writes to the console.
2. Under **Stimulus and time**, inject **ID 120** with **10 27**. The node's receive handler transmits **ID 123**. Trace shows both events at 0 ms. Graphics plots **100 km/h** from the sample DBC.
3. Click **Advance clock** with 100 ms entered. Change Rx bytes to **88 13** and inject again. Graphics adds **50 km/h** at 100 ms. Switch **Graph signal** to **Rx and Tx timeline** to view raw frame events instead.
4. Open **DBC editor** and change the factor from 0.01 to 0.02. **Apply DBC** decodes the same captured frames with the updated definition.
5. In **Test Module**, select **Last key or Rx**, expected direction **Tx**, and ID **123**. Enter a deadline and, optionally, the expected bytes. **Run trace check** evaluates the trace from the chosen stimulus. The CAPL example beneath it shows how a CANoe Test Module is structured.

The virtual clock advances when you use its control. Editing the node or loading an example invalidates the current measurement. The CAPL draft stays in memory when you switch tabs. Refreshing the page resets the Workbench.

## Quiz rotation

The server stores the questions and answer key for each quiz. New quiz excludes the current set and prioritizes prompts you have never seen. Once you have seen the pool, the oldest prompts become eligible again. Revision deliberately selects questions you missed. Existing quiz attempts and their scores remain in the database.

## Set up from source

Use Python 3.12 or newer, Node.js 24 and PostgreSQL. Create a PostgreSQL database named `virtualeculab` and a role named `virtualeculab_app` that owns it. Copy `.env.example` to `.env` and enter the role password. Keep `.env` local.

From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m backend.init_db --local-only
npm.cmd --prefix frontend ci
```

Start the servers in two terminals from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

```powershell
npm.cmd --prefix frontend run dev -- --port 5173 --strictPort
```

Open [http://localhost:5173](http://localhost:5173).

## Verify

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

The PostgreSQL integration test runs with `POSTGRES_TEST_URL` pointing to a disposable database. GitHub Actions runs backend tests, frontend checks and Playwright against PostgreSQL. See [validation results](docs/VALIDATION.md).

## Simulator scope

- The node simulator supports a CAPL subset with `on start`, `on key`, `on message`, `on timer`, `write`, `output`, and timer controls. It models standard Classical CAN IDs and up to eight data bytes. Tx appears in the trace and requires explicit Rx injection to trigger a receive handler. There is no physical bus connection.
- The DBC editor decodes byte-aligned signals of 1–6 bytes within standard CAN frames. It supports signed and unsigned Intel and Motorola fields, factor and offset. Multiplexed and non-byte-aligned fields are outside the supported subset.
- Test Module checks actual simulated frames by ID, direction, optional exact payload and an inclusive deadline. The displayed `MainTest()` example is for a CANoe configuration with the database message defined. The browser executes the configurable trace check.
- Legacy simulation and assessment API routes remain available for existing callers and stored learning records.

## References

- [Vector CANoe Test Feature Set tutorial](https://support.vector.com/sys_attachment.do?sys_id=b1d992aa1bcca094d2cd97de1d4bcb4b)
- [CSS Electronics DBC signal encoding guide](https://www.csselectronics.com/pages/can-dbc-file-database-intro)
- [AUTOSAR E2E protocol specification](https://www.autosar.org/fileadmin/standards/R21-11/FO/AUTOSAR_PRS_E2EProtocol.pdf)
