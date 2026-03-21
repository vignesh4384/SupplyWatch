import { useMemo } from 'react';
import type { DomainScore, DomainHistoryMap } from '../types/risk';

interface RiskHeatmapProps {
  domains: DomainScore[];
  domainHistory: DomainHistoryMap;
}

// Generate synthetic weekly data as fallback when no real history exists
function generateSyntheticData(domains: DomainScore[]): { domain: string; weeks: number[]; labels: string[] }[] {
  const labels = ['W-8', 'W-7', 'W-6', 'W-5', 'W-4', 'W-3', 'W-2', 'W-1'];
  return domains.slice(0, 6).map((d) => {
    const weeks: number[] = [];
    for (let w = 0; w < 8; w++) {
      const variation = Math.sin(w * 0.8 + d.score * 0.1) * 12 + (Math.random() - 0.5) * 8;
      const val = Math.max(0, Math.min(100, d.score + variation - (8 - w) * 2));
      weeks.push(Math.round(val));
    }
    return { domain: d.domain, weeks, labels };
  });
}

// Build heatmap data from real API domain history
function buildFromHistory(domainHistory: DomainHistoryMap, domains: DomainScore[]): { domain: string; weeks: number[]; labels: string[] }[] | null {
  const domainNames = Object.keys(domainHistory);
  if (domainNames.length === 0) return null;

  // Get all unique dates across all domains
  const allDates = new Set<string>();
  for (const points of Object.values(domainHistory)) {
    for (const p of points) allDates.add(p.date);
  }
  const sortedDates = Array.from(allDates).sort();
  // Take last 8 dates
  const recentDates = sortedDates.slice(-8);
  if (recentDates.length === 0) return null;

  const labels = recentDates.map(d => d); // Use actual date labels

  // Order domains by current score descending (matching domain_scores order)
  const domainOrder = domains.map(d => d.domain).filter(d => domainNames.includes(d));
  // Add any domains in history not in current domains list
  for (const d of domainNames) {
    if (!domainOrder.includes(d)) domainOrder.push(d);
  }

  return domainOrder.slice(0, 6).map(domain => {
    const points = domainHistory[domain] || [];
    const dateMap = new Map(points.map(p => [p.date, p.score]));

    const weeks = recentDates.map(date => dateMap.get(date) ?? 0);
    return { domain, weeks, labels };
  });
}

// Map score to purple gradient intensity
function scoreToColor(score: number): string {
  if (score >= 75) return 'rgba(168, 85, 247, 0.85)';
  if (score >= 60) return 'rgba(168, 85, 247, 0.6)';
  if (score >= 45) return 'rgba(168, 85, 247, 0.38)';
  if (score >= 30) return 'rgba(168, 85, 247, 0.2)';
  return 'rgba(168, 85, 247, 0.08)';
}

function scoreToGlow(score: number): string {
  if (score >= 75) return '0 0 8px rgba(168,85,247,0.3)';
  if (score >= 60) return '0 0 4px rgba(168,85,247,0.15)';
  return 'none';
}

export default function RiskHeatmap({ domains, domainHistory }: RiskHeatmapProps) {
  const heatData = useMemo(() => {
    const fromHistory = buildFromHistory(domainHistory, domains);
    return fromHistory ?? generateSyntheticData(domains);
  }, [domains, domainHistory]);

  const columnCount = heatData.length > 0 ? heatData[0].weeks.length : 8;
  const labels = heatData.length > 0 ? heatData[0].labels : [];
  const hasRealData = Object.keys(domainHistory).length > 0;

  return (
    <div className="card-base p-6 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(124,58,237,0.1)' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1" />
            <rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" />
            <rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
        </div>
        <h3 className="font-heading text-[13px] font-bold uppercase tracking-[2px] text-text-secondary">
          Risk Heatmap
        </h3>
        <div className="flex-1 h-px bg-section-line ml-2" />
        <span className="text-[9px] font-mono text-text-dim uppercase tracking-wider">
          {hasRealData ? `${columnCount} snapshots` : '8 weeks'}
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="flex-1 flex flex-col justify-center">
        {/* Column headers */}
        <div className="grid items-center gap-[3px] mb-1.5" style={{ gridTemplateColumns: `80px repeat(${columnCount}, 1fr)` }}>
          <div />
          {labels.map(w => (
            <span key={w} className="text-[8px] font-mono text-text-dim text-center">{w}</span>
          ))}
        </div>

        {/* Rows */}
        <div className="flex flex-col gap-[3px]">
          {heatData.map((row, i) => (
            <div
              key={row.domain}
              className="grid items-center gap-[3px] animate-fade-up"
              style={{ gridTemplateColumns: `80px repeat(${columnCount}, 1fr)`, animationDelay: `${i * 60}ms` }}
            >
              <span className="text-[10px] text-text-muted font-medium truncate pr-2">
                {row.domain}
              </span>
              {row.weeks.map((score, w) => (
                <div
                  key={w}
                  className="h-[26px] rounded-[4px] flex items-center justify-center transition-all duration-300 hover:scale-110 cursor-default"
                  style={{
                    background: scoreToColor(score),
                    boxShadow: scoreToGlow(score),
                  }}
                  title={`${row.domain} ${labels[w]}: ${score}`}
                >
                  <span className="text-[8px] font-mono text-white/60">{score}</span>
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Gradient legend */}
        <div className="flex items-center gap-2 mt-4 justify-end">
          <span className="text-[8px] text-text-dim">Low</span>
          <div className="flex gap-0.5">
            {[0.08, 0.2, 0.38, 0.6, 0.85].map((opacity, i) => (
              <div
                key={i}
                className="w-4 h-2.5 rounded-sm"
                style={{ background: `rgba(168, 85, 247, ${opacity})` }}
              />
            ))}
          </div>
          <span className="text-[8px] text-text-dim">High</span>
        </div>
      </div>
    </div>
  );
}
