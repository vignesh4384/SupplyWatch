import { useEffect, useRef, useCallback, useState } from 'react';
import L from 'leaflet';
import type { RiskZone, TradeRoute } from '../types/risk';

interface MapViewProps {
  zones: RiskZone[];
  routes: TradeRoute[];
  flyToTarget: RiskZone | null;
}

type LayerFilter = 'all' | 'economic' | 'disaster' | 'maritime' | 'geopolitical';

const riskColors: Record<string, string> = {
  HIGH: '#ef4444',
  MEDIUM: '#f59e0b',
  LOW: '#10b981',
};

const routeColors: Record<string, string> = {
  critical: '#ef4444',
  disrupted: '#f59e0b',
  normal: '#10b981',
};

export default function MapView({ zones, routes, flyToTarget }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const initRef = useRef(false);
  const [activeLayer, setActiveLayer] = useState<LayerFilter>('all');
  const layerGroupsRef = useRef<Record<string, L.LayerGroup>>({});

  const initMap = useCallback(() => {
    if (!containerRef.current || initRef.current) return;
    initRef.current = true;

    const map = L.map(containerRef.current, {
      center: [20, 30],
      zoom: 2.5,
      zoomControl: false,
      attributionControl: false,
    });

    // Use CartoDB Positron (English labels) with dark filter
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    // Zone bubbles by category
    const categories = ['economic', 'disaster', 'maritime', 'geopolitical'];
    categories.forEach(cat => {
      const group = L.layerGroup();
      zones.filter(z => z.category === cat).forEach(zone => {
        const color = riskColors[zone.riskLevel];
        const r = 6 + zone.score / 14;

        // Outer glow
        L.circleMarker([zone.lat, zone.lng], {
          radius: r + 6,
          fillColor: color,
          fillOpacity: 0.15,
          stroke: false,
        }).addTo(group);

        // Inner dot
        L.circleMarker([zone.lat, zone.lng], {
          radius: r,
          fillColor: color,
          fillOpacity: 0.7,
          color: '#fff',
          weight: 1,
          opacity: 0.3,
        }).bindPopup(`
          <div style="font-family:Inter,sans-serif;min-width:200px">
            <div style="font-weight:700;font-size:14px;margin-bottom:4px">${zone.name}</div>
            <div style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;color:${color};background:${color}20;margin-bottom:6px">${zone.riskLevel} &bull; ${zone.score}</div>
            <div style="font-size:12px;color:#666;line-height:1.4">${zone.description}</div>
          </div>
        `, { className: 'custom-popup' }).addTo(group);
      });
      group.addTo(map);
      layerGroupsRef.current[cat] = group;
    });

    // Trade route polylines
    const routeGroup = L.layerGroup();
    routes.forEach(route => {
      L.polyline(route.points as L.LatLngExpression[], {
        color: routeColors[route.status],
        weight: 2,
        dashArray: '8 6',
        opacity: 0.6,
      }).addTo(routeGroup);
    });
    routeGroup.addTo(map);
    layerGroupsRef.current['routes'] = routeGroup;

    mapRef.current = map;
  }, [zones, routes]);

  useEffect(() => {
    initMap();
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        initRef.current = false;
      }
    };
  }, [initMap]);

  // Handle flyTo
  useEffect(() => {
    if (flyToTarget && mapRef.current) {
      mapRef.current.flyTo([flyToTarget.lat, flyToTarget.lng], 5, { duration: 1.5 });
    }
  }, [flyToTarget]);

  // Handle layer filtering
  useEffect(() => {
    const groups = layerGroupsRef.current;
    const map = mapRef.current;
    if (!map) return;

    const categories = ['economic', 'disaster', 'maritime', 'geopolitical'];
    categories.forEach(cat => {
      if (groups[cat]) {
        if (activeLayer === 'all' || activeLayer === cat) {
          map.addLayer(groups[cat]);
        } else {
          map.removeLayer(groups[cat]);
        }
      }
    });
  }, [activeLayer]);

  const layers: { label: string; value: LayerFilter }[] = [
    { label: 'All Risks', value: 'all' },
    { label: 'Economic', value: 'economic' },
    { label: 'Disasters', value: 'disaster' },
    { label: 'Maritime', value: 'maritime' },
    { label: 'Geopolitical', value: 'geopolitical' },
  ];

  return (
    <div className="flex-1 relative">
      {/* Layer toggle bar */}
      <div className="absolute top-3.5 left-1/2 -translate-x-1/2 z-[1000] flex gap-0.5 p-[3px] rounded-xl bg-bg-card border border-border">
        {layers.map(layer => (
          <button
            key={layer.value}
            onClick={() => setActiveLayer(layer.value)}
            className={`px-3.5 py-1.5 rounded-lg text-[10px] font-semibold transition-all ${
              activeLayer === layer.value
                ? 'bg-accent text-white'
                : 'text-text-dim hover:text-text-muted'
            }`}
          >
            {layer.label}
          </button>
        ))}
      </div>

      {/* Map container */}
      <div ref={containerRef} className="w-full h-full dark-tiles" />

      {/* Info badge */}
      <div className="absolute bottom-4 right-4 z-[1000] bg-bg-card border border-border rounded-lg px-3.5 py-2 font-mono text-[10px] text-text-dim">
        <div>{zones.length} Active Risk Zones</div>
        <div className="mt-0.5">{routes.length} Trade Routes Monitored</div>
      </div>
    </div>
  );
}
