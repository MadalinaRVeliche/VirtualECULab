"""Curated teaching content. Solutions/answer keys never enter public module JSON."""

from copy import deepcopy

SOURCES = [
    {
        "label": "Vector: CANoe Test Feature Set tutorial",
        "url": "https://support.vector.com/sys_attachment.do?sys_id=b1d992aa1bcca094d2cd97de1d4bcb4b",
    },
    {
        "label": "CSS Electronics: DBC signal encoding",
        "url": "https://www.csselectronics.com/pages/can-dbc-file-database-intro",
    },
    {
        "label": "AUTOSAR E2E protocol specification (reference, not our toy profile)",
        "url": "https://www.autosar.org/fileadmin/standards/R21-11/FO/AUTOSAR_PRS_E2EProtocol.pdf",
    },
]

SPEED = """variables
{
  message 0x123 VehicleSpeed;
}
on key 'a'
{
  VehicleSpeed.dlc = 2;
  VehicleSpeed.byte(0) = 0x10;
  VehicleSpeed.byte(1) = 0x27;
  output(VehicleSpeed);
  VehicleSpeed.byte(0) = 0x88;
  VehicleSpeed.byte(1) = 0x13;
  output(VehicleSpeed);
}"""
STATE = """variables
{
  int count = 0;
  message 0x200 Status;
}
on start
{
  Status.dlc = 1;
}
on key 'a'
{
  count++;
  Status.byte(0) = count;
  output(Status);
}"""
PERIODIC = """variables
{
  msTimer heartbeat;
  message 0x300 Heartbeat;
}
on start
{
  Heartbeat.dlc = 1;
  Heartbeat.byte(0) = 1;
  setTimer(heartbeat, 100);
}
on timer heartbeat
{
  output(Heartbeat);
  setTimer(heartbeat, 100);
}
on key 's'
{
  cancelTimer(heartbeat);
}
on key 'r'
{
  setTimer(heartbeat, 100);
}"""
WATCHDOG = """variables
{
  msTimer watchdog;
  int timedOut = 0;
}
on start
{
  setTimer(watchdog, 500);
}
on message 0x300
{
  timedOut = 0;
  setTimer(watchdog, 500);
}
on timer watchdog
{
  timedOut = 1;
  write("Communication timeout");
}"""


def section(title, text, example=None):
    return {"title": title, "text": text, "example": example}


def question(identifier, prompt, options, correct, explanation, topic):
    return {
        "id": identifier,
        "prompt": prompt,
        "options": options,
        "correct": correct,
        "explanation": explanation,
        "topic": topic,
    }


FOUNDATION = [
    question(
        "transmission",
        "Which statement transmits a CAN message?",
        ['write("Message sent");', "output(VehicleSpeed);", "VehicleSpeed.dlc = 2;"],
        1,
        "output() transmits; write() logs text. Assignments only change the message object.",
        "CAPL transmission",
    ),
    question(
        "decoding",
        "Decode 88 13 as unsigned little-endian speed, factor 0.01, offset 0.",
        ["50 km/h", "100 km/h", "136.19 km/h"],
        0,
        "0x1388 = 5000; 5000 × 0.01 = 50 km/h.",
        "Signal encoding",
    ),
    question(
        "trace",
        "Where do you inspect CAN identifiers, payloads and timestamps in CANoe?",
        ["Write window", "Trace window", "CAPL editor"],
        1,
        "Trace displays communication events. Write displays CAPL text logs.",
        "CANoe debugging",
    ),
    question(
        "e2e",
        "Counters are 5,6,7,7,8; all CRCs pass. Duplicates are forbidden. Is this valid?",
        [
            "Yes, because every CRC is valid",
            "No, because counter 7 is repeated",
            "Yes, because the final counter is 8",
        ],
        1,
        "CRC and sequence checks are distinct. A repeated counter violates this stated requirement.",
        "E2E sequence",
    ),
    question(
        "verdict",
        "ACC must activate within 100 ms. What should the test do?",
        [
            "Check the state immediately and fail if inactive",
            "Wait 500 ms and always report PASS",
            "Wait for the required active state with a 100 ms deadline",
        ],
        2,
        "Wait for a fresh qualifying response within the requirement's deadline.",
        "Test timing",
    ),
]

MODULES = {}


