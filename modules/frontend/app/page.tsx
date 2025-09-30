'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { MapView } from '@/components/map/map-view'
import { PredictionPanel } from '@/components/prediction/prediction-panel'
import { StatsOverview } from '@/components/dashboard/stats-overview'
import { useStore } from '@/lib/store'

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { selectedLocation, prediction } = useStore()

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <main className="flex-1 overflow-hidden">
          <div className="h-full flex flex-col">
            {/* Stats Overview */}
            <div className="p-4 border-b bg-card">
              <StatsOverview />
            </div>

            {/* Map and Prediction Panel */}
            <div className="flex-1 flex overflow-hidden">
              {/* Map */}
              <div className="flex-1 relative">
                <MapView />
              </div>

              {/* Prediction Panel - Slides in when location selected */}
              {selectedLocation && (
                <div className="w-96 border-l bg-card overflow-y-auto animate-slide-in">
                  <PredictionPanel />
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
