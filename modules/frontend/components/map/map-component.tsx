'use client'

import { type FormEvent, useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle, Polygon, useMap, useMapEvents, LayersControl, GeoJSON } from 'react-leaflet'
import { Icon, LatLng } from 'leaflet'
import { useStore } from '@/lib/store'
import { MapPin, Droplet, AlertTriangle, CheckCircle, Minus, Plus, Search, XCircle } from 'lucide-react'
import 'leaflet/dist/leaflet.css'

// Realistic Kenya aquifer zones (simplified)
const kenyaAquiferZones = [
  {
    name: 'Lake Victoria Basin',
    coordinates: [[0.5, 33.9], [0.5, 34.8], [-0.5, 34.8], [-0.5, 33.9]],
    type: 'high_potential',
    description: 'High groundwater potential - Volcanic and sedimentary aquifers',
    depth: '20-80m',
    yield: '5-15 L/s'
  },
  {
    name: 'Rift Valley Aquifer System',
    coordinates: [[1.5, 35.8], [1.5, 36.5], [-1.5, 36.5], [-1.5, 35.8]],
    type: 'moderate_potential',
    description: 'Moderate potential - Fractured volcanic rocks',
    depth: '30-120m',
    yield: '2-8 L/s'
  },
  {
    name: 'Coastal Sedimentary Basin',
    coordinates: [[-2.5, 40.0], [-2.5, 41.5], [-4.5, 41.5], [-4.5, 40.0]],
    type: 'high_potential',
    description: 'High potential - Coastal sedimentary aquifers',
    depth: '15-60m',
    yield: '8-20 L/s'
  },
  {
    name: 'Northern Kenya Basement',
    coordinates: [[2.0, 36.5], [2.0, 38.0], [4.0, 38.0], [4.0, 36.5]],
    type: 'low_potential',
    description: 'Low potential - Crystalline basement rocks',
    depth: '40-150m',
    yield: '0.5-3 L/s'
  }
]

// Simulated historical predictions
const historicalPredictions = [
  { lat: -1.2921, lon: 36.8219, probability: 0.85, result: 'success', depth: 45, yield: 12 },
  { lat: 0.0236, lon: 37.9062, probability: 0.72, result: 'success', depth: 68, yield: 8 },
  { lat: -0.4172, lon: 36.9583, probability: 0.45, result: 'low_yield', depth: 95, yield: 2 },
  { lat: -3.2191, lon: 40.1169, probability: 0.91, result: 'success', depth: 32, yield: 18 },
  { lat: 1.2833, lon: 36.8167, probability: 0.38, result: 'failure', depth: 120, yield: 0 },
  { lat: -0.0917, lon: 34.7680, probability: 0.78, result: 'success', depth: 52, yield: 10 },
  { lat: -1.9536, lon: 37.2611, probability: 0.68, result: 'success', depth: 75, yield: 6 },
  { lat: 0.5143, lon: 35.2698, probability: 0.82, result: 'success', depth: 38, yield: 14 },
]

// Water infrastructure (boreholes, wells)
const waterInfrastructure = [
  { lat: -1.2921, lon: 36.8219, type: 'borehole', status: 'active', name: 'Nairobi Central BH-001' },
  { lat: -0.0917, lon: 34.7680, type: 'borehole', status: 'active', name: 'Kisumu BH-045' },
  { lat: -3.2191, lon: 40.1169, type: 'borehole', status: 'active', name: 'Malindi BH-023' },
  { lat: 0.5143, lon: 35.2698, type: 'well', status: 'active', name: 'Eldoret Well-012' },
  { lat: -1.9536, lon: 37.2611, type: 'borehole', status: 'maintenance', name: 'Embu BH-067' },
]