def module(
    identifier,
    title,
    description,
    task,
    code,
    theory,
    bank,
    *,
    kind="capl",
    challenge="",
    challenge_code=None,
    example=None,
):
    MODULES[identifier] = {
        "id": identifier,
        "title": title,
        "description": description,
        "task": task,
        "code": code,
        "kind": kind,
        "theory": theory,
        "quiz_bank": bank,
        "challenge": challenge,
        "challenge_code": challenge_code or code,
        "worked_example": example or code,
        "sources": SOURCES,
        "level": "Foundation"
        if identifier <= 4
        else "Applied"
        if identifier <= 8
        else "Interview",
    }


module(
    1,
    "Your first CAPL event",
    "Start an ECU and distinguish logs from traffic.",
    "Write an on start event that prints exactly one message: ECU ready",
    'on start\n{\n  write("Hello, ECU!");\n}',
    [
        section(
            "CAN frames and CAPL transmission",
            "CANoe analyzes and simulates networks. CAPL reacts to events. Our app is an educational subset, not Vector CANoe or a CAPL compiler.",
        ),
        section(
            "Startup",
            "on start runs once when measurement starts. In our lab Start simulation begins a fresh replay; clicking a key dispatches a different event.",
            'on start { write("ECU ready"); }',
        ),
        section(
            "Logs versus frames",
            "write() adds text to the Write window. output(message) submits a frame for transmission. A log saying 'sent' is not evidence that a frame was transmitted.",
        ),
        section(
            "CANoe workflow",
            "Configure a node in Simulation Setup, compile its CAPL, start measurement, then inspect Write and Trace. Graphics is useful for signal trends. This app has no physical CAN hardware or arbitration simulation.",
        ),
        section(
            "Interview reasoning",
            "Investigate preconditions → stimulus → communication → timing → verdict. A frame visible in Trace does not establish ECU application acceptance.",
        ),
    ],
    FOUNDATION,
    challenge="Start with exactly two logs: ECU booting, then ECU ready.",
    example='on start { write("ECU ready"); }',
)

module(
    2,
    "Multiple messages",
    "Follow statement execution order.",
    "Print exactly two messages in this order: Starting ECU, then System ready.",
    'on start { write("First message"); write("Second message"); }',
    [
        section(
            "Execution order",
            "Statements in a handler run sequentially. Their order matters for logs, byte assignments and output snapshots.",
        ),
        section(
            "Snapshots",
            "output() captures the payload at that call. Later assignments do not alter a previously captured transmission.",
            'write("First");\nwrite("Second");',
        ),
        section(
            "Test evidence",
            "An exact sequence check rejects extra entries and reversed order. Match the requirement rather than checking whether the expected text appears somewhere.",
        ),
    ],
    [
        question(
            "order",
            'What does write("A"); write("B"); produce?',
            ["A then B", "B then A", "One CAN frame"],
            0,
            "Statements execute in source order within the handler.",
            "Execution order",
        ),
        question(
            "extra",
            "Requirement: exactly A then B. Observed: A,B,C. Verdict?",
            ["PASS", "FAIL", "Always ignore C"],
            1,
            "Exactly means additional output is a mismatch.",
            "Requirement checking",
        ),
        question(
            "snapshot",
            "Set byte 0 to 1; output; set it to 2; output. Which payloads?",
            ["1 then 2", "2 then 2", "No payloads"],
            0,
            "Each output captures its own snapshot.",
            "CAPL transmission",
        ),
        question(
            "log",
            "Two write calls create how many CAN transmissions?",
            ["Two", "Zero", "One"],
            1,
            "write creates logs, not CAN traffic.",
            "CAPL transmission",
        ),
    ],
    challenge="Print Boot, Ready, Running, in exactly that order.",
)

