// These presets populate the CAPL editor. FastAPI runs the selected source
// against the user's actions, such as injecting a frame or advancing the clock.
export const programs = {
  // Relay the two received bytes under a different CAN ID so both
  // the incoming frame and the resulting transmission appear in Trace.
  relay: {
    label: "Receive and transmit",
    hint: "Start measurement, then inject ID 120 with bytes 10 27. Advance 100 ms and inject 88 13 to see the speed change.",
    code: `variables {
  message 0x123 VehicleSpeed;
}

on start {
  VehicleSpeed.dlc = 2;
  write("Speed relay ready");
}

on message 0x120 {
  VehicleSpeed.byte(0) = this.byte(0);
  VehicleSpeed.byte(1) = this.byte(1);
  output(VehicleSpeed);
}`,
  },

  // Isolate transmission from reception: pressing 'a' sends a known
  // payload that the sample DBC decodes as 100 km/h.
  transmit: {
    label: "Transmit on key",
    hint: "Start measurement and send key a to transmit ID 0x123.",
    code: `variables {
  message 0x123 VehicleSpeed;
}

on key 'a' {
  VehicleSpeed.dlc = 2;
  VehicleSpeed.byte(0) = 0x10;
  VehicleSpeed.byte(1) = 0x27;
  output(VehicleSpeed);
}`,
  },

  // CAPL timers in this simulator are one-shot. The handler rearms
  // the timer after each transmission to produce a 100 ms interval.
  timer: {
    label: "Periodic timer",
    hint: "Start measurement and advance 300 ms. The trace should show a frame every 100 ms.",
    code: `variables {
  message 0x123 VehicleSpeed;
  msTimer heartbeat;
}

on start {
  VehicleSpeed.dlc = 2;
  VehicleSpeed.byte(0) = 0x88;
  VehicleSpeed.byte(1) = 0x13;
  setTimer(heartbeat, 100);
}

on timer heartbeat {
  output(VehicleSpeed);
  setTimer(heartbeat, 100);
}`,
  },
};

// Reference code for a Vector CANoe Test Module. The Workbench evaluates
// its own test conditions through checkTrace(), using the simulated frames.
export const testModuleExample = `void MainTest()
{
  CheckSpeedFrame();
}

testcase CheckSpeedFrame()
{
  // Arrange for the SpeedECU to publish VehicleSpeed.
  // VehicleSpeed is a database message in the CANoe configuration.
  if (TestWaitForMessage(VehicleSpeed, 100) == 1)
    TestStepPass("RX", "VehicleSpeed received within 100 ms");
  else
    TestStepFail("RX", "VehicleSpeed missing or wait failed");
}`;

const messageLine = /^BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s+\w+/;
const signalLine =
  /^SG_\s+(\w+)\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*\(\s*([^,]+),\s*([^)]+)\)\s*\[[^\]]+\]\s*"([^"]*)"/;

