import { BarChart3 } from 'lucide-react';
import type { DomainScore } from '../types/risk';

interface DomainBarsProps {
  domains: DomainScore[];
}

const barGradient = {
  HIGH: 'bg-gradient-to-r from-[#dc2626] to-[#f87171]',
  MEDIUM: 'bg-gradient-to-r from-[#d97706] to-[#fbbf24]',
  LOW: 'bg-gradient-to-r from-[#059669] to-[#34d399]',
};

const scoreColor = {
  HIGH: 'text-high-text',
  MEDIUM: 'text-medium-text',
  LOW: 'text-low-text',
};

const barShadow = {
  HIGH: '0 0 8px rgba(239,68,68,0.15)',
  MEDIUM: '0 0 6px rgba(245,158,11,0.12)',
  LOW: '0 0 6px rgba(16,185,129,0.1)',
};

export default function DomainBars({ domains }: DomainBarsProps) {
  return (
    <div className="card-base p-6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(124,58,237,0.1)' }}>
          <BarChart3 size={16} color="#a78bfa" strokeWidth={2} />
        </div>
        <h3 className="font-heading text-[13px] font-bold uppercase tracking-[2px] text-text-secondary">
          Risk by Domain
        </h3>
        <div className="flex-1 h-px bg-section-line ml-2" />
      </div>

      <div className="flex flex-col gap-3.5">
        {domains.map(domain => (
          <div key={domain.domain} className="grid grid-cols-[95px_1fr_38px] items-center gap-3.5 group">
            <span className="text-[11px] text-text-muted font-medium group-hover:text-text-secondary transition-colors">
              {domain.domain}
            </span>
            <div className="h-[7px] bg-bar-track rounded-[3px] overflow-hidden">
              <div
                className={`h-full rounded-[3px] animate-bar ${barGradient[domain.level]}`}
                style={{ width: `${domain.score}%`, boxShadow: barShadow[domain.level] }}
              />
            </div>
            <span className={`font-mono text-[13px] font-medium text-right tabular-nums ${scoreColor[domain.level]}`}>
              {domain.score}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