module(
    3,
    "Keyboard events",
    "Trigger the correct event rather than just starting measurement.",
    "Write an on key 'a' event that prints exactly one message: Key A pressed",
    "on key 'a' { write(\"Your message\"); }",
    [
        section(
            "Event selection",
            "on key 'a' runs for lowercase a. Starting measurement does not execute this handler. Key A and key a differ.",
        ),
        section(
            "CANoe interaction",
            "In CANoe, keyboard events require keyboard input reaching the measurement environment. Our Press A button explicitly dispatches lowercase a.",
            "on key 'a' { write(\"Key A pressed\"); }",
        ),
        section(
            "Isolation",
            "The basic Run operation is stateless. The advanced virtual-clock lab replays a history to preserve state across actions. Editing code starts a new history.",
        ),
    ],
    [
        question(
            "key-start",
            "Does starting measurement trigger on key 'a'?",
            ["Yes", "No", "Only with write()"],
            1,
            "Startup and keyboard dispatch are different events.",
            "Event dispatch",
        ),
        question(
            "case",
            "Which key matches on key 'a'?",
            ["lowercase a", "uppercase A", "Any key"],
            0,
            "The selector is case-sensitive in this subset.",
            "Event dispatch",
        ),
        question(
            "handler",
            "When does a keyboard handler execute?",
            ["When its matching event occurs", "Continuously", "When declared"],
            0,
            "Declarations do not execute the event body.",
            "Event dispatch",
        ),
        question(
            "trigger",
            "Which action proves a keyboard handler works?",
            [
                "Press the matching key and inspect evidence",
                "Read only its source",
                "Start PostgreSQL",
            ],
            0,
            "Exercise the intended event and verify results.",
            "Test design",
        ),
    ],
    challenge="Use key b to print Key B pressed. Starting must remain silent.",
)

module(
    4,
    "Transmit vehicle speed",
    "Build real payload evidence for the 100 → 50 km/h exercise.",
    "On key a, transmit exactly two ID 0x123 frames, DLC 2: 10 27 then 88 13. Logs alone do not pass.",
    SPEED.replace("0x10", "0x00")
    .replace("0x27", "0x00")
    .replace("0x88", "0x00")
    .replace("0x13;", "0x00;"),
    [
        section(
            "Classical standard CAN",
            "Standard data identifiers are 11 bits, 0x000–0x7FF; Classical CAN carries 0–8 bytes. Between competing standard data frames a lower numeric ID wins arbitration. An ID is not a destination address.",
        ),
        section(
            "Signal definition",
            "Our speed occupies bytes 0–1, unsigned little-endian, factor 0.01 km/h and offset 0. This is our own definition, not a universal CAN rule.",
            "raw = byte0 + 256 × byte1\nphysical = raw × factor + offset\n10 27 → 10000 → 100 km/h\n88 13 → 5000 → 50 km/h",
        ),
        section(
            "CAPL transmission",
            "Declare the message, set its DLC and bytes, then call output(). Use Trace for Tx evidence and Write for text logs. Our simulated Tx has no physical bus ACK or arbitration.",
        ),
    ],
    [
        *FOUNDATION[:3],
        question(
            "dlc",
            "How many data bytes are transmitted with DLC 2?",
            ["2", "8", "16"],
            0,
            "For our Classical CAN data frame DLC 2 denotes two bytes.",
            "CAN payload",
        ),
        question(
            "id",
            "Largest standard 11-bit identifier?",
            ["0x7FF", "0x800", "0xFFFF"],
            0,
            "Eleven bits represent 0 through 2047.",
            "CAN identifiers",
        ),
    ],
    challenge="On key a, send ID 0x123, DLC 2, for 25 km/h then 75 km/h. No extra transmissions.",
    example=SPEED,
)

module(
    5,
    "Multiple events and state",
    "Initialize once, then update persistent state on input.",
    "Initialize Status DLC in on start. Each a increments count and transmits ID 0x200 with count in its one-byte payload: 1,2,3.",
    STATE.replace("count++;", "// Update count here"),
    [
        section(
            "State lifetime",
            "Global values persist during a measurement. on start initializes them; each key handler uses the updated value. Resetting the virtual simulation starts from declarations again.",
        ),
        section(
            "Replay model",
            "The browser submits code plus action history. The server deterministically rebuilds state from time zero. State is not shared with other browser tabs and is not a database record.",
        ),
        section(
            "Multiple handlers",
            "Several events may coexist. The supported interpreter allows integer/byte scalars, message objects, if/else, arithmetic, comparisons, and declared msTimer timers. It has no loops, custom functions, arrays or general CAPL compiler.",
            STATE,
        ),
    ],
    [
        question(
            "state",
            "After three a events with count++ from zero, count is?",
            ["3", "1", "0"],
            0,
            "Global state persists between events in one simulation.",
            "Persistent state",
        ),
        question(
            "reset",
            "What resets our virtual measurement?",
            ["Start simulation", "Switching Theory/Practice", "Reading a frame"],
            0,
            "Start explicitly creates a fresh replay.",
            "Simulation lifecycle",
        ),
        question(
            "init",
            "Where should one-time message initialization go?",
            ["on start", "Every log", "A DBC comment"],
            0,
            "on start is the startup handler.",
            "Initialization",
        ),
        question(
            "scope",
            "Does our replay make two browsers share ECU state?",
            ["No", "Yes", "Only at DLC 8"],
            0,
            "Each request's history is independent.",
            "Simulation lifecycle",
        ),
    ],
    challenge="Count upward by 2 per key a; transmit ID 0x200 one-byte payloads 2,4,6.",
    example=STATE,
)

