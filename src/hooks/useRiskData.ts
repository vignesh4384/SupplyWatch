import { useState, useEffect, useCallback } from 'react';
import type { RiskSummary, RiskIndicator, Alert, DomainScore, TradeRoute, RiskZone, RiskHistoryPoint, DomainHistoryMap } from '../types/risk';
import { api } from '../lib/api';
import { mockSummary, mockIndicators, mockAlerts, mockDomains, mockRoutes, mockZones, mockHistory } from '../data/mockData';

export interface RiskData {
  summary: RiskSummary;
  indicators: RiskIndicator[];
  alerts: Alert[];
  domains: DomainScore[];
  routes: TradeRoute[];
  zones: RiskZone[];
  history: RiskHistoryPoint[];
  domainHistory: DomainHistoryMap;
}

interface UseRiskDataResult {
  data: RiskData;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  isLive: boolean;
}

const POLL_INTERVAL = 60_000; // 60 seconds

// Default mock data (renders immediately)
const defaultData: RiskData = {
  summary: mockSummary,
  indicators: mockIndicators,
  alerts: mockAlerts,
  domains: mockDomains,
  routes: mockRoutes,
  zones: mockZones,
  history: mockHistory,
  domainHistory: {},
};

export function useRiskData(): UseRiskDataResult {
  const [data, setData] = useState<RiskData>(defaultData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const results = await Promise.allSettled([
        api.getSummary(),
        api.getIndicators(),
        api.getAlerts(),
        api.getDomains(),
        api.getRoutes(),
        api.getZones(),
        api.getHistory(),
        api.getDomainHistory(),
      ]);

      // Partial fallback: use API data where available, mock data otherwise
      const newData: RiskData = {
        summary: results[0].status === 'fulfilled' ? results[0].value : defaultData.summary,
        indicators: results[1].status === 'fulfilled' && results[1].value.length > 0 ? results[1].value : defaultData.indicators,
        alerts: results[2].status === 'fulfilled' && results[2].value.length > 0 ? results[2].value : defaultData.alerts,
        domains: results[3].status === 'fulfilled' && results[3].value.length > 0 ? results[3].value : defaultData.domains,
        routes: results[4].status === 'fulfilled' && results[4].value.length > 0 ? results[4].value : defaultData.routes,
        zones: results[5].status === 'fulfilled' && results[5].value.length > 0 ? results[5].value : defaultData.zones,
        history: results[6].status === 'fulfilled' && results[6].value.length > 0 ? results[6].value : defaultData.history,
        domainHistory: results[7].status === 'fulfilled' && Object.keys(results[7].value).length > 0 ? results[7].value : defaultData.domainHistory,
      };

      setData(newData);

      // Check if any API call succeeded (= live data)
      const anyLive = results.some(r => r.status === 'fulfilled');
      setIsLive(anyLive);

      if (!anyLive) {
        setError('Backend unreachable — showing mock data');
      }
    } catch (e) {
      setError('Failed to fetch data — showing mock data');
      setIsLive(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch + polling
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const refresh = useCallback(() => {
    api.refresh().catch(() => {});
    // Fetch updated data after a short delay (give backend time to process)
    setTimeout(fetchAll, 3000);
  }, [fetchAll]);

  return { data, loading, error, refresh, isLive };
}
