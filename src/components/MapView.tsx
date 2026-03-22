import { useEffect, useRef, useCallback, useState } from 'react';
import L from 'leaflet';
import type { RiskZone, TradeRoute, VesselFeature, VesselProperties } from '../types/risk';
import { api } from '../lib/api';

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

// Vessel marker colors by type
const vesselColors: Record<string, string> = {
  Tanker: '#f59e0b',      // amber
  Cargo: '#06b6d4',       // cyan
  Passenger: '#8b5cf6',   // purple
  default: '#94a3b8',     // slate
  dark: '#ef4444',        // red
};

function getVesselColor(props: VesselProperties): string {
  if (props.is_dark) return vesselColors.dark;
  return vesselColors[props.ship_type_label] || vesselColors.default;
}

function createVesselIcon(props: VesselProperties): L.DivIcon {
  const color = getVesselColor(props);
  const size = props.is_dark ? 12 : 10;
  const pulseClass = props.is_dark ? 'vessel-pulse' : '';

  return L.divIcon({
    className: 'vessel-marker',
    html: `<div class="${pulseClass}" style="
      width:${size}px;height:${size}px;
      background:${color};
      border-radius:50%;
      border:1.5px solid rgba(255,255,255,0.8);
      box-shadow:0 0 ${props.is_dark ? 8 : 4}px ${color}80;
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function vesselPopupHtml(props: VesselProperties): string {
  const color = getVesselColor(props);
  const darkBadge = props.is_dark
    ? '<span style="background:#ef4444;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-left:6px">DARK</span>'
    : '';
  const ago = getTimeAgo(props.recorded_at);
  return `
    <div style="font-family:Inter,system-ui,sans-serif;min-width:220px">
      <div style="font-weight:700;font-size:13px;margin-bottom:2px">${props.name}${darkBadge}</div>
      <div style="font-size:11px;color:#64748b;margin-bottom:6px">MMSI: ${props.mmsi}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px 12px;font-size:11px">
        <div><span style="color:#94a3b8">Type:</span> <span style="color:${color};font-weight:600">${props.ship_type_label}</span></div>
        <div><span style="color:#94a3b8">Zone:</span> ${props.zone}</div>
        <div><span style="color:#94a3b8">Speed:</span> ${props.speed?.toFixed(1) ?? '—'} kts</div>
        <div><span style="color:#94a3b8">Heading:</span> ${props.heading?.toFixed(0) ?? '—'}°</div>
        <div><span style="color:#94a3b8">Status:</span> ${props.nav_status_label}</div>
        <div><span style="color:#94a3b8">Updated:</span> ${ago}</div>
      </div>
    </div>
  `;
}

function getTimeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// Inject CSS for vessel pulse animation (once)
const styleId = 'vessel-pulse-style';
if (typeof document !== 'undefined' && !document.getElementById(styleId)) {
  const style = document.createElement('style');
  style.id = styleId;
  style.textContent = `
    @keyframes vesselPulse { 0%,100%{box-shadow:0 0 4px #ef444480} 50%{box-shadow:0 0 12px #ef4444cc} }
    .vessel-pulse { animation: vesselPulse 1.5s ease-in-out infinite; }
    .vessel-marker { background: transparent !important; border: none !important; }
  `;
  document.head.appendChild(style);
}

export default function MapView({ zones, routes, flyToTarget }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const initRef = useRef(false);
  const [activeLayer, setActiveLayer] = useState<LayerFilter>('all');
  const layerGroupsRef = useRef<Record<string, L.LayerGroup>>({});
  const vesselMarkersRef = useRef<Map<string, L.Marker>>(new Map());
  const vesselLastSeenRef = useRef<Map<string, number>>(new Map());
  const trackLayerRef = useRef<L.LayerGroup | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [vesselCount, setVesselCount] = useState(0);
  const [showVessels, setShowVessels] = useState(true);
  const showVesselsRef = useRef(true);

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

    // Vessel layers
    const vesselLayer = L.layerGroup().addTo(map);
    layerGroupsRef.current['vessels'] = vesselLayer;

    const trackLayer = L.layerGroup();
    layerGroupsRef.current['tracks'] = trackLayer;
    trackLayerRef.current = trackLayer;

    mapRef.current = map;
  }, [zones, routes]);

  // Add or update a vessel marker
  const upsertVessel = useCallback((feature: VesselFeature) => {
    const map = mapRef.current;
    const vesselLayer = layerGroupsRef.current['vessels'];
    if (!map || !vesselLayer) return;

    const props = feature.properties;
    const mmsi = props.mmsi;
    const [lng, lat] = feature.geometry.coordinates;

    vesselLastSeenRef.current.set(mmsi, Date.now());

    const existing = vesselMarkersRef.current.get(mmsi);
    if (existing) {
      // Move existing marker
      existing.setLatLng([lat, lng]);
      existing.setIcon(createVesselIcon(props));
      existing.setPopupContent(vesselPopupHtml(props));
    } else {
      // Create new marker
      const marker = L.marker([lat, lng], { icon: createVesselIcon(props) })
        .bindPopup(vesselPopupHtml(props), { className: 'custom-popup' });

      // Click handler: fetch and draw vessel track
      marker.on('click', async () => {
        try {
          const data = await api.getVesselHistory(mmsi, 24);
          const trackLayer = trackLayerRef.current;
          if (trackLayer && data.track.length > 1) {
            trackLayer.clearLayers();
            const points: L.LatLngExpression[] = data.track.map(p => [p.lat, p.lng]);
            L.polyline(points, {
              color: getVesselColor(props),
              weight: 2,
              opacity: 0.7,
              dashArray: '4 4',
            }).addTo(trackLayer);
            trackLayer.addTo(map);
          }
        } catch {
          // Silently fail track fetch
        }
      });

      marker.addTo(vesselLayer);
      vesselMarkersRef.current.set(mmsi, marker);
      setVesselCount(vesselMarkersRef.current.size);
    }
  }, []);

  // Load vessels via REST + WebSocket
  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let cleanupTimer: ReturnType<typeof setInterval>;
    let cancelled = false;

    // Load initial vessel positions via REST (with retry until map is ready)
    const loadInitial = () => {
      api.getLiveVessels().then(fc => {
        if (cancelled) return;
        // Retry if map not ready yet
        if (!mapRef.current || !layerGroupsRef.current['vessels']) {
          setTimeout(loadInitial, 1000);
          return;
        }
        fc.features.forEach(f => upsertVessel(f));
      }).catch(() => {});
    };
    setTimeout(loadInitial, 500);

    // WebSocket for live updates
    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/vessels/live`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          try {
            const feature: VesselFeature = JSON.parse(event.data);
            if (showVesselsRef.current) {
              upsertVessel(feature);
            }
          } catch {
            // Skip malformed messages
          }
        };

        ws.onclose = () => {
          wsRef.current = null;
          reconnectTimer = setTimeout(connect, 5000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        reconnectTimer = setTimeout(connect, 5000);
      }
    }

    connect();

    // Cleanup stale markers every 60s (remove if not seen in 15 min)
    cleanupTimer = setInterval(() => {
      const now = Date.now();
      const staleThreshold = 15 * 60 * 1000;
      const vesselLayer = layerGroupsRef.current['vessels'];

      vesselLastSeenRef.current.forEach((lastSeen, mmsi) => {
        if (now - lastSeen > staleThreshold) {
          const marker = vesselMarkersRef.current.get(mmsi);
          if (marker && vesselLayer) {
            vesselLayer.removeLayer(marker);
          }
          vesselMarkersRef.current.delete(mmsi);
          vesselLastSeenRef.current.delete(mmsi);
        }
      });
      setVesselCount(vesselMarkersRef.current.size);
    }, 60000);

    return () => {
      cancelled = true;
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
      clearTimeout(reconnectTimer);
      clearInterval(cleanupTimer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  // Toggle vessel layer visibility
  useEffect(() => {
    showVesselsRef.current = showVessels;
    const map = mapRef.current;
    const vesselLayer = layerGroupsRef.current['vessels'];
    if (!map || !vesselLayer) return;

    if (showVessels) {
      map.addLayer(vesselLayer);
    } else {
      map.removeLayer(vesselLayer);
    }
  }, [showVessels]);

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
        <button
          onClick={() => setShowVessels(v => !v)}
          className={`px-3.5 py-1.5 rounded-lg text-[10px] font-semibold transition-all ${
            showVessels
              ? 'bg-cyan-600 text-white'
              : 'text-text-dim hover:text-text-muted'
          }`}
        >
          Vessels ({vesselCount})
        </button>
      </div>

      {/* Map container */}
      <div ref={containerRef} className="w-full h-full dark-tiles" />

      {/* Info badge */}
      <div className="absolute bottom-4 right-4 z-[1000] bg-bg-card border border-border rounded-lg px-3.5 py-2 font-mono text-[10px] text-text-dim">
        <div>{zones.length} Active Risk Zones</div>
        <div className="mt-0.5">{routes.length} Trade Routes Monitored</div>
        {vesselCount > 0 && (
          <div className="mt-0.5 text-cyan-400">{vesselCount} Live Vessels (AIS)</div>
        )}
      </div>
    </div>
  );
}