module(
    6,
    "Timers and periodic traffic",
    "Reschedule a one-shot timer to produce periodic messages.",
    "Transmit ID 0x300 data 01 at 100,200,300 ms. Key s cancels the timer. Key r restarts after a fresh 100 ms.",
    PERIODIC.replace(
        "  setTimer(heartbeat, 100);\n}\non key",
        "  // Rearm the timer here\n}\non key",
        1,
    ),
    [
        section(
            "One-shot timers",
            "An msTimer expires once. Periodic transmission requires setTimer in its handler. Calling setTimer again replaces the timer's next due time; cancelTimer removes it.",
        ),
        section(
            "Virtual time",
            "Advance time runs all due timers in timestamp order. At equal timestamps timers use scheduling order. A timer due at the advance boundary fires before the next key or receive action. This is our explicit lab rule, not a universal CANoe scheduling guarantee.",
        ),
        section(
            "Trace evidence",
            "Inspect successive Tx timestamps. A 100 ms requirement means a 100 ms interval, not merely three frames. No wall-clock sleeping is used.",
            PERIODIC,
        ),
    ],
    [
        question(
            "oneshot",
            "Does msTimer automatically repeat?",
            ["No", "Yes", "Only on CAN FD"],
            0,
            "Explicitly rearm it for periodic behavior.",
            "Timers",
        ),
        question(
            "rearm",
            "Where do you rearm a periodic timer?",
            ["In its on timer handler", "In every quiz", "In the DBC"],
            0,
            "The next interval is scheduled from the timer event.",
            "Timers",
        ),
        question(
            "period",
            "Tx times 100,200,300 ms indicate what interval?",
            ["100 ms", "300 ms", "200 ms"],
            0,
            "Subtract neighboring timestamps.",
            "Timing",
        ),
        question(
            "cancel",
            "cancelTimer does what?",
            ["Removes the pending expiry", "Erases all trace rows", "Stops PostgreSQL"],
            0,
            "It cancels that timer, not the whole measurement.",
            "Timers",
        ),
    ],
    challenge="Use a 50 ms period with the same stop/restart keys. Check both first delay and repeat interval.",
    example=PERIODIC,
)

module(
    7,
    "Reception and watchdogs",
    "Detect silence after the last received message.",
    "Arm a 500 ms watchdog at startup; rearm on each 0x300 reception. Log Communication timeout once after silence; receiving again clears timedOut.",
    WATCHDOG.replace(
        "  setTimer(watchdog, 500);\n}\non timer",
        "  // Rearm on reception here\n}\non timer",
        1,
    ),
    [
        section(
            "Reception",
            "on message 0x300 responds to injected Rx frames. Our own Tx frames do not automatically loop back into reception. this.byte(index) is read-only and guarded by received DLC.",
        ),
        section(
            "Watchdog",
            "If the final reception is at 200 ms and timeout is 500 ms, expiry is at 700 ms. A flag set once cannot monitor later loss. Rearm on reception rather than merely arming once at startup.",
        ),
        section(
            "Recovery and boundaries",
            "The lab sets timedOut=0 on reception and 1 on expiry. An Rx action after advancing exactly to a timer deadline occurs after that timer fired; design boundary checks accordingly.",
            WATCHDOG,
        ),
    ],
    [
        question(
            "deadline",
            "Last Rx at 200 ms; watchdog 500 ms. Expiry?",
            ["700 ms", "500 ms", "200 ms"],
            0,
            "The deadline is measured from the last rearm.",
            "Watchdogs",
        ),
        question(
            "restart",
            "What should a reception watchdog do on valid reception?",
            ["Rearm its deadline", "Only set a permanent flag", "Print PASS"],
            0,
            "Rearming monitors future silence.",
            "Watchdogs",
        ),
        question(
            "txrx",
            "Does our own output automatically invoke on message?",
            ["No", "Yes", "Only if write exists"],
            0,
            "Our lab deliberately separates injected Rx from Tx.",
            "Reception",
        ),
        question(
            "read",
            "A received frame has DLC 1. Can this.byte(1) safely be read?",
            ["No, check DLC first", "Always", "Only in hexadecimal"],
            0,
            "Index 1 is outside this payload.",
            "DLC validation",
        ),
    ],
    challenge="Implement the same watchdog with a 300 ms timeout and recovery.",
    example=WATCHDOG,
)

