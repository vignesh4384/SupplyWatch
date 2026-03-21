import type { RiskIndicator } from '../types/risk';
import { formatValue } from '../lib/utils';

interface KPICardProps {
  indicator: RiskIndicator;
}

const badgeStyles = {
  HIGH: 'bg-high-bg border-high-border text-high-text',
  MEDIUM: 'bg-medium-bg border-medium-border text-medium-text',
  LOW: 'bg-low-bg border-low-border text-low-text',
};

const cardRisk = {
  HIGH: 'card-risk-high',
  MEDIUM: 'card-risk-medium',
  LOW: 'card-risk-low',
};

const riskBarColor = {
  HIGH: { bar: '#ef4444', glow: '0 0 4px rgba(239,68,68,0.25)' },
  MEDIUM: { bar: '#f59e0b', glow: '0 0 4px rgba(245,158,11,0.2)' },
  LOW: { bar: '#10b981', glow: '0 0 4px rgba(16,185,129,0.15)' },
};

const riskBarWidth = {
  HIGH: '100%',
  MEDIUM: '60%',
  LOW: '30%',
};

export default function KPICard({ indicator }: KPICardProps) {
  const isUp = indicator.change > 0;
  const barConfig = riskBarColor[indicator.riskLevel];

  return (
    <div className={`card-base ${cardRisk[indicator.riskLevel]} px-5 py-4 cursor-pointer`}>
      {/* Header: name + badge */}
      <div className="flex justify-between items-center mb-3.5">
        <span className="text-[11.5px] text-text-muted font-medium tracking-wide">{indicator.name}</span>
        <span className={`text-[8.5px] font-bold px-2 py-[3px] rounded-md tracking-wider border ${badgeStyles[indicator.riskLevel]}`}>
          {indicator.riskLevel}
        </span>
      </div>

      {/* Value row */}
      <div className="flex items-baseline gap-1.5">
        <span className="font-mono text-[32px] font-medium leading-none tracking-tight text-text-primary">
          {formatValue(indicator.value, indicator.unit)}
        </span>
        <span className="text-[11px] text-text-dim font-normal">{indicator.unit}</span>
      </div>

      {/* Inline risk bar */}
      <div className="mt-3 mb-1">
        <div className="h-[4px] bg-bar-track rounded-full overflow-hidden">
          <div
            className="h-full rounded-full animate-bar"
            style={{
              width: riskBarWidth[indicator.riskLevel],
              background: barConfig.bar,
              boxShadow: barConfig.glow,
            }}
          />
        </div>
      </div>

      {/* Footer: change + date */}
      <div className="flex justify-between items-center mt-2 pt-3 border-t border-border/50">
        <span className={`font-mono text-[10.5px] font-medium flex items-center gap-1 px-2 py-0.5 rounded ${
          isUp ? 'text-high-text bg-chg-up-bg' : 'text-low-text bg-chg-down-bg'
        }`}>
          {isUp ? '▲' : '▼'} {isUp ? '+' : ''}{indicator.change}%
        </span>
        <span className="font-mono text-[9.5px] text-text-dim tracking-wider">{indicator.date}</span>
      </div>
    </div>
  );
}
