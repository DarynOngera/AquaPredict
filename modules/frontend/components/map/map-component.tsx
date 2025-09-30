'use client'

import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import { Icon, LatLng } from 'leaflet'
import { useStore } from '@/lib/store'
import { MapPin } from 'lucide-react'
import 'leaflet/dist/leaflet.css'

// Fix for default marker icon
const createCustomIcon = () => {
  return new Icon({
    iconUrl: 'data:image/svg+xml;base64,' + btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1890ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
        <circle cx="12" cy="10" r="3"></circle>
      </svg>
    `),
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  })
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

export default function MapComponent() {
  const { mapCenter, mapZoom, selectedLocation } = useStore()
  const mapRef = useRef<any>(null)

  useEffect(() => {
    // Invalidate size when component mounts
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current?.invalidateSize()
      }, 100)
    }
  }, [])

  return (
    <div className="h-full w-full">
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        className="h-full w-full"
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Satellite layer option */}
        {/* <TileLayer
          attribution='Tiles &copy; Esri'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        /> */}

        <MapClickHandler />

        {selectedLocation && (
          <Marker
            position={[selectedLocation.lat, selectedLocation.lon]}
            icon={createCustomIcon()}
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
        )}
      </MapContainer>

      {/* Map Controls Overlay */}
      <div className="absolute bottom-4 left-4 z-[1000] flex flex-col gap-2">
        <div className="rounded-lg bg-card/95 backdrop-blur border shadow-lg p-3">
          <p className="text-xs font-medium text-muted-foreground">
            Click anywhere on the map to select a location
          </p>
        </div>
      </div>
    </div>
  )
}
