'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { MapView } from '@/components/map/map-view'
import { PredictionPanel } from '@/components/prediction/prediction-panel'
import { useStore } from '@/lib/store'

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { selectedLocation } = useStore()

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen((open) => !open)} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          open={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          onToggle={() => setSidebarOpen((open) => !open)}
        />
        
        <main className="flex-1 overflow-hidden flex flex-col">
          {/* Main Content Area */}
          <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
            {/* Map Section */}
            <div className="flex-1 relative">
              <MapView />
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
