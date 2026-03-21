export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type AlertSeverity = 'info' | 'warning' | 'critical';
export type RouteStatus = 'normal' | 'disrupted' | 'critical';
export type IndicatorCategory = 'energy' | 'freight' | 'raw_materials' | 'inflation' | 'economic';
export type ZoneCategory = 'economic' | 'disaster' | 'maritime' | 'geopolitical';

export interface RiskSummary {
  overallScore: number;
  level: RiskLevel;
  highCount: number;
  mediumCount: number;
  lowCount: number;
  lastUpdated: string;
  trend: number;
}

export interface RiskIndicator {
  id: string;
  name: string;
  category: IndicatorCategory;
  value: number;
  unit: string;
  change: number;
  riskLevel: RiskLevel;
  date: string;
}

export interface RiskZone {
  id: string;
  name: string;
  lat: number;
  lng: number;
  score: number;
  riskLevel: RiskLevel;
  category: ZoneCategory;
  description: string;
}

export interface Alert {
  id: string;
  title: string;
  severity: AlertSeverity;
  source: string;
  timestamp: string;
}

export interface TradeRoute {
  id: string;
  name: string;
  description: string;
  status: RouteStatus;
  riskScore: number;
  points: [number, number][];
}

export interface DomainScore {
  domain: string;
  score: number;
  level: RiskLevel;
}

export interface RiskHistoryPoint {
  date: string;
  score: number;
}

export interface DomainHistoryPoint {
  date: string;
  score: number;
  level: RiskLevel;
}

export type DomainHistoryMap = Record<string, DomainHistoryPoint[]>;
