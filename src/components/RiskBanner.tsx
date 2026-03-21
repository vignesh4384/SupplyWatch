import { Shield } from 'lucide-react';
import type { RiskSummary, RiskHistoryPoint } from '../types/risk';

interface RiskBannerProps {
  summary: RiskSummary;
  history: RiskHistoryPoint[];
}

const badgeStyle: Record<string, string> = {
  HIGH: 'bg-high-bg text-high-text border-high-border',
  MEDIUM: 'bg-medium-bg text-medium-text border-medium-border',
  LOW: 'bg-low-bg text-low-text border-low-border',
};

const trendColor: Record<string, string> = {
  HIGH: 'text-high-text',
  MEDIUM: 'text-medium-text',
  LOW: 'text-low-text',
};

export default function RiskBanner({ summary, history }: RiskBannerProps) {
  const pct = summary.overallScore;

  return (
    <div className="card-base p-6 flex flex-col h-full">
      {/* Top: Icon + Title */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
             style={{ background: 'rgba(124,58,237,0.1)' }}>
          <Shield size={16} color="#a78bfa" strokeWidth={2} />
        </div>
        <h3 className="font-heading text-[13px] font-bold uppercase tracking-[2px] text-text-secondary">
          Global Risk Score
        </h3>
        <div className="flex-1 h-px bg-section-line ml-2" />
      </div>

      {/* Score + Badge row */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-baseline gap-2.5">
          <span className="font-mono text-[44px] font-medium leading-none tracking-[-2px] text-text-primary">
            {summary.overallScore}
          </span>
          <span className="font-heading text-[10px] font-bold uppercase tracking-[2px] text-text-dim">
            / 100
          </span>
        </div>

        <div className={`flex items-center gap-1.5 px-4 py-2 rounded-xl border text-[11px] font-bold tracking-wider ${badgeStyle[summary.level]}`}>
          {summary.level} RISK
        </div>
      </div>

      {/* Gradient bar */}
      <div className="mb-4">
        <div className="relative h-2.5 rounded-full overflow-hidden bg-bar-track">
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-all duration-1000 ease-out"
            style={{
              width: `${pct}%`,
              background: 'linear-gradient(90deg, #10b981 0%, #34d399 25%, #fbbf24 50%, #f59e0b 70%, #ef4444 90%, #dc2626 100%)',
              boxShadow: pct >= 66
                ? '0 0 12px rgba(239,68,68,0.3)'
                : pct >= 41
                ? '0 0 10px rgba(245,158,11,0.25)'
                : '0 0 8px rgba(16,185,129,0.2)',
            }}
          />
          <div className="absolute inset-0 rounded-full" style={{
            background: 'linear-gradient(180deg, rgba(255,255,255,0.12) 0%, transparent 60%)',
            width: `${pct}%`,
          }} />
        </div>
        <div className="flex justify-between mt-1.5 px-0.5">
          <span className="text-[8px] font-mono text-low-text">Low</span>
          <span className="text-[8px] font-mono text-medium-text">Medium</span>
          <span className="text-[8px] font-mono text-high-text">High</span>
        </div>
      </div>

      {/* Trend + Sparkline */}
      <div className="flex items-center justify-between pt-4 border-t border-border/50 mt-auto">
        <div className={`font-mono text-[16px] font-medium ${trendColor[summary.level]}`}>
          {summary.trend > 0 ? '▲' : summary.trend < 0 ? '▼' : '—'} {summary.trend > 0 ? '+' : ''}{summary.trend}%
          <span className="text-[9px] text-text-dim ml-2 uppercase tracking-wider">vs last week</span>
        </div>

        {/* Mini sparkline */}
        <div className="flex items-end gap-[2px] h-5">
          {history.map((point, i) => {
            const h = Math.max(8, ((point.score - 20) / 60) * 100);
            const color = point.score >= 66 ? 'var(--color-high)' : point.score >= 41 ? 'var(--color-medium)' : 'var(--color-low)';
            return (
              <div
                key={i}
                className="w-[3px] rounded-sm opacity-70 hover:opacity-100 transition-opacity"
                style={{ height: `${h}%`, background: color }}
              />
            );
          })}
          <span className="text-[7px] text-text-dim ml-1 self-center">30d</span>
        </div>
      </div>
    </div>
  );
}
