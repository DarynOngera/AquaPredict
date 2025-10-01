'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import { 
  Database, 
  Layers, 
  MapPin,
  Info,
  Eye,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Loader2
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
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)
  const [region, setRegion] = useState('kenya')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })

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

  const loadPreview = async (dataset: Dataset) => {
    setSelectedDataset(dataset)
    setPreviewLoading(true)
    setPreviewData(null)
    try {
      const data = await api.getDatasetPreview(
        dataset.id,
        region,
        dateRange.start || undefined,
        dateRange.end || undefined
      )
      setPreviewData(data)
    } catch (error) {
      console.error('Failed to load preview:', error)
    } finally {
      setPreviewLoading(false)
    }
  }

  const formatValue = (value: number | undefined, decimals: number = 2) => {
    if (value === null || value === undefined) return 'N/A'
    return typeof value === 'number' ? value.toFixed(decimals) : value
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
                        loadPreview(dataset)
                      }}
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      Load Data Preview
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Enhanced Dataset Preview */}
            {selectedDataset && (
              <Card className="border-2 border-primary">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        {selectedDataset.name} - Live Data Preview
                      </CardTitle>
                      <CardDescription className="mt-1">
                        Real-time statistics from Google Earth Engine
                      </CardDescription>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => {
                      setSelectedDataset(null)
                      setPreviewData(null)
                    }}>
                      <RefreshCw className="h-5 w-5" />
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="space-y-6">
                  {/* Region and Date Range Selector */}
                  <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
                    <div>
                      <Label htmlFor="region">Region</Label>
                      <select
                        id="region"
                        value={region}
                        onChange={(e) => setRegion(e.target.value)}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="kenya">All Kenya</option>
                        <option value="nairobi">Nairobi</option>
                        <option value="mombasa">Mombasa</option>
                        <option value="mt_kenya">Mt. Kenya</option>
                        <option value="turkana">Turkana</option>
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="start">Start Date</Label>
                      <Input
                        id="start"
                        type="date"
                        value={dateRange.start}
                        onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="end">End Date</Label>
                      <Input
                        id="end"
                        type="date"
                        value={dateRange.end}
                        onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="flex justify-center">
                    <Button onClick={() => loadPreview(selectedDataset)} disabled={previewLoading} size="lg">
                      {previewLoading ? (
                        <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Loading Regional Data...</>
                      ) : (
                        <><MapPin className="mr-2 h-4 w-4" />Load Preview</>
                      )}
                    </Button>
                  </div>

                  {/* Statistics Cards */}
                  {previewData?.statistics && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {previewData.statistics.min !== undefined && (
                          <Card>
                            <CardContent className="pt-6">
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <TrendingDown className="h-4 w-4" />
                                Minimum
                              </div>
                              <div className="text-2xl font-bold mt-2">{formatValue(previewData.statistics.min)}</div>
                              <div className="text-xs text-muted-foreground">{previewData.statistics.unit}</div>
                            </CardContent>
                          </Card>
                        )}
                        {previewData.statistics.max !== undefined && (
                          <Card>
                            <CardContent className="pt-6">
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <TrendingUp className="h-4 w-4" />
                                Maximum
                              </div>
                              <div className="text-2xl font-bold mt-2">{formatValue(previewData.statistics.max)}</div>
                              <div className="text-xs text-muted-foreground">{previewData.statistics.unit}</div>
                            </CardContent>
                          </Card>
                        )}
                        {previewData.statistics.mean !== undefined && (
                          <Card>
                            <CardContent className="pt-6">
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Activity className="h-4 w-4" />
                                Mean
                              </div>
                              <div className="text-2xl font-bold mt-2">{formatValue(previewData.statistics.mean)}</div>
                              <div className="text-xs text-muted-foreground">{previewData.statistics.unit}</div>
                            </CardContent>
                          </Card>
                        )}
                        {previewData.statistics.std !== undefined && (
                          <Card>
                            <CardContent className="pt-6">
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <BarChart3 className="h-4 w-4" />
                                Std Dev
                              </div>
                              <div className="text-2xl font-bold mt-2">{formatValue(previewData.statistics.std)}</div>
                              <div className="text-xs text-muted-foreground">{previewData.statistics.unit}</div>
                            </CardContent>
                          </Card>
                        )}
                      </div>

                      {/* Dataset-specific details */}
                      {selectedDataset.id === 'srtm' && previewData.statistics.elevation !== undefined && (
                        <Card>
                          <CardHeader><CardTitle className="text-base">Elevation Details</CardTitle></CardHeader>
                          <CardContent className="grid grid-cols-2 gap-4 text-sm">
                            <div><p className="text-muted-foreground">Point Elevation</p><p className="text-lg font-semibold">{formatValue(previewData.statistics.elevation, 0)}m</p></div>
                            <div><p className="text-muted-foreground">Slope</p><p className="text-lg font-semibold">{formatValue(previewData.statistics.slope, 1)}°</p></div>
                            <div><p className="text-muted-foreground">Regional Min</p><p className="text-lg font-semibold">{formatValue(previewData.statistics.regional_min, 0)}m</p></div>
                            <div><p className="text-muted-foreground">Regional Max</p><p className="text-lg font-semibold">{formatValue(previewData.statistics.regional_max, 0)}m</p></div>
                          </CardContent>
                        </Card>
                      )}

                      {selectedDataset.id === 'worldcover' && previewData.statistics.class_name && (
                        <Card>
                          <CardHeader><CardTitle className="text-base">Land Cover</CardTitle></CardHeader>
                          <CardContent>
                            <div className="flex items-center justify-between">
                              <div><p className="text-sm text-muted-foreground">Classification</p><p className="text-2xl font-bold">{previewData.statistics.class_name}</p></div>
                              <Badge variant="outline" className="text-lg px-4 py-2">{previewData.statistics.class_value}</Badge>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {selectedDataset.id === 'sentinel2' && previewData.statistics.interpretation && (
                        <Card>
                          <CardHeader><CardTitle className="text-base">NDVI Analysis</CardTitle></CardHeader>
                          <CardContent>
                            <div className="flex items-center justify-between">
                              <div><p className="text-sm text-muted-foreground">Vegetation</p><p className="text-xl font-bold">{previewData.statistics.interpretation}</p></div>
                              <div className="text-right"><p className="text-sm text-muted-foreground">Value</p><p className="text-2xl font-bold">{formatValue(previewData.statistics.mean, 3)}</p></div>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Time Series */}
                      {previewData.statistics.time_series?.values?.length > 0 && (
                        <Card>
                          <CardHeader><CardTitle className="text-base">Time Series (Last 30 Days)</CardTitle></CardHeader>
                          <CardContent>
                            <div className="h-48 flex items-end justify-between gap-1">
                              {previewData.statistics.time_series.values.slice(-30).map((value: number, idx: number) => {
                                const maxValue = Math.max(...previewData.statistics.time_series.values)
                                const height = (value / maxValue) * 100
                                return <div key={idx} className="flex-1 bg-primary rounded-t hover:opacity-80" style={{ height: `${height}%`, minHeight: '2px' }} title={`${value.toFixed(1)} ${previewData.statistics.unit}`} />
                              })}
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  )}

                  {!previewData && !previewLoading && (
                    <div className="text-center py-12 text-muted-foreground">
                      <MapPin className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Select a region and date range, then click "Load Preview"</p>
                      <p className="text-sm mt-2">Real-time regional statistics from Google Earth Engine</p>
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
