import type { RiskZone, RiskSummary, TradeRoute } from '../types/risk';

interface MapSidebarProps {
  summary: RiskSummary;
  zones: RiskZone[];
  routes: TradeRoute[];
  onZoneClick: (zone: RiskZone) => void;
}

const riskTextColor = {
  HIGH: 'text-high-text',
  MEDIUM: 'text-medium-text',
  LOW: 'text-low-text',
};

const riskBgColor = {
  HIGH: 'bg-high',
  MEDIUM: 'bg-medium',
  LOW: 'bg-low',
};

const statusStyle: Record<string, string> = {
  critical: 'bg-high-bg border border-high-border text-high-text',
  disrupted: 'bg-medium-bg border border-medium-border text-medium-text',
  normal: 'bg-low-bg border border-low-border text-low-text',
};

export default function MapSidebar({ summary, zones, routes, onZoneClick }: MapSidebarProps) {
  const topZones = [...zones].sort((a, b) => b.score - a.score).slice(0, 5);

  return (
    <div className="w-[300px] shrink-0 bg-header-bg border-r border-border p-5 overflow-y-auto">
      {/* Global Summary */}
      <section className="mb-6">
        <h4 className="font-heading text-[9px] font-bold uppercase tracking-[3px] text-text-dim mb-3">
          Global Summary
        </h4>
        <div className="bg-pill-bg border border-border rounded-xl p-4 text-center">
          <div className="font-mono text-[38px] font-medium text-text-primary tracking-tight leading-none">
            {summary.overallScore}
          </div>
          <div className="text-[9px] text-text-dim uppercase tracking-[2px] mt-1">
            Overall Risk Score
          </div>
          <div className="flex justify-center gap-4 mt-3">
            <span className="text-[10px]">
              <span className="font-mono font-medium text-high-text">{summary.highCount}</span>
              <span className="text-text-dim ml-1">High</span>
            </span>
            <span className="text-[10px]">
              <span className="font-mono font-medium text-medium-text">{summary.mediumCount}</span>
              <span className="text-text-dim ml-1">Med</span>
            </span>
            <span className="text-[10px]">
              <span className="font-mono font-medium text-low-text">{summary.lowCount}</span>
              <span className="text-text-dim ml-1">Low</span>
            </span>
          </div>
        </div>
      </section>

      {/* Top 5 Hotspots */}
      <section className="mb-6">
        <h4 className="font-heading text-[9px] font-bold uppercase tracking-[3px] text-text-dim mb-3">
          Top 5 Hotspots
        </h4>
        {topZones.map((zone, i) => (
          <div
            key={zone.id}
            onClick={() => onZoneClick(zone)}
            className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-pill-bg transition-all cursor-pointer mb-0.5"
          >
            <span className="font-mono text-[9px] text-text-dim w-4">
              {String(i + 1).padStart(2, '0')}
            </span>
            <div className={`w-[7px] h-[7px] rounded-full shrink-0 ${riskBgColor[zone.riskLevel]}`} />
            <div className="flex-1">
              <div className="text-[11px] font-semibold text-text-secondary">{zone.name}</div>
              <div className="text-[8px] text-text-dim">{zone.category}</div>
            </div>
            <span className={`font-mono text-[12px] font-medium ${riskTextColor[zone.riskLevel]}`}>
              {zone.score}
            </span>
          </div>
        ))}
      </section>

      {/* Route Status */}
      <section className="mb-6">
        <h4 className="font-heading text-[9px] font-bold uppercase tracking-[3px] text-text-dim mb-3">
          Route Status
        </h4>
        {routes.map(route => (
          <div
            key={route.id}
            className="flex justify-between items-center px-2.5 py-1.5 bg-pill-bg rounded-md border border-border mb-1"
          >
            <span className="text-[11px] text-text-secondary">{route.name}</span>
            <span className={`text-[7px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide ${statusStyle[route.status]}`}>
              {route.status}
            </span>
          </div>
        ))}
      </section>

      {/* Legend */}
      <section>
        <h4 className="font-heading text-[9px] font-bold uppercase tracking-[3px] text-text-dim mb-3">
          Legend
        </h4>
        {[
          { color: 'bg-high', label: 'High Risk (66-100)' },
          { color: 'bg-medium', label: 'Medium Risk (41-65)' },
          { color: 'bg-low', label: 'Low Risk (0-40)' },
          { color: 'bg-geo', label: 'Geopolitical' },
          { color: 'bg-maritime', label: 'Maritime' },
        ].map(item => (
          <div key={item.label} className="flex items-center gap-2 mb-1.5 text-[10px] text-text-dim">
            <div className={`w-[7px] h-[7px] rounded-full ${item.color}`} />
            {item.label}
          </div>
        ))}
        <div className="mt-2 pt-2 border-t border-border">
          <div className="text-[8px] font-bold uppercase tracking-[2px] text-text-dim mb-1.5">AIS Vessels</div>
          {[
            { color: 'bg-amber-400', label: 'Tanker' },
            { color: 'bg-cyan-400', label: 'Cargo' },
            { color: 'bg-slate-400', label: 'Other / Unknown' },
            { color: 'bg-red-500', label: 'Dark / Suspicious' },
          ].map(item => (
            <div key={item.label} className="flex items-center gap-2 mb-1.5 text-[10px] text-text-dim">
              <div className={`w-[7px] h-[7px] rounded-full ${item.color}`} />
              {item.label}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