// Fix for default marker icon
const createCustomIcon = (color: string = '#1890ff') => {
  return new Icon({
    iconUrl: 'data:image/svg+xml;base64,' + btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
        <circle cx="12" cy="10" r="3"></circle>
      </svg>
    `),
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  })
}

const createPredictionIcon = (result: string) => {
  const color = result === 'success' ? '#10b981' : result === 'low_yield' ? '#f59e0b' : '#ef4444'
  return createCustomIcon(color)
}

const createInfrastructureIcon = (status: string) => {
  const color = status === 'active' ? '#3b82f6' : '#9ca3af'
  return new Icon({
    iconUrl: 'data:image/svg+xml;base64,' + btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="${color}" stroke="white" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 6v12M8 12h8" stroke="white" stroke-width="2"></path>
      </svg>
    `),
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  })
}

const getZoneColor = (type: string) => {
  switch (type) {
    case 'high_potential': return '#10b981'
    case 'moderate_potential': return '#f59e0b'
    case 'low_potential': return '#ef4444'
    default: return '#6b7280'
  }
}

function MapClickHandler() {
  const { setSelectedLocation } = useStore()

  useMapEvents({
    click: (e) => {
      setSelectedLocation({
        lat: e.latlng.lat,
        lon: e.latlng.lng,
      })
    },
  })

  return null
}

function FlyToSearchTarget() {
  const map = useMap()
  const searchTarget = useStore((state) => state.searchTarget)

  useEffect(() => {
    if (searchTarget) {
      // Search is the only selection path that recenters and zooms. Map clicks
      // leave the current viewport untouched while opening the prediction panel.
      const frame = requestAnimationFrame(() => {
        map.invalidateSize({ animate: false, pan: false })
        map.setView([searchTarget.lat, searchTarget.lon], Math.max(map.getZoom(), 11), { animate: false })
      })
      return () => cancelAnimationFrame(frame)
    }
  }, [map, searchTarget])

  return null
}

function MapResizeHandler() {
  const map = useMap()

  useEffect(() => {
    const container = map.getContainer()
    const observer = new ResizeObserver(() => map.invalidateSize({ animate: false, pan: false }))
    observer.observe(container)
    return () => observer.disconnect()
  }, [map])

  return null
}

type SearchResult = {
  name: string
  latitude: number
  longitude: number
  country?: string
  admin1?: string
}

function parseCoordinates(query: string) {
  const match = query.trim().match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/)
  if (!match) return null

  const lat = Number(match[1])
  const lon = Number(match[2])
  return Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180
    ? { lat, lon }
    : null
}

