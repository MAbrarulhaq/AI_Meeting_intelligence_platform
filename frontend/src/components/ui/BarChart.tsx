interface BarChartDatum {
  label: string;
  value: number;
}

interface BarChartProps {
  data: BarChartDatum[];
  /** Formats the value shown above each bar. */
  formatValue?: (value: number) => string;
  height?: number;
}

/**
 * A plain horizontal-axis bar chart, built from a handful of <rect>s.
 * Deliberately not a charting library — the data here is a handful of
 * points at most, and this keeps the visual language (color, radius,
 * type) identical to the rest of the app.
 */
export function BarChart({ data, formatValue, height = 160 }: BarChartProps) {
  if (data.length === 0) return null;

  const max = Math.max(...data.map((d) => d.value), 1);
  const barWidth = 100 / data.length;

  return (
    <div className="bar-chart" style={{ height }}>
      {data.map((d) => {
        const barHeight = Math.max((d.value / max) * 100, d.value > 0 ? 4 : 0);
        return (
          <div className="bar-chart-col" key={d.label} style={{ width: `${barWidth}%` }}>
            <span className="bar-chart-value">{formatValue ? formatValue(d.value) : d.value}</span>
            <div className="bar-chart-track">
              <div className="bar-chart-bar" style={{ height: `${barHeight}%` }} />
            </div>
            <span className="bar-chart-label">{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}
