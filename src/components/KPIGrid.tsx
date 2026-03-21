import type { RiskIndicator, IndicatorCategory } from '../types/risk';
import { Flame, Ship, Gem, TrendingUp, Activity } from 'lucide-react';
import KPICard from './KPICard';

interface KPIGridProps {
  indicators: RiskIndicator[];
}

const categoryConfig: Record<IndicatorCategory, { label: string; colorClass: string; cols?: number; iconColor: string }> = {
  energy: { label: 'Energy & Fuel', colorClass: 'energy', iconColor: '#fbbf24' },
  freight: { label: 'Freight & Shipping', colorClass: 'freight', cols: 3, iconColor: '#3b82f6' },
  raw_materials: { label: 'Raw Materials', colorClass: 'materials', iconColor: '#a855f7' },
  inflation: { label: 'Inflation', colorClass: 'inflation', cols: 3, iconColor: '#f87171' },
  economic: { label: 'Economic Activity', colorClass: 'economic', cols: 3, iconColor: '#34d399' },
};

const categoryIcons: Record<IndicatorCategory, typeof Flame> = {
  energy: Flame,
  freight: Ship,
  raw_materials: Gem,
  inflation: TrendingUp,
  economic: Activity,
};

const colorMap: Record<string, string> = {
  energy: 'bg-medium',
  freight: 'bg-cyber',
  materials: 'bg-geo',
  inflation: 'bg-high',
  economic: 'bg-low',
};

const iconBgMap: Record<string, string> = {
  energy: 'rgba(251,191,36,0.1)',
  freight: 'rgba(59,130,246,0.1)',
  materials: 'rgba(168,85,247,0.1)',
  inflation: 'rgba(248,113,113,0.1)',
  economic: 'rgba(52,211,153,0.1)',
};

const categoryOrder: IndicatorCategory[] = ['energy', 'freight', 'raw_materials', 'inflation', 'economic'];

export default function KPIGrid({ indicators }: KPIGridProps) {
  const grouped = categoryOrder.map(cat => ({
    category: cat,
    config: categoryConfig[cat],
    items: indicators.filter(ind => ind.category === cat),
  })).filter(g => g.items.length > 0);

  return (
    <div className="space-y-1">
      {grouped.map(({ category, config, items }, idx) => {
        const Icon = categoryIcons[category];
        return (
          <div key={category} className={idx > 0 ? 'pt-6 border-t border-section-line' : ''}>
            {/* Section header with icon */}
            <div className="flex items-center gap-3 mb-4 pl-1">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: iconBgMap[config.colorClass] }}
              >
                <Icon size={16} color={config.iconColor} strokeWidth={2} />
              </div>
              <span className="text-[13px] font-heading font-bold uppercase tracking-[2px] text-text-muted">
                {config.label}
              </span>
              <div className="flex-1 h-px bg-section-line ml-3" />
              <span className="text-[10px] font-mono text-text-dim/60 tracking-wider">
                {items.length} indicators
              </span>
            </div>

            {/* Cards grid */}
            <div
              className="grid gap-3 mb-4"
              style={{ gridTemplateColumns: `repeat(${config.cols || 4}, 1fr)` }}
            >
              {items.map((indicator, i) => (
                <div key={indicator.id} className="animate-fade-up" style={{ animationDelay: `${i * 50}ms` }}>
                  <KPICard indicator={indicator} />
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
