'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { 
  Database, 
  Layers, 
  MapPin,
  Calendar,
  Info,
  Eye,
  RefreshCw
} from 'lucide-react'

interface Dataset {
  id: string
  name: string
  collection: string
  description: string
  band: string
  unit: string
  temporal_resolution: string
  spatial_resolution: string
  visualization: {
    min: number
    max: number
    palette: string[]
  }
  default_center: {
    lat: number
    lon: number
    zoom: number
  }
}

export default function DatasetsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [loading, setLoading] = useState(true)
  const [geeAvailable, setGeeAvailable] = useState(false)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await api.getDataSources()
      setDatasets(response.gee.datasets || [])
      setGeeAvailable(response.gee.available)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    } finally {
      setLoading(false)
    }
  }

  const ColorPalette = ({ colors }: { colors: string[] }) => (
    <div className="flex gap-1 h-6 rounded overflow-hidden">
      {colors.map((color, idx) => (
        <div
          key={idx}
          className="flex-1"
          style={{ backgroundColor: `#${color}` }}
          title={`#${color}`}
        />
      ))}
    </div>
  )

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading datasets...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6 space-y-6">
            {/* Page Header */}
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <Database className="h-8 w-8" />
                GEE Datasets
              </h1>
              <p className="text-muted-foreground mt-1">
                Google Earth Engine datasets used for aquifer prediction
              </p>
              
              {!geeAvailable && (
                <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    ⚠️ Google Earth Engine is not available. Configure GEE credentials to preview datasets.
                  </p>
                </div>
              )}
            </div>

            {/* Datasets Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {datasets.map((dataset) => (
                <Card 
                  key={dataset.id}
                  className="hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => setSelectedDataset(dataset)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <Layers className="h-5 w-5" />
                          {dataset.name}
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {dataset.description}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-4">
                    {/* Dataset Info */}
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Collection:</span>
                        <span className="font-mono text-xs">{dataset.collection.split('/').pop()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Band:</span>
                        <Badge variant="outline">{dataset.band}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Unit:</span>
                        <span>{dataset.unit}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Resolution:</span>
                        <span>{dataset.spatial_resolution}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Temporal:</span>
                        <Badge variant="secondary">{dataset.temporal_resolution}</Badge>
                      </div>
                    </div>

                    {/* Color Palette */}
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Visualization Palette:</p>
                      <ColorPalette colors={dataset.visualization.palette} />
                      <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                        <span>Min: {dataset.visualization.min}</span>
                        <span>Max: {dataset.visualization.max}</span>
                      </div>
                    </div>

                    {/* Preview Button */}
                    <Button 
                      className="w-full" 
                      variant="outline"
                      disabled={!geeAvailable}
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedDataset(dataset)
                      }}
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      Preview on Map
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Selected Dataset Detail */}
            {selectedDataset && (
              <Card className="border-2 border-primary">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{selectedDataset.name}</span>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setSelectedDataset(null)}
                    >
                      Close
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    Full dataset information and preview
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <Info className="h-4 w-4" />
                        Dataset Details
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">Full Collection:</span>
                          <p className="font-mono text-xs mt-1 p-2 bg-muted rounded">
                            {selectedDataset.collection}
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Description:</span>
                          <p className="mt-1">{selectedDataset.description}</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <MapPin className="h-4 w-4" />
                        Default View
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Latitude:</span>
                          <span>{selectedDataset.default_center.lat}°</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Longitude:</span>
                          <span>{selectedDataset.default_center.lon}°</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Zoom Level:</span>
                          <span>{selectedDataset.default_center.zoom}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {geeAvailable && (
                    <div className="pt-4 border-t">
                      <p className="text-sm text-muted-foreground mb-2">
                        🚧 Map preview will be available in the next update. 
                        The backend is ready to serve GEE tiles via <code className="bg-muted px-1 py-0.5 rounded">/api/v1/data/preview/{selectedDataset.id}</code>
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
