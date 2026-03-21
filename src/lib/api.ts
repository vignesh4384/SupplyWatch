import type { RiskSummary, RiskIndicator, RiskZone, Alert, TradeRoute, DomainScore, RiskHistoryPoint, DomainHistoryMap } from '../types/risk';

const BASE = '/api';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  getSummary:      () => fetchJson<RiskSummary>('/risk/summary'),
  getIndicators:   () => fetchJson<RiskIndicator[]>('/risk/indicators'),
  getZones:        () => fetchJson<RiskZone[]>('/risk/zones'),
  getAlerts:       () => fetchJson<Alert[]>('/alerts'),
  getRoutes:       () => fetchJson<TradeRoute[]>('/routes'),
  getHistory:      () => fetchJson<RiskHistoryPoint[]>('/risk/history'),
  getDomains:      () => fetchJson<DomainScore[]>('/risk/domains'),
  getDomainHistory:() => fetchJson<DomainHistoryMap>('/risk/domains/history'),
  refresh:         () => fetch(`${BASE}/refresh`, { method: 'POST' }),
};