module(
    8,
    "Signals and DBC",
    "Decode bytes with a stated signal definition.",
    "Configure an unsigned two-byte signal at byte 0 so 10 27 decodes to 100 km/h and 88 13 to 50 km/h.",
    "",
    [
        section(
            "DBC fields",
            "A signal definition specifies start bit, bit length, byte order, signedness, factor, offset and unit. The supplied VehicleSpeed.dbc has a 16-bit little-endian signal starting at bit 0.",
        ),
        section(
            "Conversion",
            "physical = raw × factor + offset. Intel little-endian means the first byte contains the least significant part for this byte-aligned example. Motorola DBC start-bit numbering has additional rules; our decoder supports only byte-aligned unsigned fields, not arbitrary DBC parsing.",
        ),
        section(
            "Debugging",
            "Wrong byte order, wrong factor or wrong offset can produce plausible but incorrect values. Validate at several known values, including boundaries.",
            "100 km/h → raw 10000 → bytes 10 27\n50 km/h → raw 5000 → bytes 88 13",
        ),
    ],
    [
        FOUNDATION[1],
        question(
            "scale",
            "Raw 100, factor 0.5, offset -10 gives?",
            ["40", "50", "90"],
            0,
            "100 × 0.5 − 10 = 40.",
            "Scaling",
        ),
        question(
            "dbc",
            "Does a DBC normally define physical signal conversion?",
            ["Yes", "No", "Only for logging text"],
            0,
            "DBC metadata defines interpretation, not raw CAN itself.",
            "DBC",
        ),
        question(
            "endian",
            "Unsigned byte-aligned big-endian bytes 13 88 represent?",
            ["5000", "34835", "1388 decimal"],
            0,
            "0x1388 = 5000.",
            "Byte order",
        ),
    ],
    kind="signals",
    challenge="Decode a big-endian two-byte field with factor 0.1 and offset -10; validate 03 E8 → 90 and 01 F4 → 40.",
)

module(
    9,
    "E2E integrity and sequence",
    "Separate CRC integrity from counter acceptance.",
    "Classify each frame under the stated modulo-16 teaching profile with zero lost-frame tolerance.",
    "",
    [
        section(
            "Two CRC layers",
            "CAN's link-layer CRC differs from an application CRC carried in the payload. An application CRC can pass while the receiver rejects a repeated or out-of-window counter.",
        ),
        section(
            "Teaching profile",
            "Our explicit toy profile uses modulo 16, a two-byte big-endian Data ID, one counter byte and supplied data bytes. CRC-8 uses polynomial 0x1D, init 0xFF, no reflection, xorout 0xFF. This is not an AUTOSAR E2E profile or certification implementation.",
        ),
        section(
            "Acceptance",
            "The first good CRC establishes the accepted baseline. Delta=(counter-lastAccepted) modulo 16. Delta 0 is REPEATED. Delta 1 is OK. Deltas up to maxLost+1 are OK_SOME_LOST; larger deltas are WRONG_SEQUENCE. Rejected frames do not advance our accepted baseline.",
        ),
        section(
            "Investigate",
            "Inspect payload, counter, application CRC and timestamps. Consider two transmitters with the same ID or a replay. Never assume all 4-bit AUTOSAR counters wrap modulo 16; actual rules are profile-specific.",
            "Toy example: 15 → 0 is delta 1\n5 → 6 → 7 → 7 → 8 contains a repeated 7",
        ),
    ],
    [
        FOUNDATION[3],
        question(
            "wrap",
            "In this modulo-16 toy profile, 15 → 0 has delta?",
            ["1", "0", "15"],
            0,
            "(0 − 15) modulo 16 = 1. Other profiles may use other counter ranges.",
            "Counter wraparound",
        ),
        question(
            "lost",
            "Last accepted 6, next 8, maxLost=1. Classification?",
            ["OK_SOME_LOST", "REPEATED", "WRONG_CRC"],
            0,
            "Delta 2 means one missed frame and is allowed by this requirement.",
            "Lost-message tolerance",
        ),
        question(
            "crcbase",
            "Does a wrong-CRC frame update our accepted baseline?",
            ["No", "Yes", "Only if its counter is larger"],
            0,
            "Rejected data does not become the accepted reference in this toy state machine.",
            "E2E sequence",
        ),
    ],
    kind="e2e",
    challenge="Classify a new sequence with maxLost=1. Include duplicate, bad CRC, loss tolerance, and recovery.",
)