export function parseDbc(source) {
  // Each SG_ belongs to the most recent BO_ declaration. Store that
  // message with the signal so decoding can match frames by CAN ID.
  let message;
  const signals = new Map();
  const identifiers = new Set();
  for (const [index, raw] of source.split(/\r?\n/).entries()) {
    const line = raw.trim();
    const fail = (reason) => {
      throw new Error(`DBC line ${index + 1}: ${reason}`);
    };
    if (/^BO_\s/.test(line)) {
      const match = line.match(messageLine);
      if (!match) fail("Use BO_ <decimal ID> <name>: <DLC> <sender>.");
      const [, id, name, size] = match;

      // BO_ uses a decimal identifier. Workbench input and Trace display hex.
      const identifier = Number(id);
      const dlc = Number(size);
      if (identifier > 0x7ff || dlc > 8)
        fail("Use a standard 11-bit CAN ID and DLC up to 8.");
      if (identifiers.has(identifier)) fail("This CAN ID is already defined.");
      identifiers.add(identifier);
      message = { identifier, name, dlc };
    } else if (/^SG_\s/.test(line)) {
      const match = line.match(signalLine);
      if (!message || !match)
        fail("Add a non-multiplexed SG_ signal after its BO_ message.");
      const [, name, bit, width, order, sign, scale, intercept, unit] = match;
      const startBit = Number(bit);
      const length = Number(width) / 8;
      const little = order === "1";
      const start = Math.floor(startBit / 8);
      const factor = Number(scale);
      const offset = Number(intercept);

      // Intel names the least significant bit and Motorola names the most
      // significant bit. For whole-byte fields those positions are 0 and 7
      // within the starting byte. Six bytes keep the raw integer exact in JS.
      if (
        startBit % 8 !== (little ? 0 : 7) ||
        !Number.isInteger(length) ||
        length < 1 ||
        length > 6 ||
        start + length > message.dlc
      ) {
        fail(
          "Use a byte-aligned signal of 1–6 bytes contained within the message.",
        );
      }
      if (
        !Number.isFinite(factor) ||
        factor === 0 ||
        !Number.isFinite(offset)
      ) {
        fail("Factor must be finite and nonzero, and offset must be finite.");
      }

      // A signal name can recur under a different CAN message.
      const id = `${message.identifier}:${name}`;
      if (signals.has(id))
        fail("This signal name is already defined for the message.");
      signals.set(id, {
        id,
        name,
        message,
        start,
        length,
        little,
        signed: sign === "-",
        factor,
        offset,
        unit,
      });
    }
  }
  if (!signals.size)
    throw new Error("Add at least one BO_ message with an SG_ signal.");
  return [...signals.values()];
}

export function decodeSignal(frame, signal) {
  // The graph skips unrelated frames and frames with too few payload bytes.
  if (
    frame.identifier !== signal.message.identifier ||
    frame.data.length < signal.start + signal.length
  )
    return null;

  // Work on a copy so reversing Intel bytes leaves the original trace intact.
  // Accumulate the bytes from most significant to least significant.
  const bytes = frame.data.slice(signal.start, signal.start + signal.length);
  if (signal.little) bytes.reverse();
  let raw = bytes.reduce((value, byte) => value * 256 + byte, 0);

  // Interpret signed fields as two's complement before applying DBC scaling.
  const range = 2 ** (signal.length * 8);
  if (signal.signed && raw >= range / 2) raw -= range;
  const value = raw * signal.factor + signal.offset;
  return Number.isFinite(value) ? value : null;
}

export function canId(text) {
  const hex = text.trim().replace(/^0x/i, "");
  const identifier = Number.parseInt(hex, 16);

  // parseInt accepts a valid prefix of an invalid string. Validate the
  // entire input before accepting it as an 11-bit CAN identifier.
  if (!/^[0-9a-f]{1,3}$/i.test(hex) || identifier > 0x7ff) {
    throw new Error("Enter a standard CAN ID from 000 to 7FF in hex.");
  }
  return identifier;
}

export function checkTrace({
  measurement,
  origin,
  identifier,
  direction,
  deadline,
  payload,
}) {
  if (!measurement || !origin)
    return { verdict: "NOT EXECUTED", reason: "Start a measurement first." };

  // Several events can share a virtual timestamp. Start at the frame index
  // captured before the stimulus so an older response cannot satisfy the test.
  const frame = measurement.frames
    .slice(origin.frameIndex)
    .find(
      (candidate) =>
        candidate.time_ms >= origin.time &&
        candidate.identifier === identifier &&
        candidate.direction === direction &&
        (!payload ||
          (candidate.data.length === payload.length &&
            candidate.data.every((byte, index) => byte === payload[index]))),
    );
  if (frame) {
    const delay = frame.time_ms - origin.time;
    return delay <= deadline
      ? {
          verdict: "PASS",
          reason: `Matching frame after ${delay} ms (limit ${deadline} ms).`,
        }
      : {
          verdict: "FAIL",
          reason: `First matching frame arrived after ${delay} ms (limit ${deadline} ms).`,
        };
  }

  // Without a matching frame, the verdict stays pending until the virtual
  // clock reaches the deadline. Real time spent on the page does not count.
  const elapsed = measurement.time_ms - origin.time;
  return elapsed >= deadline
    ? { verdict: "FAIL", reason: `No matching frame within ${deadline} ms.` }
    : {
        verdict: "PENDING",
        reason: `Advance the clock by at least ${deadline - elapsed} ms to finish the wait.`,
      };
}
