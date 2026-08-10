interface WaveformMarkProps {
  className?: string;
  /** Stroke/fill color. Defaults to currentColor so it inherits from its container. */
  color?: string;
}

/**
 * The product's signature visual: a spoken waveform on the left that
 * resolves into flat transcript lines on the right — literally what
 * the platform does to a meeting. Used on the auth brand panel and
 * the landing hero. Pure SVG, no external assets.
 */
function WaveformMark({ className, color = "currentColor" }: WaveformMarkProps) {
  const bars = [6, 14, 9, 22, 12, 26, 15, 20, 10, 17];
  const barGap = 7;
  const barWidth = 3;

  return (
    <svg
      className={className}
      viewBox="0 0 320 56"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {bars.map((h, i) => (
        <rect
          key={i}
          x={i * barGap}
          y={28 - h / 2}
          width={barWidth}
          height={h}
          rx={1.5}
          fill={color}
          opacity={0.55 + (i / bars.length) * 0.35}
        />
      ))}
      {/* transcript lines the waveform resolves into */}
      <line x1="150" y1="18" x2="300" y2="18" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity="0.9" />
      <line x1="150" y1="28" x2="278" y2="28" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity="0.65" />
      <line x1="150" y1="38" x2="292" y2="38" stroke={color} strokeWidth="2.5" strokeLinecap="round" opacity="0.4" />
    </svg>
  );
}

export default WaveformMark;
