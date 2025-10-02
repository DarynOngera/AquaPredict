'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { MapView } from '@/components/map/map-view'
import { PredictionPanel } from '@/components/prediction/prediction-panel'
import OracleDashboard from '@/components/oracle-dashboard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useStore } from '@/lib/store'
import { Droplets, TrendingUp, Activity, AlertTriangle } from 'lucide-react'

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showWelcome, setShowWelcome] = useState(true)
  const { selectedLocation, prediction } = useStore()

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <main className="flex-1 overflow-hidden flex flex-col">
          {/* Quick Stats Bar */}
          <div className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-gray-900 dark:to-gray-800 px-6 py-4 shadow-sm">
            <div className="grid grid-cols-4 gap-4">
              <div className="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                <div className="rounded-lg bg-blue-500 p-2.5">
                  <Droplets className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Total Predictions</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">1,247</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                <div className="rounded-lg bg-green-500 p-2.5">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Success Rate</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">87.3%</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                <div className="rounded-lg bg-purple-500 p-2.5">
                  <Activity className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Active Wells</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">342</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                <div className="rounded-lg bg-yellow-500 p-2.5">
                  <AlertTriangle className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Areas at Risk</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">23</p>
                </div>
              </div>
            </div>
          </div>

          {/* Oracle Cloud Dashboard */}
          <div className="px-6 py-4 border-b bg-white dark:bg-gray-900">
            <OracleDashboard />
          </div>

          {/* Main Content Area */}
          <div className="flex-1 overflow-hidden flex">
            {/* Map Section */}
            <div className="flex-1 relative">
              <MapView />
              
              {!selectedLocation && showWelcome && (
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[1000] pointer-events-none">
                  <Card className="shadow-2xl pointer-events-auto max-w-lg border-2 border-blue-200 dark:border-blue-800 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md">
                    <CardHeader className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-t-lg">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-center flex-1 text-lg">🌊 Welcome to AquaPredict</CardTitle>
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
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>

            {/* Prediction Panel */}
            {selectedLocation && (
              <div className="w-96 border-l bg-white dark:bg-gray-900 shadow-xl overflow-y-auto">
                <PredictionPanel />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
