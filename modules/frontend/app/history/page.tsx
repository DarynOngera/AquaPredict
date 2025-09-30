'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  History as HistoryIcon, 
  MapPin, 
  Calendar,
  Droplets,
  TrendingUp,
  Trash2,
  Eye,
  Download
} from 'lucide-react'
import { formatCoordinate, formatProbability, getPredictionBadgeColor, formatDate } from '@/lib/utils'

// Sample history data
const predictionHistory = [
  {
    id: 1,
    location: { lat: -1.2921, lon: 36.8219 },
    prediction: 'present',
    probability: 0.89,
    timestamp: '2024-01-15T14:30:00Z',
    type: 'aquifer',
  },
  {
    id: 2,
    location: { lat: -0.0917, lon: 34.7680 },
    prediction: 'absent',
    probability: 0.34,
    timestamp: '2024-01-15T13:45:00Z',
    type: 'aquifer',
  },
  {
    id: 3,
    location: { lat: 0.5143, lon: 35.2698 },
    prediction: 'present',
    probability: 0.92,
    timestamp: '2024-01-15T12:20:00Z',
    type: 'aquifer',
  },
  {
    id: 4,
    location: { lat: -3.2192, lon: 40.1169 },
    prediction: 'present',
    probability: 0.76,
    timestamp: '2024-01-15T11:10:00Z',
    type: 'aquifer',
  },
  {
    id: 5,
    location: { lat: 1.4419, lon: 38.5619 },
    prediction: 'absent',
    probability: 0.28,
    timestamp: '2024-01-15T10:05:00Z',
    type: 'aquifer',
  },
]

const forecastHistory = [
  {
    id: 1,
    location: { lat: -1.2921, lon: 36.8219 },
    horizon: 12,
    avgRecharge: 45.3,
    timestamp: '2024-01-15T14:00:00Z',
    type: 'forecast',
  },
  {
    id: 2,
    location: { lat: 0.5143, lon: 35.2698 },
    horizon: 12,
    avgRecharge: 52.1,
    timestamp: '2024-01-15T11:30:00Z',
    type: 'forecast',
  },
]

export default function HistoryPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState<'predictions' | 'forecasts'>('predictions')

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6 space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">Prediction History</h1>
                <p className="text-muted-foreground mt-1">
                  View and manage your past predictions and forecasts
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  Export History
                </Button>
                <Button variant="destructive">
                  <Trash2 className="mr-2 h-4 w-4" />
                  Clear All
                </Button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Predictions</p>
                      <p className="text-2xl font-bold mt-1">{predictionHistory.length}</p>
                    </div>
                    <Droplets className="h-8 w-8 text-aqua-600 dark:text-aqua-400" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Forecasts</p>
                      <p className="text-2xl font-bold mt-1">{forecastHistory.length}</p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-green-600 dark:text-green-400" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Locations Analyzed</p>
                      <p className="text-2xl font-bold mt-1">
                        {new Set([...predictionHistory, ...forecastHistory].map(h => `${h.location.lat},${h.location.lon}`)).size}
                      </p>
                    </div>
                    <MapPin className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Tabs */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-4 border-b -mb-6">
                  <button
                    onClick={() => setActiveTab('predictions')}
                    className={`pb-4 px-1 font-medium transition-colors border-b-2 ${
                      activeTab === 'predictions'
                        ? 'border-primary text-primary'
                        : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Aquifer Predictions ({predictionHistory.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('forecasts')}
                    className={`pb-4 px-1 font-medium transition-colors border-b-2 ${
                      activeTab === 'forecasts'
                        ? 'border-primary text-primary'
                        : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Recharge Forecasts ({forecastHistory.length})
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                {activeTab === 'predictions' ? (
                  <div className="space-y-3">
                    {predictionHistory.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-4 flex-1">
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-aqua-500 to-aqua-700 flex items-center justify-center">
                            <Droplets className="h-5 w-5 text-white" />
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium">
                                {formatCoordinate(item.location.lat, 'lat')}, {formatCoordinate(item.location.lon, 'lon')}
                              </span>
                              <Badge className={getPredictionBadgeColor(item.prediction)}>
                                {item.prediction}
                              </Badge>
                            </div>
                            
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              <span>Confidence: {formatProbability(item.probability)}</span>
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {formatDate(item.timestamp)}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {forecastHistory.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-4 flex-1">
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-green-500 to-green-700 flex items-center justify-center">
                            <TrendingUp className="h-5 w-5 text-white" />
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium">
                                {formatCoordinate(item.location.lat, 'lat')}, {formatCoordinate(item.location.lon, 'lon')}
                              </span>
                              <Badge variant="secondary">
                                {item.horizon} months
                              </Badge>
                            </div>
                            
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              <span>Avg Recharge: {item.avgRecharge.toFixed(1)} mm</span>
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {formatDate(item.timestamp)}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
