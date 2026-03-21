import type { RiskLevel, AlertSeverity, RouteStatus } from '../types/risk';

export function riskColor(level: RiskLevel): string {
  switch (level) {
    case 'HIGH': return 'var(--color-high-text)';
    case 'MEDIUM': return 'var(--color-medium-text)';
    case 'LOW': return 'var(--color-low-text)';
  }
}

export function riskBg(level: RiskLevel): string {
  switch (level) {
    case 'HIGH': return 'bg-high-bg border-high-border text-high-text';
    case 'MEDIUM': return 'bg-medium-bg border-medium-border text-medium-text';
    case 'LOW': return 'bg-low-bg border-low-border text-low-text';
  }
}

export function severityDotClass(severity: AlertSeverity): string {
  switch (severity) {
    case 'critical': return 'bg-high';
    case 'warning': return 'bg-medium';
    case 'info': return 'bg-cyber';
  }
}

export function routeStatusClass(status: RouteStatus): string {
  switch (status) {
    case 'critical': return 'bg-high-bg border border-high-border text-high-text';
    case 'disrupted': return 'bg-medium-bg border border-medium-border text-medium-text';
    case 'normal': return 'bg-low-bg border border-low-border text-low-text';
  }
}

export function formatValue(value: number, unit: string): string {
  if (unit === '%') return `${value}`;
  if (value >= 1000) return `$${value.toLocaleString()}`;
  if (unit.startsWith('USD')) return `$${value.toFixed(2)}`;
  return value.toLocaleString();
}

export function domainBarGradient(level: RiskLevel): string {
  switch (level) {
    case 'HIGH': return 'from-[#dc2626] to-[#f87171]';
    case 'MEDIUM': return 'from-[#d97706] to-[#fbbf24]';
    case 'LOW': return 'from-[#059669] to-[#34d399]';
  }
}
