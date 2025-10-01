'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  MapPin,
  Calendar,
  BarChart3,
  X,
  Loader2
} from 'lucide-react'
import { api } from '@/lib/api'

interface DatasetPreviewProps {
  dataset: any
  onClose: () => void
}

export function DatasetPreview({ dataset, onClose }: DatasetPreviewProps) {
  const [loading, setLoading] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)
  const [location, setLocation] = useState({ lat: 0.0236, lon: 37.9062 })

  const loadPreview = async () => {
    setLoading(true)
    try {
      const data = await api.getDatasetPreview(
        dataset.id,
        'kenya',
        undefined,
        undefined
      )
      setPreviewData(data)
    } catch (error) {
      console.error('Failed to load preview:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatValue = (value: number, decimals: number = 2) => {
    if (value === null || value === undefined) return 'N/A'
    return typeof value === 'number' ? value.toFixed(decimals) : value
  }

  return (
    <Card className="border-2 border-primary">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              {dataset.name} - Data Preview
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {dataset.description}
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Location Input */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
          <div>
            <Label htmlFor="lat">Latitude</Label>
            <Input
              id="lat"
              type="number"
              step="0.0001"
              value={location.lat}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocation({ ...location, lat: parseFloat(e.target.value) })}
              placeholder="0.0236"
            />
          </div>
          <div>
            <Label htmlFor="lon">Longitude</Label>
            <Input
              id="lon"
              type="number"
              step="0.0001"
              value={location.lon}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocation({ ...location, lon: parseFloat(e.target.value) })}
              placeholder="37.9062"
            />
          </div>
          <div className="col-span-2">
            <Button onClick={loadPreview} disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading Data...
                </>
              ) : (
                <>
                  <MapPin className="mr-2 h-4 w-4" />
                  Load Preview
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Preview Data */}
        {previewData && previewData.statistics && (
          <div className="space-y-4">
            {/* Statistics Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {previewData.statistics.min !== undefined && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <TrendingDown className="h-4 w-4" />
                      Minimum
                    </div>
                    <div className="text-2xl font-bold mt-2">
                      {formatValue(previewData.statistics.min)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {previewData.statistics.unit}
                    </div>
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
                    <div className="text-2xl font-bold mt-2">
                      {formatValue(previewData.statistics.max)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {previewData.statistics.unit}
                    </div>
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
                    <div className="text-2xl font-bold mt-2">
                      {formatValue(previewData.statistics.mean)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {previewData.statistics.unit}
                    </div>
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
                    <div className="text-2xl font-bold mt-2">
                      {formatValue(previewData.statistics.std)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {previewData.statistics.unit}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Dataset-Specific Information */}
            {dataset.id === 'srtm' && previewData.statistics.elevation !== undefined && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Elevation Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Point Elevation</p>
                      <p className="text-lg font-semibold">
                        {formatValue(previewData.statistics.elevation, 0)}m
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Slope</p>
                      <p className="text-lg font-semibold">
                        {formatValue(previewData.statistics.slope, 1)}°
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Regional Min</p>
                      <p className="text-lg font-semibold">
                        {formatValue(previewData.statistics.regional_min, 0)}m
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Regional Max</p>
                      <p className="text-lg font-semibold">
                        {formatValue(previewData.statistics.regional_max, 0)}m
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {dataset.id === 'worldcover' && previewData.statistics.class_name && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Land Cover Classification</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Class</p>
                      <p className="text-2xl font-bold">{previewData.statistics.class_name}</p>
                    </div>
                    <Badge variant="outline" className="text-lg px-4 py-2">
                      {previewData.statistics.class_value}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Resolution: {previewData.statistics.resolution} | Year: {previewData.statistics.year}
                  </p>
                </CardContent>
              </Card>
            )}

            {dataset.id === 'sentinel2' && previewData.statistics.interpretation && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">NDVI Interpretation</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Vegetation Status</p>
                      <p className="text-xl font-bold">{previewData.statistics.interpretation}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">NDVI Value</p>
                      <p className="text-2xl font-bold">{formatValue(previewData.statistics.mean, 3)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Time Series Chart (for CHIRPS) */}
            {previewData.statistics.time_series && previewData.statistics.time_series.values.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    Time Series (Last 90 Days)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-48 flex items-end justify-between gap-1">
                    {previewData.statistics.time_series.values.slice(-30).map((value: number, idx: number) => {
                      const maxValue = Math.max(...previewData.statistics.time_series.values)
                      const height = (value / maxValue) * 100
                      return (
                        <div
                          key={idx}
                          className="flex-1 bg-primary rounded-t transition-all hover:opacity-80"
                          style={{ height: `${height}%`, minHeight: '2px' }}
                          title={`${value.toFixed(1)} ${previewData.statistics.unit}`}
                        />
                      )
                    })}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2 text-center">
                    Showing last 30 days of data
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Metadata */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {previewData.statistics.total_images && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Images:</span>
                    <span className="font-semibold">{previewData.statistics.total_images}</span>
                  </div>
                )}
                {previewData.statistics.date_range && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Date Range:</span>
                    <span className="font-semibold">
                      {previewData.statistics.date_range[0]} to {previewData.statistics.date_range[1]}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Location:</span>
                  <span className="font-semibold">
                    {location.lat.toFixed(4)}°, {location.lon.toFixed(4)}°
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {!previewData && !loading && (
          <div className="text-center py-12 text-muted-foreground">
            <MapPin className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Enter coordinates and click "Load Preview" to see dataset statistics</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
