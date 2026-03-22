import type { RiskSummary, RiskIndicator, Alert, DomainScore, TradeRoute, RiskZone, RiskHistoryPoint } from '../types/risk';

export const mockSummary: RiskSummary = {
  overallScore: 72,
  level: 'HIGH',
  highCount: 5,
  mediumCount: 8,
  lowCount: 12,
  indicatorHighCount: 3,
  indicatorMediumCount: 5,
  indicatorLowCount: 7,
  zoneHighCount: 2,
  zoneMediumCount: 3,
  zoneLowCount: 5,
  lastUpdated: '2026-03-18T14:32:07Z',
  trend: 4.2,
};

export const mockIndicators: RiskIndicator[] = [
  // Energy & Fuel
  { id: 'brent', name: 'Brent Crude Oil', category: 'energy', value: 104.80, unit: 'USD/bbl', change: 3.2, riskLevel: 'HIGH', date: 'Mar 17' },
  { id: 'wti', name: 'WTI Crude Oil', category: 'energy', value: 98.40, unit: 'USD/bbl', change: 2.8, riskLevel: 'HIGH', date: 'Mar 17' },
  { id: 'natgas', name: 'Natural Gas', category: 'energy', value: 3.21, unit: 'USD/MMBtu', change: 1.4, riskLevel: 'MEDIUM', date: 'Mar 17' },
  { id: 'gasoline', name: 'US Gasoline', category: 'energy', value: 3.48, unit: 'USD/gal', change: 0.8, riskLevel: 'MEDIUM', date: 'Mar 14' },
  // Freight
  { id: 'bdi', name: 'Baltic Dry Index', category: 'freight', value: 1847, unit: 'index', change: -2.1, riskLevel: 'MEDIUM', date: 'Mar 17' },
  { id: 'scfi', name: 'Shanghai SCFI', category: 'freight', value: 1023, unit: 'index', change: -0.5, riskLevel: 'LOW', date: 'Mar 14' },
  { id: 'aircargo', name: 'Air Cargo Rate', category: 'freight', value: 3.42, unit: 'USD/kg', change: 5.3, riskLevel: 'MEDIUM', date: 'Mar 14' },
  // Raw Materials
  { id: 'copper', name: 'Copper', category: 'raw_materials', value: 8920, unit: 'USD/ton', change: 1.8, riskLevel: 'MEDIUM', date: 'Mar 15' },
  { id: 'aluminum', name: 'Aluminum', category: 'raw_materials', value: 2340, unit: 'USD/ton', change: -0.3, riskLevel: 'LOW', date: 'Mar 15' },
  { id: 'ironore', name: 'Iron Ore', category: 'raw_materials', value: 118.50, unit: 'USD/ton', change: -1.2, riskLevel: 'LOW', date: 'Mar 15' },
  { id: 'steel', name: 'Steel HRC', category: 'raw_materials', value: 680, unit: 'USD/ton', change: 2.4, riskLevel: 'MEDIUM', date: 'Mar 14' },
  // Inflation
  { id: 'cpi', name: 'US CPI', category: 'inflation', value: 3.2, unit: '%', change: 0.1, riskLevel: 'MEDIUM', date: 'Feb 2026' },
  { id: 'hicp', name: 'EU HICP', category: 'inflation', value: 2.8, unit: '%', change: -0.2, riskLevel: 'LOW', date: 'Feb 2026' },
  { id: 'ppi', name: 'PPI All Commodities', category: 'inflation', value: 248.6, unit: 'index', change: 4.1, riskLevel: 'HIGH', date: 'Feb 2026' },
  // Economic
  { id: 'pmi', name: 'US PMI', category: 'economic', value: 51.2, unit: 'index', change: 0.4, riskLevel: 'MEDIUM', date: 'Mar 2026' },
  { id: 'sentiment', name: 'Consumer Sentiment', category: 'economic', value: 68.4, unit: 'index', change: -2.1, riskLevel: 'MEDIUM', date: 'Mar 2026' },
  { id: 'indpro', name: 'Industrial Production', category: 'economic', value: 103.8, unit: 'index', change: 0.2, riskLevel: 'LOW', date: 'Feb 2026' },
];

export const mockAlerts: Alert[] = [
  { id: 'a1', title: 'Red Sea shipping attacks escalate — vessels rerouting via Cape', severity: 'critical', source: 'GDELT', timestamp: '2 hours ago' },
  { id: 'a2', title: 'Cyclone warning issued for Bay of Bengal — Port Chennai on alert', severity: 'critical', source: 'GDACS', timestamp: '3 hours ago' },
  { id: 'a3', title: 'EU imposes new tariffs on Chinese EV imports effective April 1', severity: 'warning', source: 'NewsAPI', timestamp: '5 hours ago' },
  { id: 'a4', title: 'Panama Canal water levels drop — transit restrictions tightened', severity: 'warning', source: 'GDELT', timestamp: '8 hours ago' },
  { id: 'a5', title: 'Port of Shanghai reports 12% congestion increase week-over-week', severity: 'info', source: 'AIS', timestamp: '12 hours ago' },
  { id: 'a6', title: 'Semiconductor supply constraints reported across Taiwan foundries', severity: 'warning', source: 'NewsAPI', timestamp: '14 hours ago' },
  { id: 'a7', title: 'OPEC+ announces production cut extension through Q2 2026', severity: 'info', source: 'NewsAPI', timestamp: '1 day ago' },
];

