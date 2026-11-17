'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { MapView } from '@/components/map/map-view'
import { PredictionPanel } from '@/components/prediction/prediction-panel'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useStore } from '@/lib/store'

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showWelcome, setShowWelcome] = useState(true)
  const { selectedLocation, setSelectedLocation } = useStore()

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          open={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />
        
        <main className="flex-1 overflow-hidden flex flex-col">
          {/* Main Content Area */}
          <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
            {/* Map Section */}
            <div className="flex-1 relative">
              <MapView />
              
              {!selectedLocation && showWelcome && (
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[1000] pointer-events-none px-4">
                  <Card className="shadow-2xl pointer-events-auto w-full max-w-lg border-2 border-blue-200 dark:border-blue-800 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md">
                    <CardHeader className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-t-lg">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-center flex-1 text-base sm:text-lg">🌊 Welcome to AquaPredict</CardTitle>
                        <button
                          onClick={() => setShowWelcome(false)}
                          className="text-white hover:bg-white/20 rounded-full p-1 transition-colors"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <p className="text-sm text-gray-700 dark:text-gray-300 text-center mb-4 leading-relaxed">
                        Click anywhere on the map to select a location and start analyzing groundwater potential.
                        The map shows aquifer zones, historical predictions, and existing water infrastructure.
                      </p>
                      <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3 space-y-2.5">
                        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Map Features:</p>
                        <div className="flex items-center gap-2.5">
                          <div className="w-4 h-4 rounded bg-green-500 shadow-sm"></div>
                          <span className="text-xs text-gray-700 dark:text-gray-300">High potential aquifer zones</span>
                        </div>
                        <div className="flex items-center gap-2.5">
                          <div className="w-4 h-4 rounded bg-yellow-500 shadow-sm"></div>
                          <span className="text-xs text-gray-700 dark:text-gray-300">Moderate potential zones</span>
                        </div>
                        <div className="flex items-center gap-2.5">
                          <div className="w-4 h-4 rounded bg-red-500 shadow-sm"></div>
                          <span className="text-xs text-gray-700 dark:text-gray-300">Low potential zones</span>
                        </div>
                        <div className="flex items-center gap-2.5">
                          <div className="w-4 h-4 rounded-full bg-blue-500 shadow-sm"></div>
                          <span className="text-xs text-gray-700 dark:text-gray-300">Active infrastructure & historical data</span>
                        </div>
                      </div>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedLocation({ lat: -1.2921, lon: 36.8219 })
                            setShowWelcome(false)
                          }}
                          className="mt-4 w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
                        >
                          Analyze Nairobi demo location
                        </button>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>

            {/* Prediction Panel - Responsive */}
            {selectedLocation && (
              <div className="w-full md:w-96 border-t md:border-t-0 md:border-l bg-white dark:bg-gray-900 shadow-xl overflow-y-auto max-h-96 md:max-h-none">
                <PredictionPanel />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
