'use client'

import { type ReactNode, useState } from 'react'
import { Calendar, Download, Droplets, History as HistoryIcon, MapPin, Trash2, TrendingUp } from 'lucide-react'

import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useStore } from '@/lib/store'
import { formatCoordinate, formatDate, formatProbability, getPredictionBadgeColor } from '@/lib/utils'

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export default function HistoryPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState<'predictions' | 'forecasts'>('predictions')
  const [exporting, setExporting] = useState(false)
  const {
    predictionHistory,
    forecastHistory,
    clearHistory,
    removePredictionHistory,
    removeForecastHistory,
  } = useStore()

  const uniqueLocations = new Set([...predictionHistory, ...forecastHistory].map((item) => `${item.location.lat},${item.location.lon}`)).size

  const exportHistory = async () => {
    setExporting(true)
    try {
      const blob = await api.exportData('history', 'csv', { history: predictionHistory })
      download(blob, `aquapredict-history-${new Date().toISOString().slice(0, 10)}.csv`)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen((open) => !open)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} onToggle={() => setSidebarOpen((open) => !open)} />
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto space-y-6 p-6">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <h1 className="text-3xl font-bold">Prediction History</h1>
                <p className="mt-1 text-muted-foreground">Real analyses created in this browser are retained for the demo.</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => void exportHistory()} disabled={exporting || predictionHistory.length === 0}>
                  <Download className="mr-2 h-4 w-4" />{exporting ? 'Exporting…' : 'Export CSV'}
                </Button>
                <Button variant="destructive" onClick={clearHistory} disabled={predictionHistory.length + forecastHistory.length === 0}>
                  <Trash2 className="mr-2 h-4 w-4" />Clear history
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Metric label="Aquifer predictions" value={predictionHistory.length} icon={<Droplets className="h-8 w-8 text-aqua-600" />} />
              <Metric label="Recharge forecasts" value={forecastHistory.length} icon={<TrendingUp className="h-8 w-8 text-green-600" />} />
              <Metric label="Locations analysed" value={uniqueLocations} icon={<MapPin className="h-8 w-8 text-purple-600" />} />
            </div>

            <Card>
              <CardHeader>
                <div className="flex gap-5 border-b">
                  <button className={`border-b-2 pb-3 text-sm font-medium ${activeTab === 'predictions' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`} onClick={() => setActiveTab('predictions')}>Aquifer predictions ({predictionHistory.length})</button>
                  <button className={`border-b-2 pb-3 text-sm font-medium ${activeTab === 'forecasts' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`} onClick={() => setActiveTab('forecasts')}>Recharge forecasts ({forecastHistory.length})</button>
                </div>
              </CardHeader>
              <CardContent>
                {activeTab === 'predictions' ? (
                  predictionHistory.length === 0 ? <EmptyState message="Run an aquifer prediction from the map to create your first history record." /> :
                    <div className="space-y-3">{predictionHistory.map((item) => <div key={item.id} className="flex items-center justify-between gap-4 rounded-lg border p-4"><div className="flex items-center gap-3"><div className="rounded-full bg-aqua-600 p-2.5"><Droplets className="h-5 w-5 text-white" /></div><div><div className="mb-1 flex flex-wrap items-center gap-2"><span className="font-medium">{formatCoordinate(item.location.lat, 'lat')}, {formatCoordinate(item.location.lon, 'lon')}</span><Badge className={getPredictionBadgeColor(item.prediction)}>{item.prediction}</Badge></div><p className="text-sm text-muted-foreground">Confidence {formatProbability(item.probability)} · <span className="inline-flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(item.timestamp)}</span></p></div></div><Button variant="ghost" size="icon" aria-label="Remove prediction" onClick={() => removePredictionHistory(item.id)}><Trash2 className="h-4 w-4" /></Button></div>)}</div>
                ) : (
                  forecastHistory.length === 0 ? <EmptyState message="Generate a recharge forecast from the map to create your first history record." /> :
                    <div className="space-y-3">{forecastHistory.map((item) => <div key={item.id} className="flex items-center justify-between gap-4 rounded-lg border p-4"><div className="flex items-center gap-3"><div className="rounded-full bg-green-600 p-2.5"><TrendingUp className="h-5 w-5 text-white" /></div><div><div className="mb-1 flex flex-wrap items-center gap-2"><span className="font-medium">{formatCoordinate(item.location.lat, 'lat')}, {formatCoordinate(item.location.lon, 'lon')}</span><Badge variant="secondary">{item.forecast.length} months</Badge></div><p className="text-sm text-muted-foreground"><span className="inline-flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(item.timestamp)}</span></p></div></div><Button variant="ghost" size="icon" aria-label="Remove forecast" onClick={() => removeForecastHistory(item.id)}><Trash2 className="h-4 w-4" /></Button></div>)}</div>
                )}
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}

function Metric({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
  return <Card><CardContent className="flex items-center justify-between pt-6"><div><p className="text-sm text-muted-foreground">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p></div>{icon}</CardContent></Card>
}

function EmptyState({ message }: { message: string }) {
  return <div className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground"><HistoryIcon className="h-8 w-8" /><p>{message}</p></div>
}