function MapSearch() {
  const { setSelectedLocation, setSearchTarget } = useStore()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const selectLocation = (lat: number, lon: number) => {
    const location = { lat, lon }
    setSelectedLocation(location)
    setSearchTarget(location)
    setQuery(`${lat.toFixed(5)}, ${lon.toFixed(5)}`)
    setResults([])
    setMessage(null)
  }

  const search = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const coordinates = parseCoordinates(query)
    if (coordinates) {
      selectLocation(coordinates.lat, coordinates.lon)
      return
    }
    if (query.trim().length < 2) {
      setMessage('Enter at least two characters, or coordinates as latitude, longitude.')
      return
    }

    setLoading(true)
    setMessage(null)
    try {
      const response = await fetch(`/api/v1/analytics/locations?name=${encodeURIComponent(query.trim())}`)
      const payload = await response.json().catch(() => null)
      if (!response.ok || !payload || payload.status !== 'success') {
        throw new Error(payload?.detail || 'Location search is unavailable')
      }
      setResults(payload.results)
      if (payload.results.length === 0) setMessage('No locations found. Try including a county or country.')
    } catch (error) {
      setResults([])
      setMessage(error instanceof Error ? error.message : 'Location search is unavailable')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="absolute left-4 top-4 z-[1000] w-[min(22rem,calc(100%-2rem))]">
      <form onSubmit={search} className="flex rounded-lg border bg-white/95 p-1 shadow-lg backdrop-blur-md dark:bg-gray-900/95">
        <label className="sr-only" htmlFor="map-location-search">Search location or coordinates</label>
        <input
          id="map-location-search"
          value={query}
          onChange={(event) => { setQuery(event.target.value); setResults([]); setMessage(null) }}
          placeholder="Search place or -1.286, 36.817"
          className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm outline-none"
          autoComplete="off"
        />
        <button type="submit" className="rounded-md bg-blue-600 px-3 text-white hover:bg-blue-700 disabled:opacity-60" disabled={loading} aria-label="Search map">
          <Search className="h-4 w-4" />
        </button>
      </form>
      {(message || results.length > 0) && (
        <div className="mt-1 overflow-hidden rounded-lg border bg-white/95 shadow-lg backdrop-blur-md dark:bg-gray-900/95">
          {message && <p className="px-3 py-2 text-xs text-muted-foreground">{message}</p>}
          {results.map((result) => (
            <button
              key={`${result.latitude}-${result.longitude}`}
              type="button"
              onClick={() => selectLocation(result.latitude, result.longitude)}
              className="block w-full border-b px-3 py-2.5 text-left text-sm last:border-b-0 hover:bg-muted"
            >
              <span className="block font-medium">{result.name}</span>
              <span className="block text-xs text-muted-foreground">{[result.admin1, result.country].filter(Boolean).join(', ') || `${result.latitude.toFixed(4)}, ${result.longitude.toFixed(4)}`}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function MapComponent() {
  const { mapCenter, mapZoom, selectedLocation } = useStore()
  const mapRef = useRef<any>(null)
  const [showAquiferZones, setShowAquiferZones] = useState(true)
  const [showHistoricalData, setShowHistoricalData] = useState(true)
  const [showInfrastructure, setShowInfrastructure] = useState(true)
  const [mapLayer, setMapLayer] = useState<'street' | 'satellite'>('street')
  const [legendOpen, setLegendOpen] = useState(true)

  useEffect(() => {
    // Invalidate size when component mounts
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current?.invalidateSize()
      }, 100)
    }
  }, [])

  return (
    <div className="h-full w-full relative">
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        className="dashboard-map h-full w-full"
        ref={mapRef}
        zoomControl={false}
      >
        {/* Base Layers */}
        {mapLayer === 'street' ? (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        ) : (
          <TileLayer
            attribution='Tiles &copy; Esri'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
        )}

        <MapClickHandler />
        <FlyToSearchTarget />
        <MapResizeHandler />

        {/* Aquifer Zones */}
        {showAquiferZones && kenyaAquiferZones.map((zone, idx) => (
          <Polygon
            key={idx}
            positions={zone.coordinates as any}
            pathOptions={{
              color: getZoneColor(zone.type),
              fillColor: getZoneColor(zone.type),
              fillOpacity: 0.2,
              weight: 2,
            }}
          >
            <Popup>
              <div className="p-2 min-w-[200px]">
                <p className="font-bold text-sm mb-1">{zone.name}</p>
                <p className="text-xs text-gray-600 mb-2">{zone.description}</p>
                <div className="text-xs space-y-1">
                  <p><span className="font-semibold">Typical Depth:</span> {zone.depth}</p>
                  <p><span className="font-semibold">Expected Yield:</span> {zone.yield}</p>
                </div>
              </div>
            </Popup>
          </Polygon>
        ))}

        {/* Historical Predictions */}
        {showHistoricalData && historicalPredictions.map((pred, idx) => (
          <Marker
            key={`pred-${idx}`}
            position={[pred.lat, pred.lon]}
            icon={createPredictionIcon(pred.result)}
          >
            <Popup>
              <div className="p-2">
                <p className="font-semibold text-sm mb-1">Historical Prediction</p>
                <div className="text-xs space-y-1">
                  <p><span className="font-semibold">Probability:</span> {(pred.probability * 100).toFixed(0)}%</p>
                  <p><span className="font-semibold">Result:</span> 
                    <span className={`ml-1 px-1.5 py-0.5 rounded text-white ${
                      pred.result === 'success' ? 'bg-green-500' :
                      pred.result === 'low_yield' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}>
                      {pred.result.replace('_', ' ')}
                    </span>
                  </p>
                  <p><span className="font-semibold">Depth:</span> {pred.depth}m</p>
                  <p><span className="font-semibold">Yield:</span> {pred.yield} L/s</p>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Water Infrastructure */}
        {showInfrastructure && waterInfrastructure.map((infra, idx) => (
          <Marker
            key={`infra-${idx}`}
            position={[infra.lat, infra.lon]}
            icon={createInfrastructureIcon(infra.status)}
          >
            <Popup>
              <div className="p-2">
                <p className="font-semibold text-sm">{infra.name}</p>
                <div className="text-xs mt-1 space-y-1">
                  <p><span className="font-semibold">Type:</span> {infra.type}</p>
                  <p><span className="font-semibold">Status:</span> 
                    <span className={`ml-1 px-1.5 py-0.5 rounded text-white ${
                      infra.status === 'active' ? 'bg-blue-500' : 'bg-gray-500'
                    }`}>
                      {infra.status}
                    </span>
                  </p>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Selected Location */}
        {selectedLocation && (
          <>
            <Marker
              position={[selectedLocation.lat, selectedLocation.lon]}
              icon={createCustomIcon('#1890ff')}
            >
              <Popup>
                <div className="p-2">
                  <p className="font-semibold text-sm">Selected Location</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {selectedLocation.lat.toFixed(4)}°, {selectedLocation.lon.toFixed(4)}°
                  </p>
                  <p className="text-xs text-aqua-600 dark:text-aqua-400 mt-2">
                    Click "Predict" to analyze this location
                  </p>
                </div>
              </Popup>
            </Marker>
            {/* Radius circle showing analysis area */}
            <Circle
              center={[selectedLocation.lat, selectedLocation.lon]}
              radius={5000}
              pathOptions={{
                color: '#1890ff',
                fillColor: '#1890ff',
                fillOpacity: 0.1,
                weight: 2,
                dashArray: '5, 5'
              }}
            />
          </>
        )}
      </MapContainer>

      <MapSearch />

      {/* Custom zoom controls stay clear of the location search field. */}
      <div className="absolute left-4 top-24 z-[1000] overflow-hidden rounded-lg border border-blue-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-900">
        <button
          type="button"
          onClick={() => mapRef.current?.zoomIn()}
          className="flex h-10 w-10 items-center justify-center border-b text-gray-700 transition-colors hover:bg-blue-50 hover:text-blue-700 dark:text-gray-200 dark:hover:bg-gray-800 dark:hover:text-blue-300"
          aria-label="Zoom in"
          title="Zoom in"
        >
          <Plus className="h-5 w-5" strokeWidth={2.5} />
        </button>
        <button
          type="button"
          onClick={() => mapRef.current?.zoomOut()}
          className="flex h-10 w-10 items-center justify-center text-gray-700 transition-colors hover:bg-blue-50 hover:text-blue-700 dark:text-gray-200 dark:hover:bg-gray-800 dark:hover:text-blue-300"
          aria-label="Zoom out"
          title="Zoom out"
        >
          <Minus className="h-5 w-5" strokeWidth={2.5} />
        </button>
      </div>

      {/* Layer Controls */}
      <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
        <div className="rounded-lg bg-white/98 dark:bg-gray-900/98 backdrop-blur-md border-2 border-gray-200 dark:border-gray-700 shadow-2xl p-4">
          <p className="text-sm font-bold mb-3 text-gray-900 dark:text-white flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            Map Layers
          </p>
          <div className="space-y-2.5">
            <label className="flex items-center gap-2.5 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={showAquiferZones}
                onChange={(e) => setShowAquiferZones(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-gray-700 dark:text-gray-300 font-medium">Aquifer Zones</span>
            </label>
            <label className="flex items-center gap-2.5 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={showHistoricalData}
                onChange={(e) => setShowHistoricalData(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-gray-700 dark:text-gray-300 font-medium">Historical Data</span>
            </label>
            <label className="flex items-center gap-2.5 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 p-2 rounded transition-colors">
              <input
                type="checkbox"
                checked={showInfrastructure}
                onChange={(e) => setShowInfrastructure(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-gray-700 dark:text-gray-300 font-medium">Infrastructure</span>
            </label>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm font-bold mb-2 text-gray-900 dark:text-white">Base Map</p>
            <div className="flex gap-2">
              <button
                onClick={() => setMapLayer('street')}
                className={`flex-1 text-sm px-3 py-2 rounded-lg font-medium transition-all ${
                  mapLayer === 'street'
                    ? 'bg-blue-500 text-white shadow-md'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                Street
              </button>
              <button
                onClick={() => setMapLayer('satellite')}
                className={`flex-1 text-sm px-3 py-2 rounded-lg font-medium transition-all ${
                  mapLayer === 'satellite'
                    ? 'bg-blue-500 text-white shadow-md'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                Satellite
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] flex flex-col gap-2">
        <div className="rounded-lg bg-white/98 dark:bg-gray-900/98 backdrop-blur-md border-2 border-gray-200 dark:border-gray-700 shadow-2xl p-4 max-w-xs">
          <div className="flex items-center justify-between gap-4">
            <p className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Legend
            </p>
            <button
              type="button"
              onClick={() => setLegendOpen((open) => !open)}
              aria-expanded={legendOpen}
              aria-controls="map-legend-content"
              aria-label={legendOpen ? 'Collapse map legend' : 'Expand map legend'}
              className="rounded p-1 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={legendOpen ? 'm18 15-6-6-6 6' : 'm6 9 6 6 6-6'} />
              </svg>
            </button>
          </div>
          {legendOpen && <div id="map-legend-content" className="mt-3 space-y-2.5 text-sm">
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-2">
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Aquifer Zones</p>
              <div className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded shadow-sm" style={{ backgroundColor: '#10b981', opacity: 0.7 }}></div>
                <span className="text-gray-700 dark:text-gray-300">High Potential</span>
              </div>
              <div className="flex items-center gap-2.5 mt-1.5">
                <div className="w-5 h-5 rounded shadow-sm" style={{ backgroundColor: '#f59e0b', opacity: 0.7 }}></div>
                <span className="text-gray-700 dark:text-gray-300">Moderate Potential</span>
              </div>
              <div className="flex items-center gap-2.5 mt-1.5">
                <div className="w-5 h-5 rounded shadow-sm" style={{ backgroundColor: '#ef4444', opacity: 0.7 }}></div>
                <span className="text-gray-700 dark:text-gray-300">Low Potential</span>
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-2">
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Historical Data</p>
              <div className="flex items-center gap-2.5">
                <div className="w-4 h-4 rounded-full bg-green-500 shadow-sm"></div>
                <span className="text-gray-700 dark:text-gray-300">Successful Borehole</span>
              </div>
              <div className="flex items-center gap-2.5 mt-1.5">
                <div className="w-4 h-4 rounded-full bg-yellow-500 shadow-sm"></div>
                <span className="text-gray-700 dark:text-gray-300">Low Yield</span>
              </div>
              <div className="flex items-center gap-2.5 mt-1.5">
                <div className="w-4 h-4 rounded-full bg-red-500 shadow-sm"></div>
                <span className="text-gray-700 dark:text-gray-300">Failed Borehole</span>
              </div>
              <div className="flex items-center gap-2.5 mt-1.5">
                <div className="w-4 h-4 rounded-full bg-blue-500 shadow-sm"></div>
                <span className="text-gray-700 dark:text-gray-300">Active Infrastructure</span>
              </div>
            </div>
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              💡 Click anywhere on the map to select a location for analysis
            </p>
          </div>
          </div>}
        </div>
      </div>
    </div>
  )
}
