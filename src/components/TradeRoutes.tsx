import { Route } from 'lucide-react';
import type { TradeRoute } from '../types/risk';

interface TradeRoutesProps {
  routes: TradeRoute[];
}

const statusStyle = {
  critical: 'bg-high-bg border border-high-border text-high-text',
  disrupted: 'bg-medium-bg border border-medium-border text-medium-text',
  normal: 'bg-low-bg border border-low-border text-low-text',
};

const riskBarConfig = {
  critical: { color: '#ef4444', glow: '0 0 4px rgba(239,68,68,0.25)', width: '92%' },
  disrupted: { color: '#f59e0b', glow: '0 0 4px rgba(245,158,11,0.2)', width: '65%' },
  normal: { color: '#10b981', glow: '0 0 4px rgba(16,185,129,0.15)', width: '32%' },
};

export default function TradeRoutes({ routes }: TradeRoutesProps) {
  return (
    <div className="card-base p-6">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(6,182,212,0.1)' }}>
          <Route size={16} color="#06b6d4" strokeWidth={2} />
        </div>
        <h3 className="font-heading text-[13px] font-bold uppercase tracking-[2px] text-text-secondary">
          Trade Routes
        </h3>
        <div className="flex-1 h-px bg-section-line ml-2" />
      </div>

      <div className="flex flex-col gap-1.5">
        {routes.map(route => {
          const bar = riskBarConfig[route.status];
          return (
            <div
              key={route.id}
              className="flex flex-col px-3.5 py-3 rounded-xl bg-bg-card border border-border hover:border-border-hover transition-all cursor-pointer group"
            >
              <div className="flex justify-between items-center mb-2">
                <div className="flex flex-col gap-0.5">
                  <span className="text-[12px] font-semibold text-text-secondary group-hover:text-text-primary transition-colors">{route.name}</span>
                  <span className="text-[10px] text-text-dim">{route.description}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-text-muted">{route.riskScore}</span>
                  <span className={`text-[8px] font-bold px-2.5 py-1 rounded-md uppercase tracking-wide ${statusStyle[route.status]}`}>
                    {route.status}
                  </span>
                </div>
              </div>

              {/* Inline risk bar */}
              <div className="h-[4px] bg-bar-track rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full animate-bar"
                  style={{
                    width: bar.width,
                    background: bar.color,
                    boxShadow: bar.glow,
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
