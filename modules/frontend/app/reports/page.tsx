'use client'

import { type ReactNode, useState } from 'react'
import { Calendar, Download, FileCheck, FileText, MapPin, Trash2 } from 'lucide-react'

import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { type GeneratedReport, useStore } from '@/lib/store'
import { formatCoordinate, formatDate } from '@/lib/utils'

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export default function ReportsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { predictionHistory, forecastHistory, reports, addReport, removeReport } = useStore()

  const downloadReport = async (report: GeneratedReport) => {
    const blob = await api.exportData('report', 'pdf', {
      prediction: report.prediction,
      forecast: report.forecast,
    })
    download(blob, `${report.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.pdf`)
  }

  const generateReport = async () => {
    const prediction = predictionHistory[0]
    if (!prediction) {
      setError('Run an aquifer prediction first. Reports are generated from real analysis results.')
      return
    }

    setGenerating(true)
    setError(null)
    const forecast = forecastHistory.find((item) => item.location.lat === prediction.location.lat && item.location.lon === prediction.location.lon)
    const report: GeneratedReport = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      title: `Aquifer analysis · ${formatCoordinate(prediction.location.lat, 'lat')}, ${formatCoordinate(prediction.location.lon, 'lon')}`,
      createdAt: new Date().toISOString(),
      prediction,
      forecast,
    }

    try {
      await downloadReport(report)
      addReport(report)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Report generation failed. Please try again.')
    } finally {
      setGenerating(false)
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
                <div className="mb-2 flex items-center gap-3"><h1 className="text-3xl font-bold">Reports</h1><Badge className="bg-aqua-600 text-white">Analysis-backed PDF</Badge></div>
                <p className="text-muted-foreground">Create a report from the latest real aquifer prediction and matching recharge forecast.</p>
              </div>
              <Button size="lg" onClick={() => void generateReport()} disabled={generating || predictionHistory.length === 0}>
                <FileText className="mr-2 h-4 w-4" />{generating ? 'Generating…' : 'Generate report'}
              </Button>
            </div>

            {error && <Card className="border-destructive"><CardContent className="pt-6 text-sm text-destructive">{error}</CardContent></Card>}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <Metric label="Generated reports" value={reports.length} icon={<FileText className="h-8 w-8 text-aqua-600" />} />
              <Metric label="Available predictions" value={predictionHistory.length} icon={<FileCheck className="h-8 w-8 text-green-600" />} />
              <Metric label="Available forecasts" value={forecastHistory.length} icon={<MapPin className="h-8 w-8 text-purple-600" />} />
            </div>

            <Card>
              <CardHeader><CardTitle>Generated reports</CardTitle><CardDescription>Reports are saved here after their PDF is successfully produced.</CardDescription></CardHeader>
              <CardContent>
                {reports.length === 0 ? <div className="py-12 text-center text-muted-foreground"><FileText className="mx-auto mb-3 h-8 w-8" />Run a prediction, then generate a report from that real result.</div> :
                  <div className="space-y-3">{reports.map((report) => <div key={report.id} className="flex flex-col justify-between gap-4 rounded-lg border p-4 sm:flex-row sm:items-center"><div className="flex items-start gap-3"><div className="rounded-lg bg-aqua-600 p-3"><FileText className="h-6 w-6 text-white" /></div><div><div className="mb-1 flex flex-wrap items-center gap-2"><h3 className="font-semibold">{report.title}</h3><Badge className="bg-green-100 text-green-800">Generated</Badge></div><p className="flex items-center gap-1 text-sm text-muted-foreground"><Calendar className="h-3.5 w-3.5" />{formatDate(report.createdAt)}</p><p className="mt-1 text-xs text-muted-foreground">Includes aquifer prediction{report.forecast ? ' and recharge forecast' : ''}.</p></div></div><div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => void downloadReport(report)}><Download className="mr-1 h-4 w-4" />Download</Button><Button variant="ghost" size="icon" aria-label="Remove report" onClick={() => removeReport(report.id)}><Trash2 className="h-4 w-4" /></Button></div></div>)}</div>}
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
