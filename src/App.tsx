import { useState, useCallback } from 'react';
import Header from './components/Header';
import RiskBanner from './components/RiskBanner';
import RiskDonut from './components/RiskDonut';
import RiskHeatmap from './components/RiskHeatmap';
import KPIGrid from './components/KPIGrid';
import AlertsPanel from './components/AlertsPanel';
import DomainBars from './components/DomainBars';
import TradeRoutes from './components/TradeRoutes';
import CategoryTrends from './components/CategoryTrends';
import MapView from './components/MapView';
import MapSidebar from './components/MapSidebar';
import AskAnalyst from './components/AskAnalyst';
import { useRiskData } from './hooks/useRiskData';
import type { RiskZone } from './types/risk';

export default function App() {
  const [view, setView] = useState<'dashboard' | 'map'>('dashboard');
  const [flyToTarget, setFlyToTarget] = useState<RiskZone | null>(null);
  const { data, isLive } = useRiskData();

  const { summary, indicators, alerts, domains, routes, zones, history, domainHistory } = data;

  const handleZoneClick = useCallback((zone: RiskZone) => {
    setFlyToTarget(zone);
    setTimeout(() => setFlyToTarget(null), 2000);
  }, []);

  return (
    <div className="min-h-screen bg-bg">
      <Header
        view={view}
        onViewChange={setView}
        lastUpdated={summary.lastUpdated}
        isLive={isLive}
      />

      {view === 'dashboard' ? (
        <main className="px-8 py-7 max-w-[1600px] mx-auto">
          {/* Executive Summary Row — 3 columns */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <RiskBanner summary={summary} history={history} />
            <RiskHeatmap domains={domains} domainHistory={domainHistory} />
            <RiskDonut summary={summary} />
          </div>

          {/* KPI Grid */}
          <KPIGrid indicators={indicators} />

          {/* Alerts Table — full width */}
          <div className="mt-6">
            <AlertsPanel alerts={alerts} />
          </div>

          {/* Bottom row: Domain Trends + Domain Bars + Trade Routes */}
          <div className="grid grid-cols-3 gap-4 mt-6">
            <CategoryTrends domains={domains} />
            <DomainBars domains={domains} />
            <TradeRoutes routes={routes} />
          </div>
        </main>
      ) : (
        <div className="flex h-[calc(100vh-53px)]">
          <MapSidebar
            summary={summary}
            zones={zones}
            routes={routes}
            onZoneClick={handleZoneClick}
          />
          <MapView
            zones={zones}
            routes={routes}
            flyToTarget={flyToTarget}
          />
        </div>
      )}

      <AskAnalyst view={view} />
    </div>
  );
}