export const mockDomains: DomainScore[] = [
  { domain: 'Geopolitical', score: 82, level: 'HIGH' },
  { domain: 'Maritime', score: 74, level: 'HIGH' },
  { domain: 'Energy', score: 68, level: 'HIGH' },
  { domain: 'Raw Materials', score: 61, level: 'MEDIUM' },
  { domain: 'Weather', score: 55, level: 'MEDIUM' },
  { domain: 'Trade Policy', score: 48, level: 'MEDIUM' },
  { domain: 'Cyber', score: 35, level: 'LOW' },
  { domain: 'Labour', score: 28, level: 'LOW' },
];

export const mockRoutes: TradeRoute[] = [
  { id: 'r1', name: 'Suez Canal', description: 'Asia — Europe via Red Sea', status: 'critical', riskScore: 92, points: [[30,32],[13.5,43.5],[12,45],[5,50],[0,55],[-5,60],[10,70],[22,80],[30,105],[35,120]] },
  { id: 'r2', name: 'Strait of Hormuz', description: 'Persian Gulf — Indian Ocean', status: 'disrupted', riskScore: 85, points: [[26.5,56.5],[25,58],[24,60],[22,63],[18,68],[12,72]] },
  { id: 'r3', name: 'Cape of Good Hope', description: 'Asia — Europe (alternate)', status: 'disrupted', riskScore: 65, points: [[0,50],[-10,40],[-25,30],[-34,18],[-34,25],[-30,35],[-20,40],[-5,50],[10,55],[25,60]] },
  { id: 'r4', name: 'Trans-Pacific', description: 'East Asia — North America', status: 'normal', riskScore: 32, points: [[35,120],[33,140],[30,160],[28,180],[30,-170],[33,-155],[35,-140],[36,-125]] },
];

export const mockZones: RiskZone[] = [
  { id: 'z1', name: 'Red Sea / Suez Canal', lat: 13.5, lng: 43.5, score: 92, riskLevel: 'HIGH', category: 'maritime', description: 'Houthi attacks disrupting vessel transits. Major rerouting via Cape of Good Hope.' },
  { id: 'z2', name: 'Black Sea / Ukraine', lat: 46.0, lng: 33.0, score: 88, riskLevel: 'HIGH', category: 'geopolitical', description: 'Ongoing conflict affecting grain exports and energy supply routes.' },
  { id: 'z3', name: 'Strait of Hormuz', lat: 26.5, lng: 56.5, score: 85, riskLevel: 'HIGH', category: 'maritime', description: 'Elevated tension. 20% of global oil transits through this chokepoint.' },
  { id: 'z4', name: 'Taiwan Strait', lat: 24.0, lng: 120.0, score: 72, riskLevel: 'MEDIUM', category: 'geopolitical', description: 'Military exercises increasing. Key semiconductor supply chain risk.' },
  { id: 'z5', name: 'Bay of Bengal', lat: 14.0, lng: 88.0, score: 65, riskLevel: 'MEDIUM', category: 'disaster', description: 'Cyclone season approaching. Port Chennai on pre-alert status.' },
  { id: 'z6', name: 'Shanghai Port', lat: 31.2, lng: 121.5, score: 58, riskLevel: 'MEDIUM', category: 'economic', description: 'Container congestion up 12% WoW. Average dwell time increasing.' },
  { id: 'z7', name: 'Singapore Strait', lat: 1.3, lng: 104.0, score: 42, riskLevel: 'MEDIUM', category: 'maritime', description: 'Increased vessel density due to Red Sea rerouting.' },
  { id: 'z8', name: 'Panama Canal', lat: 9.0, lng: -79.5, score: 55, riskLevel: 'MEDIUM', category: 'disaster', description: 'Water levels critically low. Transit restrictions in effect.' },
  { id: 'z9', name: 'Gulf of Guinea', lat: 3.0, lng: 5.0, score: 48, riskLevel: 'MEDIUM', category: 'maritime', description: 'Piracy incidents declining but remain elevated.' },
  { id: 'z10', name: 'US Gulf Coast', lat: 28.0, lng: -90.0, score: 35, riskLevel: 'LOW', category: 'disaster', description: 'Hurricane season prep underway. No active threats.' },
  { id: 'z11', name: 'Rotterdam Port', lat: 51.9, lng: 4.5, score: 25, riskLevel: 'LOW', category: 'economic', description: 'Operations normal. Minor labor negotiations ongoing.' },
  { id: 'z12', name: 'South China Sea', lat: 15.0, lng: 115.0, score: 68, riskLevel: 'HIGH', category: 'geopolitical', description: 'Territorial disputes affecting shipping lane confidence.' },
];

export const mockHistory: RiskHistoryPoint[] = Array.from({ length: 20 }, (_, i) => ({
  date: `Mar ${i + 1}`,
  score: Math.round(40 + i * 1.6 + Math.sin(i * 0.5) * 5),
}));