module(
    10,
    "Test verdicts and deadlines",
    "Verify the required response rather than a stale state.",
    "Select event-based checking with a 100 ms deadline. It must accept 80 ms, reject 120 ms and reject no response.",
    "",
    [
        section(
            "Test structure",
            "Preconditions → stimulus → bounded response wait → verification → verdict. A missing precondition makes this lab NOT_EXECUTED; it is not evidence that the ECU passed or failed.",
        ),
        section(
            "Fresh observations",
            "Observations are timestamped relative to the command. This lab treats supplied samples as fresh observations, not cached states from before the stimulus. At the deadline, an observation exactly at the boundary is accepted by our stated requirement.",
        ),
        section(
            "CAPL Test Modules",
            'CANoe test functions include bounded waits and verdict reporting. write("PASS") is merely a log; testStepPass/testStepFail affect reports. These functions are discussed in theory; this app\'s Test Bench is a separate teaching model, not a CAPL Test Module interpreter.',
        ),
        section(
            "ACC false failures",
            "If activation arrives at 80 ms within a 100 ms requirement, an immediate read can fail incorrectly. A 500 ms delay also does not prove the deadline was respected.",
        ),
    ],
    [
        FOUNDATION[4],
        question(
            "writepass",
            'Does write("PASS") set a CANoe test verdict?',
            ["No", "Yes", "Only with CRC OK"],
            0,
            "Use the appropriate test reporting API, not a console string.",
            "Verdicts",
        ),
        question(
            "late",
            "Deadline 100 ms; response 120 ms. Verdict?",
            ["FAIL", "PASS", "Ignore timestamps"],
            0,
            "Correct state after the allowed deadline is late.",
            "Deadlines",
        ),
        question(
            "precondition",
            "ECU is not READY before the test. What is justified?",
            [
                "Report setup/precondition failure",
                "PASS the ECU",
                "Assume an ECU response defect",
            ],
            0,
            "Do not confuse invalid setup with failed behavior under valid preconditions.",
            "Test preconditions",
        ),
    ],
    kind="verdict",
    challenge="Use the same approach for a 150 ms deadline; cover boundary, late, absent and invalid-setup cases.",
)

module(
    11,
    "ADAS scenario reasoning",
    "Connect trace evidence to ACC and AEB requirements.",
    "Classify braking decisions for the four simplified AEB cases under the stated 2-second TTC threshold.",
    "",
    [
        section(
            "Abbreviations",
            "ADAS: Advanced Driver Assistance Systems. ACC: Adaptive Cruise Control. AEB: Automatic Emergency Braking. FCW: Forward Collision Warning. TTC: Time To Collision. HIL/SIL/MIL: Hardware/Software/Model in the Loop.",
        ),
        section(
            "TTC model",
            "For constant velocities on the same path with positive closing speed: TTC=distance/closingSpeed. Convert km/h to m/s by dividing by 3.6. If there is no positive closing speed, this model has no finite collision time.",
        ),
        section(
            "Explicit AEB rule",
            "This lab requests braking only when sensors are valid, an obstacle is on path, closing speed is positive, and TTC ≤ configured threshold. Invalid sensors produce DEGRADED. This is a deliberately simplified offline teaching model, not a production control algorithm or driving guidance.",
        ),
        section(
            "ACC model",
            "Our state demonstration is OFF when disabled, DEGRADED with invalid sensing, OVERRIDDEN with driver braking and ACTIVE otherwise. Actual activation conditions, priorities and fallback behavior are OEM-specific.",
        ),
        section(
            "Failure investigation",
            "False positive: intervention without the specified hazard. False negative: missing required intervention. Define the requirement and timing before judging either. Expand real validation with sensor uncertainty, cut-in/out, stationary targets, curves and driver override.",
        ),
    ],
    [
        question(
            "ttc",
            "20 m gap and closing speed 10 m/s gives TTC?",
            ["2 s", "0.5 s", "200 s"],
            0,
            "20/10 = 2 seconds for constant positive closing speed.",
            "TTC",
        ),
        question(
            "units",
            "36 km/h equals?",
            ["10 m/s", "36 m/s", "3.6 m/s"],
            0,
            "Divide km/h by 3.6.",
            "Units",
        ),
        question(
            "fp",
            "Braking without the specified hazard is called?",
            ["False positive", "False negative", "Always safe"],
            0,
            "An unwanted intervention is a false positive relative to the requirement.",
            "ADAS scenarios",
        ),
        question(
            "invalid",
            "What does our lab report for invalid sensors?",
            ["DEGRADED", "Guaranteed safe", "Always brake"],
            0,
            "The simplified model explicitly reports unavailable/invalid input.",
            "ADAS scenarios",
        ),
    ],
    kind="adas",
    challenge="Classify four new cases at a 1.5-second threshold, including no closing speed and an invalid sensor.",
)


