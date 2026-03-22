import { Info, Activity, Globe } from 'lucide-react';
import type { RiskSummary } from '../types/risk';

interface RiskDonutProps {
  summary: RiskSummary;
}

const levelColors = {
  high:   { bg: '#ef4444', glow: 'rgba(239,68,68,0.3)' },
  medium: { bg: '#f59e0b', glow: 'rgba(245,158,11,0.25)' },
  low:    { bg: '#10b981', glow: 'rgba(16,185,129,0.2)' },
} as const;

interface BarSection {
  label: string;
  icon: React.ReactNode;
  high: number;
  medium: number;
  low: number;
}

function StackedBar({ label, icon, high, medium, low }: BarSection) {
  const total = high + medium + low;
  if (total === 0) return null;

  const pctHigh = (high / total) * 100;
  const pctMed  = (medium / total) * 100;
  const pctLow  = (low / total) * 100;

  return (
    <div className="flex flex-col gap-2">
      {/* Label row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex items-center">{icon}</span>
          <span className="text-[12px] font-semibold text-text-primary tracking-wide">
            {label}
          </span>
        </div>
        <span className="font-mono text-[13px] font-medium text-text-secondary">
          {total}
        </span>
      </div>

      {/* Stacked bar */}
      <div className="flex h-3 rounded-full overflow-hidden bg-white/[0.04] gap-[2px]">
        {high > 0 && (
          <div
            className="rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${pctHigh}%`,
              background: levelColors.high.bg,
              boxShadow: `0 0 8px ${levelColors.high.glow}`,
            }}
          />
        )}
        {medium > 0 && (
          <div
            className="rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${pctMed}%`,
              background: levelColors.medium.bg,
              boxShadow: `0 0 8px ${levelColors.medium.glow}`,
            }}
          />
        )}
        {low > 0 && (
          <div
            className="rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${pctLow}%`,
              background: levelColors.low.bg,
              boxShadow: `0 0 8px ${levelColors.low.glow}`,
            }}
          />
        )}
      </div>

      {/* Legend counts */}
      <div className="flex items-center gap-4">
        {high > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: levelColors.high.bg }} />
            <span className="text-[10px] text-text-dim">
              <span className="font-mono font-medium text-text-secondary">{high}</span> High
            </span>
          </div>
        )}
        {medium > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: levelColors.medium.bg }} />
            <span className="text-[10px] text-text-dim">
              <span className="font-mono font-medium text-text-secondary">{medium}</span> Med
            </span>
          </div>
        )}
        {low > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: levelColors.low.bg }} />
            <span className="text-[10px] text-text-dim">
              <span className="font-mono font-medium text-text-secondary">{low}</span> Low
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function RiskDonut({ summary }: RiskDonutProps) {
  const indicatorTotal = (summary.indicatorHighCount ?? 0) + (summary.indicatorMediumCount ?? 0) + (summary.indicatorLowCount ?? 0);
  const zoneTotal = (summary.zoneHighCount ?? 0) + (summary.zoneMediumCount ?? 0) + (summary.zoneLowCount ?? 0);
  const grandTotal = indicatorTotal + zoneTotal;

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
        {/* Info tooltip */}
        <div className="relative group">
          <Info size={14} className="text-text-dim cursor-help opacity-40 hover:opacity-80 transition-opacity" />
          <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-72 px-3.5 py-3 rounded-lg
                          bg-[#1a1a2e] border border-white/10 shadow-xl
                          text-[11px] leading-relaxed text-text-secondary
                          opacity-0 invisible group-hover:opacity-100 group-hover:visible
                          transition-all duration-200 z-50 pointer-events-none">
            <span className="block font-semibold text-text-primary mb-1.5">What's being counted?</span>
            <span className="block mb-1"><span className="text-purple-400 font-medium">Indicators</span> — commodities (oil, metals, gas), freight rates (Baltic Dry, SCFI, Air Cargo), and economic indices.</span>
            <span className="block mb-1.5"><span className="text-blue-400 font-medium">Risk Zones</span> — geopolitical hotspots (Red Sea, Taiwan Strait, Suez), plus live disaster events from GDACS, USGS &amp; NASA EONET.</span>
            <span className="block text-text-dim border-t border-white/5 pt-1.5">
              Each item is scored: High &ge; 66 &middot; Medium 41–65 &middot; Low &lt; 41. Total may vary as live events change.
            </span>
          </div>
        </div>
        <div className="flex-1 h-px bg-section-line ml-2" />
        {/* Grand total badge */}
        <div className="flex items-center gap-1.5 ml-2">
          <span className="font-mono text-[18px] font-semibold text-text-primary leading-none">
            {grandTotal}
          </span>
          <span className="text-[9px] uppercase tracking-[1.5px] text-text-dim">
            total
          </span>
        </div>
      </div>

      {/* Stacked bars */}
      <div className="flex flex-col gap-5 flex-1 justify-center">
        <StackedBar
          label="Indicators"
          icon={<Activity size={14} className="text-purple-400" />}
          high={summary.indicatorHighCount ?? 0}
          medium={summary.indicatorMediumCount ?? 0}
          low={summary.indicatorLowCount ?? 0}
        />
        <StackedBar
          label="Risk Zones"
          icon={<Globe size={14} className="text-cyan-400" />}
          high={summary.zoneHighCount ?? 0}
          medium={summary.zoneMediumCount ?? 0}
          low={summary.zoneLowCount ?? 0}
        />
      </div>
    </div>
  );
}
