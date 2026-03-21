import type { DomainScore } from '../types/risk';

interface CategoryTrendsProps {
  domains: DomainScore[];
}

// Generate synthetic period comparison data
function generateTrendData(domains: DomainScore[]) {
  return domains.slice(0, 6).map(d => ({
    domain: d.domain,
    current: d.score,
    previous: Math.max(10, Math.min(95, d.score + Math.round((Math.random() - 0.55) * 20))),
    level: d.level,
  }));
}

const barColors = {
  current: 'rgba(168, 85, 247, 0.8)',
  previous: 'rgba(168, 85, 247, 0.25)',
};

export default function CategoryTrends({ domains }: CategoryTrendsProps) {
  const trends = generateTrendData(domains);

  return (
    <div className="card-base p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(59,130,246,0.1)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
          </div>
          <h3 className="font-heading text-[13px] font-bold uppercase tracking-[2px] text-text-secondary">
            Domain Trends
          </h3>
          <div className="flex-1 h-px bg-section-line ml-2" />
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-2 rounded-sm" style={{ background: barColors.current }} />
            <span className="text-[9px] text-text-dim">Current</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-2 rounded-sm" style={{ background: barColors.previous }} />
            <span className="text-[9px] text-text-dim">Previous</span>
          </div>
        </div>
      </div>

      {/* Bars */}
      <div className="flex flex-col gap-3">
        {trends.map((item, i) => {
          const delta = item.current - item.previous;
          const deltaColor = delta > 0 ? 'text-high-text' : delta < 0 ? 'text-low-text' : 'text-text-dim';
          return (
            <div key={item.domain} className="animate-fade-up" style={{ animationDelay: `${i * 50}ms` }}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] text-text-muted font-medium">{item.domain}</span>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[11px] text-text-secondary">{item.current}</span>
                  <span className={`font-mono text-[10px] ${deltaColor}`}>
                    {delta > 0 ? '+' : ''}{delta}
                  </span>
                </div>
              </div>
              {/* Stacked bars */}
              <div className="relative h-[8px] bg-bar-track rounded-full overflow-hidden">
                {/* Previous (background) */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full animate-bar"
                  style={{ width: `${item.previous}%`, background: barColors.previous }}
                />
                {/* Current (foreground) */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full animate-bar"
                  style={{
                    width: `${item.current}%`,
                    background: barColors.current,
                    boxShadow: item.current >= 70 ? '0 0 8px rgba(168,85,247,0.3)' : 'none',
                    animationDelay: '0.2s',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