# Numeric variants provide more than a reordering of the same four questions.
for module_id in (4, 8):
    for index, speed in enumerate((10, 20, 30, 40, 60, 80, 90, 120)):
        raw = speed * 100
        byte_text = f"{raw & 255:02X} {raw >> 8:02X}"
        options = [f"{speed} km/h", f"{speed * 2} km/h", f"{speed / 10:g} km/h"]
        correct = index % 3
        options[0], options[correct] = options[correct], options[0]
        MODULES[module_id]["quiz_bank"].append(
            question(
                f"speed-{speed}",
                f"Unsigned little-endian bytes {byte_text}, factor 0.01, offset 0. Speed?",
                options,
                correct,
                f"Raw {raw}; {raw} × 0.01 = {speed} km/h. Byte 0 is least significant.",
                "Signal encoding",
            )
        )
for period in (20, 50, 80, 100, 200):
    MODULES[6]["quiz_bank"].append(
        question(
            f"period-{period}",
            f"Tx timestamps are {period}, {period * 2}, {period * 3} ms. What is the interval?",
            [f"{period} ms", f"{period * 3} ms", "Cannot subtract timestamps"],
            0,
            f"Adjacent timestamps differ by {period} ms.",
            "Timing",
        )
    )
for previous in (13, 14, 15):
    following = (previous + 2) % 16
    MODULES[9]["quiz_bank"].append(
        question(
            f"loss-{previous}",
            f"Toy modulo-16 profile: last accepted {previous}, next {following}, valid CRC, maxLost=1. Status?",
            ["OK_SOME_LOST", "REPEATED", "WRONG_CRC"],
            0,
            "Modulo delta is 2, which allows one missing frame under this stated rule.",
            "Lost-message tolerance",
        )
    )

INTERVIEW_PROMPTS = {
    1: "How would you prove that an ECU sent a CAN frame rather than merely logging a message?",
    2: "Explain how you would diagnose an incorrect sequence of transmissions.",
    3: "Explain why an on key handler remains silent at measurement startup.",
    4: "Explain the complete path from 100 km/h to a CAN frame and back to a decoded signal.",
    5: "What is initialized once and what changes on each keyboard event?",
    6: "Why does a one-shot timer not generate periodic traffic automatically?",
    7: "A message stops after two seconds. Explain a robust 500 ms communication watchdog.",
    8: "A decoded speed looks plausible but is wrong. How do you check the signal definition?",
    9: "CRC passes for every frame but counter 7 repeats. Explain your CANoe investigation.",
    10: "ACC activates after 80 ms, but the test fails intermittently. How do you fix the test?",
    11: "How would you distinguish AEB false positives from false negatives using requirements and evidence?",
}
for module_id, prompt in INTERVIEW_PROMPTS.items():
    MODULES[module_id]["interview_prompt"] = prompt


