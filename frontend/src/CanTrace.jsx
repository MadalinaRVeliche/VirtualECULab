import { useId, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function CanTrace({ frames, onInspectFrame, onClear }) {
  const uniqueId = useId();
  const traceTitleId = `${uniqueId}-trace-title`;
  const identifierId = `${uniqueId}-identifier`;
  const dataId = `${uniqueId}-data`;
  const [identifier, setIdentifier] = useState("123");
  const [data, setData] = useState("10 27");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function inspectFrame(event) {
    event.preventDefault();
    setError("");

    const idText = identifier.trim().replace(/^0x/i, "");
    const byteTexts = data.trim() ? data.trim().split(/\s+/) : [];

    if (!/^[0-9a-f]{1,3}$/i.test(idText)) {
      setError("Enter a hexadecimal identifier from 000 to 7FF.");
      return;
    }

    const id = Number.parseInt(idText, 16);

    if (id > 0x7ff) {
      setError("Standard CAN identifiers cannot exceed 7FF.");
      return;
    }

    if (
      byteTexts.length > 8 ||
      byteTexts.some((byte) => !/^[0-9a-f]{2}$/i.test(byte))
    ) {
      setError("Enter up to 8 hexadecimal bytes, such as 10 27.");
      return;
    }

    setBusy(true);

    try {
      const response = await fetch(`${API_URL}/can/frames/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          identifier: id,
          data: byteTexts.map((byte) => Number.parseInt(byte, 16)),
        }),
      });

      const frame = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof frame.detail === "string"
            ? frame.detail
            : "The frame could not be validated.",
        );
      }

      onInspectFrame(frame);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Cannot reach the backend."
          : err.message || "Frame preview failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="can-trace" aria-labelledby={traceTitleId}>
      <h2 id={traceTitleId}>CAN Trace</h2>
      <p>
        Inspect frame previews and simulated CAPL transmissions. Identifiers and
        payload bytes are displayed in hexadecimal.
      </p>

      <form onSubmit={inspectFrame}>
        <label htmlFor={identifierId}>CAN identifier (hex)</label>
        <input
          id={identifierId}
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          disabled={busy}
          autoComplete="off"
        />

        <label htmlFor={dataId}>Data bytes (hex)</label>
        <input
          id={dataId}
          value={data}
          onChange={(event) => setData(event.target.value)}
          disabled={busy}
          autoComplete="off"
        />

        <button type="submit" disabled={busy}>
          {busy ? "Validating..." : "Inspect frame"}
        </button>

        <button
          type="button"
          onClick={onClear}
          disabled={busy || frames.length === 0}
        >
          Clear trace
        </button>
      </form>

      {error && <p role="alert">{error}</p>}

      <p role="status">{frames.length} trace entries</p>

      <div className="trace-table-wrapper">
        <table>
          <caption>
            Local simulated trace; cleared when the page reloads. Timestamps are virtual lab time; — means unavailable.
          </caption>
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Source</th>
              <th scope="col">Time (ms)</th>
              <th scope="col">Identifier</th>
              <th scope="col">Type</th>
              <th scope="col">DLC</th>
              <th scope="col">Data (hex)</th>
            </tr>
          </thead>
          <tbody>
            {frames.map((frame, index) => (
              <tr key={frame.rowId}>
                <td>{index + 1}</td>
                <td>{frame.source}</td>
                <td>{frame.time_ms ?? "—"}</td>
                <td>{frame.identifier_hex}</td>
                <td>Standard data</td>
                <td>{frame.dlc}</td>
                <td>{frame.data_hex || "(empty)"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
