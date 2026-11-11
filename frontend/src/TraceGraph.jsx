import { decodeSignal } from "./workbenchData";

const number = (value) => new Intl.NumberFormat("en", { maximumFractionDigits: 4 }).format(value);

export default function TraceGraph({ frames, time, signal }) {
  const samples = frames.flatMap((frame, index) => {
    const value = signal ? decodeSignal(frame, signal) : (frame.direction === "Tx" ? 1 : 0);
    return value === null ? [] : [{ ...frame, value, index }];
  });
  if (!samples.length) {
    return <p role="status">{signal ? `No trace samples for ${signal.name} yet.` : "Start a measurement and send or receive a frame."}</p>;
  }

  const xMax = Math.max(1, time);
  const values = samples.map(({ value }) => value);
  const yMin = signal ? Math.min(0, ...values) : 0;
  const yMax = signal ? Math.max(yMin + 1, ...values) : 1;
  const x = (value) => 76 + 620 * value / xMax;
  const y = (value) => 170 - 136 * (value - yMin) / (yMax - yMin);
  const yTicks = signal ? [yMin, (yMin + yMax) / 2, yMax] : [0, 1];
  const points = samples.map(({ time_ms, value }) => `${x(time_ms)},${y(value)}`).join(" ");
  const label = signal ? `${signal.name}${signal.unit ? ` (${signal.unit})` : ""}` : "CAN frame timeline";

  return <figure className="trace-figure">
    <svg className="trace-graph" viewBox="0 0 720 208" role="img" aria-label={`${label} over virtual time`}>
      <title>{label} over virtual time</title>
      {yTicks.map((tick) => <g key={tick}>
        <line className="chart-gridline" x1="76" y1={y(tick)} x2="696" y2={y(tick)} />
        <text x="68" y={y(tick) + 4} textAnchor="end">{signal ? number(tick) : (tick === 1 ? "Tx" : "Rx")}</text>
      </g>)}
      {[0, xMax / 2, xMax].map((tick) => <g key={tick}>
        <line className="chart-gridline" x1={x(tick)} y1="30" x2={x(tick)} y2="170" />
        <text x={x(tick)} y="193" textAnchor="middle">{number(tick)} ms</text>
      </g>)}
      {signal && <polyline points={points} fill="none" stroke="#83dfc1" strokeWidth="2" />}
      {samples.map(({ time_ms, value, direction, index, identifier }) => (
        <circle key={index} cx={x(time_ms)} cy={y(value)} r="5" className={direction === "Tx" ? "trace-tx" : "trace-rx"}>
          <title>{time_ms} ms · {direction} 0x{identifier.toString(16).toUpperCase()}{signal ? ` · ${number(value)} ${signal.unit}` : ""}</title>
        </circle>
      ))}
    </svg>
    <figcaption>{label} · {samples.length} samples{signal && ` · Last: ${number(samples.at(-1).value)} ${signal.unit}`}</figcaption>
  </figure>;
}
