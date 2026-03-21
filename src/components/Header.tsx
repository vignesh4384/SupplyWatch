interface HeaderProps {
  view: 'dashboard' | 'map';
  onViewChange: (view: 'dashboard' | 'map') => void;
  lastUpdated: string;
  isLive?: boolean;
}

export default function Header({ view, onViewChange, lastUpdated, isLive = false }: HeaderProps) {
  const ts = new Date(lastUpdated);
  const formatted = `${ts.getUTCFullYear()}-${String(ts.getUTCMonth() + 1).padStart(2, '0')}-${String(ts.getUTCDate()).padStart(2, '0')}  ${String(ts.getUTCHours()).padStart(2, '0')}:${String(ts.getUTCMinutes()).padStart(2, '0')} UTC`;

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-8 py-3 bg-header-bg border-b border-border">
      <div className="flex items-center gap-3.5">
        <span className="font-heading font-[800] text-[20px] tracking-tight text-text-primary">
          SupplyWatch
        </span>
        <div className="w-px h-5 bg-border" />
        <span className="text-[10px] uppercase tracking-[2.5px] font-medium text-text-dim">
          Global Supply Chain Control Tower
        </span>
      </div>

      <div className="flex items-center gap-3.5">
        <span className="font-mono text-[10px] tracking-wide text-text-dim">
          {formatted}
        </span>

        {/* LIVE badge */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-[1.5px] text-low-text bg-low-bg border border-low-border">
          <div className="w-1.5 h-1.5 rounded-full bg-low-text animate-live" />
          LIVE
        </div>

        {/* View toggle */}
        <div className="flex gap-0.5 p-[3px] rounded-lg bg-pill-bg border border-border">
          <button
            onClick={() => onViewChange('dashboard')}
            className={`px-4 py-1.5 rounded-md text-[11px] font-semibold transition-all ${
              view === 'dashboard'
                ? 'bg-accent text-white'
                : 'text-text-dim hover:text-text-muted'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => onViewChange('map')}
            className={`px-4 py-1.5 rounded-md text-[11px] font-semibold transition-all ${
              view === 'map'
                ? 'bg-accent text-white'
                : 'text-text-dim hover:text-text-muted'
            }`}
          >
            Map View
          </button>
        </div>
      </div>
    </header>
  );
}
