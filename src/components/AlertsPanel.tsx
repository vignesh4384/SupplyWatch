import { useState } from 'react';
import { Bell, Search } from 'lucide-react';
import type { Alert } from '../types/risk';

interface AlertsPanelProps {
  alerts: Alert[];
}

const severityConfig = {
  critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Critical', barWidth: '100%' },
  warning: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'Warning', barWidth: '65%' },
  info: { color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', label: 'Info', barWidth: '30%' },
};

const sourceIcons: Record<string, { color: string; bg: string }> = {
  GDELT: { color: '#a855f7', bg: 'rgba(168,85,247,0.12)' },
  GDACS: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
  NewsAPI: { color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
  AIS: { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)' },
  USGS: { color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
  NASA: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
};

type SeverityFilter = 'all' | 'critical' | 'warning' | 'info';

export default function AlertsPanel({ alerts }: AlertsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<SeverityFilter>('all');

  const filtered = alerts.filter(alert => {
    const matchesSearch = searchQuery === '' || alert.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = activeFilter === 'all' || alert.severity === activeFilter;
    return matchesSearch && matchesFilter;
  });

  const filterButtons: { key: SeverityFilter; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'critical', label: 'Critical' },
    { key: 'warning', label: 'Warning' },
    { key: 'info', label: 'Info' },
  ];

  return (
    <div className="card-base p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(239,68,68,0.1)' }}>
            <Bell size={16} color="#f87171" strokeWidth={2} />
          </div>
          <h3 className="font-heading text-[13px] font-bold uppercase tracking-[2px] text-text-secondary">
            Security Alerts
          </h3>
        </div>
        <span className="font-mono text-[10px] px-2.5 py-1 rounded-md bg-pill-bg border border-border text-text-dim">
          {filtered.length} of {alerts.length}
        </span>
      </div>

      {/* Search + Filter bar */}
      <div className="flex items-center gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-dim" />
          <input
            type="text"
            placeholder="Search alerts..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-2 rounded-lg bg-bg-input border border-border text-[11px] text-text-secondary placeholder:text-text-dim/50 focus:outline-none focus:border-accent/40 transition-colors"
          />
        </div>
        <div className="flex gap-0.5 p-[2px] rounded-lg bg-pill-bg border border-border">
          {filterButtons.map(fb => (
            <button
              key={fb.key}
              onClick={() => setActiveFilter(fb.key)}
              className={`px-3 py-1.5 rounded-md text-[10px] font-semibold transition-all ${
                activeFilter === fb.key
                  ? 'bg-accent text-white'
                  : 'text-text-dim hover:text-text-muted'
              }`}
            >
              {fb.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table header */}
      <div className="grid grid-cols-[1fr_100px_80px_90px_70px] gap-3 px-3 py-2 border-b border-border/50 mb-1">
        <span className="text-[9px] font-bold uppercase tracking-wider text-text-dim">Alert</span>
        <span className="text-[9px] font-bold uppercase tracking-wider text-text-dim">Risk Level</span>
        <span className="text-[9px] font-bold uppercase tracking-wider text-text-dim">Source</span>
        <span className="text-[9px] font-bold uppercase tracking-wider text-text-dim">Time</span>
        <span className="text-[9px] font-bold uppercase tracking-wider text-text-dim text-right">Status</span>
      </div>

      {/* Table rows */}
      <div className="flex flex-col gap-0.5 max-h-[380px] overflow-y-auto pr-1">
        {filtered.map(alert => {
          const sev = severityConfig[alert.severity];
          const src = sourceIcons[alert.source] || { color: '#8888a0', bg: 'rgba(136,136,160,0.1)' };

          return (
            <div
              key={alert.id}
              className="grid grid-cols-[1fr_100px_80px_90px_70px] gap-3 items-center px-3 py-2.5 rounded-lg hover:bg-pill-bg transition-all cursor-pointer group"
            >
              {/* Alert title */}
              <div className="min-w-0">
                <div className="text-[11.5px] font-medium leading-snug text-text-secondary group-hover:text-text-primary transition-colors truncate">
                  {alert.title}
                </div>
              </div>

              {/* Inline risk bar */}
              <div className="flex items-center gap-2">
                <div className="flex-1 h-[6px] bg-bar-track rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full animate-bar"
                    style={{ width: sev.barWidth, background: sev.color, boxShadow: `0 0 4px ${sev.bg}` }}
                  />
                </div>
              </div>

              {/* Source badge */}
              <div>
                <span
                  className="text-[9px] font-bold px-2 py-1 rounded-md tracking-wider inline-block"
                  style={{ background: src.bg, color: src.color }}
                >
                  {alert.source}
                </span>
              </div>

              {/* Timestamp */}
              <span className="font-mono text-[9.5px] text-text-dim">{alert.timestamp}</span>

              {/* Status */}
              <div className="text-right">
                <span className="inline-flex items-center gap-1.5 text-[9px] font-semibold px-2 py-0.5 rounded-md"
                      style={{ background: sev.bg, color: sev.color }}>
                  <span className="w-[5px] h-[5px] rounded-full" style={{ background: sev.color }} />
                  Open
                </span>
              </div>
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-8 text-[12px] text-text-dim">
            No alerts match your search
          </div>
        )}
      </div>
    </div>
  );
}