MODULES[1]["theory"].extend(
    [
        section(
            "CRC versus sequence",
            "A valid application CRC does not prove that a counter sequence is acceptable. If duplicates are forbidden, 5,6,7,7,8 fails the sequence rule. Our later E2E lab states its own modulo-16 toy rules explicitly.",
        ),
        section(
            "Response deadlines",
            "For an ACC response required within 100 ms, wait for a fresh qualifying ACTIVE observation with that deadline. An immediate read may be stale, while a fixed delay alone does not establish a correct verdict.",
        ),
    ]
)
ADVANCED_QUESTIONS = {
    6: [
        question(
            "timer-fault",
            "A timer is armed only in on start. Its handler sends one frame but never rearms. What happens after the first expiry?",
            [
                "Only one frame is sent",
                "It repeats forever",
                "It automatically uses the CAN cycle time",
            ],
            0,
            "msTimer is one-shot. Periodic behavior requires an explicit rearm.",
            "Timer debugging",
        ),
        question(
            "timer-replace",
            "A timer is set for 500 ms at t=0, then reset to 500 ms at t=200. Next expiry?",
            ["700 ms", "500 ms", "200 ms"],
            0,
            "The reset replaces the pending expiry with now+500.",
            "Timer debugging",
        ),
    ],
    7: [
        question(
            "flag-fault",
            "messageReceived is set to 1 on the first Rx and never reset. A single startup timer checks it at 500 ms. Can this detect traffic loss after two seconds?",
            [
                "No; monitoring has already ended",
                "Yes, the flag tracks every gap",
                "Yes, if CRC is valid",
            ],
            0,
            "The one-shot check saw the flag set. No future deadline is scheduled, so later silence is unobserved.",
            "Watchdog debugging",
        ),
        question(
            "wrong-id",
            "A 0x300 watchdog is reset by every frame regardless of ID. What defect can occur?",
            [
                "Unrelated traffic masks missing 0x300",
                "Timeout is always early",
                "No possible defect",
            ],
            0,
            "Rearm only on the reception relevant to the monitored requirement.",
            "Watchdog debugging",
        ),
    ],
    9: [
        question(
            "two-sources",
            "All application CRCs pass, but counters alternate 1,8,2,9. What should you investigate?",
            [
                "Possible two transmitters sharing an ID",
                "Only the UI theme",
                "Assume CRC proves sequence correctness",
            ],
            0,
            "Inspect source configuration, payloads, timestamps, sequence windows and possible replay. This pattern alone does not prove a unique root cause.",
            "E2E debugging",
        ),
        question(
            "profile-limit",
            "Can the toy modulo-16 checker be presented as an AUTOSAR Profile 1 implementation?",
            ["No", "Yes, because both use a CRC", "Yes, if DLC is 8"],
            0,
            "Counter ranges, CRC inputs, Data ID handling and state-machine rules are profile-specific.",
            "E2E profiles",
        ),
    ],
    10: [
        question(
            "cached-state",
            "ACC_State was already ACTIVE before your command. Does reading ACTIVE immediately prove this command caused activation?",
            [
                "No; require fresh causal response evidence",
                "Yes, always",
                "Only if write prints PASS",
            ],
            0,
            "A cached state does not establish the response to the new stimulus; define valid preconditions and observation semantics.",
            "Freshness and causality",
        ),
        question(
            "fixed-wait",
            "The requirement allows 100 ms but a test sleeps 500 ms then reads ACTIVE. What has not been established?",
            [
                "That activation occurred within 100 ms",
                "The final state",
                "Whether 500 is larger than 100",
            ],
            0,
            "A final correct state after a long wait can hide a late response.",
            "Test timing",
        ),
    ],
    11: [
        question(
            "units-debug",
            "An engineer divides a 20 m gap by a closing speed of 36 km/h and reports 0.56 s. What is wrong?",
            [
                "Convert 36 km/h to 10 m/s; TTC is 2 s",
                "No error",
                "Multiply the distance by DLC",
            ],
            0,
            "Distance and speed need compatible units before division.",
            "Scenario units",
        ),
        question(
            "requirement-first",
            "An AEB intervention occurs in a cut-in scenario. What is needed before labeling it a false positive?",
            [
                "The applicable hazard, path and timing requirements",
                "Only a log saying Brake",
                "Only the CAN identifier",
            ],
            0,
            "A verdict depends on the defined scenario and requirements; the event alone is not sufficient.",
            "ADAS verdicts",
        ),
    ],
}
for module_id, extra in ADVANCED_QUESTIONS.items():
    MODULES[module_id]["quiz_bank"].extend(extra)


def public_modules():
    result = []
    for entry in MODULES.values():
        item = deepcopy(entry)
        item.pop("quiz_bank")
        result.append(item)
    return result
