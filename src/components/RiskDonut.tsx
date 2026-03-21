import type { RiskSummary } from '../types/risk';

interface RiskDonutProps {
  summary: RiskSummary;
}

const segments = [
  { key: 'high', label: 'High', color: '#ef4444', glowColor: 'rgba(239,68,68,0.3)' },
  { key: 'medium', label: 'Medium', color: '#f59e0b', glowColor: 'rgba(245,158,11,0.25)' },
  { key: 'low', label: 'Low', color: '#10b981', glowColor: 'rgba(16,185,129,0.2)' },
] as const;

export default function RiskDonut({ summary }: RiskDonutProps) {
  const counts = [summary.highCount, summary.mediumCount, summary.lowCount];
  const total = counts.reduce((a, b) => a + b, 0);

  // SVG donut math
  const cx = 80, cy = 80, r = 62;
  const circumference = 2 * Math.PI * r;
  const gap = 4; // gap in pixels between segments
  const totalGap = gap * segments.length;
  const availableLength = circumference - totalGap;

  let offset = -circumference / 4; // start at top (12 o'clock)

  const arcs = segments.map((seg, i) => {
    const count = counts[i];
    const pct = total > 0 ? count / total : 0;
    const segLength = pct * availableLength;
    const dasharray = `${segLength} ${circumference - segLength}`;
    const dashoffset = -offset;
    offset += segLength + gap;
    return { ...seg, count, pct, dasharray, dashoffset, segLength };
  });

  return (
    <div className="card-base p-6 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(168,85,247,0.1)' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 2a10 10 0 0 1 10 10" />
          </svg>
        </div>
        <h3 className="font-heading text-[13px] font-bold uppercase tracking-[2px] text-text-secondary">
          Risk Distribution
        </h3>
        <div className="flex-1 h-px bg-section-line ml-2" />
      </div>

      {/* Donut + Legend */}
      <div className="flex items-center justify-center gap-8 flex-1">
        {/* SVG Donut */}
        <div className="relative">
          <svg width="160" height="160" viewBox="0 0 160 160">
            {/* Track */}
            <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="14" />

            {/* Segments */}
            {arcs.map((arc) => (
              <circle
                key={arc.key}
                cx={cx}
                cy={cy}
                r={r}
                fill="none"
                stroke={arc.color}
                strokeWidth="14"
                strokeDasharray={arc.dasharray}
                strokeDashoffset={arc.dashoffset}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
                style={{ filter: `drop-shadow(0 0 4px ${arc.glowColor})` }}
              />
            ))}
          </svg>

          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-mono text-[28px] font-medium text-text-primary leading-none">
              {total}
            </span>
            <span className="text-[9px] uppercase tracking-[2px] text-text-dim mt-1">
              Total
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-col gap-4">
          {arcs.map((arc) => (
            <div key={arc.key} className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: arc.color, boxShadow: `0 0 6px ${arc.glowColor}` }} />
              <div className="flex flex-col">
                <span className="font-mono text-[18px] font-medium text-text-primary leading-none">
                  {arc.count}
                </span>
                <span className="text-[9px] uppercase tracking-wider text-text-dim mt-0.5">
                  {arc.label}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
