'use client'

import { type ReactElement, type ReactNode, useEffect, useMemo, useState } from 'react'
import { CloudRain, Droplets, MapPin, RefreshCw, ThermometerSun, Wind } from 'lucide-react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? ''

const LOCATIONS = [
  { name: 'Nairobi', latitude: -1.286389, longitude: 36.817223 },
  { name: 'Mombasa', latitude: -4.043477, longitude: 39.668206 },
  { name: 'Kisumu', latitude: -0.10221, longitude: 34.76171 },
  { name: 'Eldoret', latitude: 0.514277, longitude: 35.26978 },
]

const RANGES = [
  { label: '1m', days: 30 },
  { label: '3m', days: 90 },
  { label: '6m', days: 180 },
  { label: '1y', days: 365 },
]

type WeatherDay = {
  date: string
  temperature_max: number | null
  temperature_min: number | null
  temperature_mean: number | null
  precipitation: number | null
  precipitation_hours: number | null
  wind_speed_max: number | null
  et0: number | null
  weather_code: number | null
}

type WeatherAnalytics = {
  status: string
  data_source: string
  location: { latitude: number; longitude: number; timezone: string }
  current: {
    temperature_2m?: number
    relative_humidity_2m?: number
    precipitation?: number
    wind_speed_10m?: number
  }
  summary: {
    days: number
    total_precipitation: number
    average_temperature: number | null
    rainy_days: number
    max_wind_speed: number | null
    total_et0: number
  }
  daily: WeatherDay[]
}

function chartDate(date: string, days: number) {
  const parsed = new Date(`${date}T00:00:00`)
  return parsed.toLocaleDateString(undefined, days > 90 ? { month: 'short', year: '2-digit' } : { month: 'short', day: 'numeric' })
}

function displayNumber(value: number | null | undefined, suffix = '') {
  return value === null || value === undefined ? '—' : `${value.toFixed(1)}${suffix}`
}

export default function AnalyticsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedLocation, setSelectedLocation] = useState(LOCATIONS[0])
  const [days, setDays] = useState(30)
  const [data, setData] = useState<WeatherAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const activeRange = RANGES.find((range) => range.days === days)?.label

  async function loadAnalytics() {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        latitude: String(selectedLocation.latitude),
        longitude: String(selectedLocation.longitude),
        days: String(days),
      })
      const response = await fetch(`${API_URL}/api/v1/analytics/weather?${params}`)
      const payload = await response.json().catch(() => null)
      if (!response.ok || !payload || payload.status !== 'success') {
        throw new Error(payload?.detail || 'Unable to load weather analytics')
      }
      setData(payload)
    } catch (requestError) {
      setData(null)
      setError(requestError instanceof Error ? requestError.message : 'Unable to load weather analytics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadAnalytics()
  }, [selectedLocation, days])

  const chartData = useMemo(() => (data?.daily ?? []).map((day) => ({
    ...day,
    label: chartDate(day.date, days),
    precipitation: day.precipitation ?? 0,
    et0: day.et0 ?? 0,
  })), [data, days])

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto space-y-6 p-6">
            <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
              <div>
                <div className="mb-2 flex items-center gap-3">
                  <h1 className="text-3xl font-bold">Weather Analytics</h1>
                  <Badge className="bg-sky-600 text-white">Open-Meteo live data</Badge>
                </div>
                <p className="text-muted-foreground">
                  Observed and current weather conditions for groundwater planning.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <label className="sr-only" htmlFor="analytics-location">Location</label>
                <select
                  id="analytics-location"
                  className="h-9 rounded-md border bg-background px-3 text-sm"
                  value={selectedLocation.name}
                  onChange={(event) => setSelectedLocation(LOCATIONS.find((location) => location.name === event.target.value) ?? LOCATIONS[0])}
                >
                  {LOCATIONS.map((location) => <option key={location.name}>{location.name}</option>)}
                </select>
                <div className="flex items-center rounded-lg border bg-card p-1">
                  {RANGES.map((range) => (
                    <Button key={range.days} variant={activeRange === range.label ? 'default' : 'ghost'} size="sm" onClick={() => setDays(range.days)}>
                      {range.label}
                    </Button>
                  ))}
                </div>
                <Button variant="outline" size="sm" onClick={() => void loadAnalytics()} disabled={loading}>
                  <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
                </Button>
              </div>
            </div>

            <Card className="border-sky-200 bg-gradient-to-r from-sky-50 to-cyan-50 dark:border-sky-900 dark:from-sky-950 dark:to-cyan-950">
              <CardContent className="flex flex-col gap-3 pt-6 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <MapPin className="h-6 w-6 text-sky-700" />
                  <div>
                    <p className="font-semibold">{selectedLocation.name}, Kenya</p>
                    <p className="text-sm text-muted-foreground">
                      {data ? `${data.location.latitude.toFixed(3)}, ${data.location.longitude.toFixed(3)} · ${data.location.timezone}` : 'Loading location data…'}
                    </p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">Source: Open-Meteo Weather Forecast API</p>
              </CardContent>
            </Card>

            {error && <Card className="border-destructive"><CardContent className="pt-6 text-sm text-destructive">{error}. Try refreshing in a moment.</CardContent></Card>}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard icon={<CloudRain className="h-5 w-5 text-sky-600" />} label={`Rainfall · ${data?.summary.days ?? days} days`} value={loading ? '…' : displayNumber(data?.summary.total_precipitation, ' mm')} hint={`${data?.summary.rainy_days ?? 0} rainy days`} />
              <MetricCard icon={<ThermometerSun className="h-5 w-5 text-orange-500" />} label="Average temperature" value={loading ? '…' : displayNumber(data?.summary.average_temperature, ' °C')} hint={`Current: ${displayNumber(data?.current.temperature_2m, ' °C')}`} />
              <MetricCard icon={<Wind className="h-5 w-5 text-slate-600" />} label="Maximum wind" value={loading ? '…' : displayNumber(data?.summary.max_wind_speed, ' km/h')} hint={`Current: ${displayNumber(data?.current.wind_speed_10m, ' km/h')}`} />
              <MetricCard icon={<Droplets className="h-5 w-5 text-cyan-600" />} label="Reference ET₀" value={loading ? '…' : displayNumber(data?.summary.total_et0, ' mm')} hint="Reference evapotranspiration" />
            </div>

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
              <ChartCard title="Daily precipitation" description="Total precipitation recorded or forecast for each day.">
                <BarChart data={chartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" minTickGap={28} /><YAxis unit=" mm" /><Tooltip /><Bar dataKey="precipitation" name="Precipitation" fill="#0284c7" radius={[3, 3, 0, 0]} /></BarChart>
              </ChartCard>
              <ChartCard title="Temperature range" description="Daily minimum, mean, and maximum air temperature at 2 m.">
                <LineChart data={chartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" minTickGap={28} /><YAxis unit=" °C" /><Tooltip /><Legend /><Line type="monotone" dataKey="temperature_min" name="Minimum" stroke="#38bdf8" dot={false} /><Line type="monotone" dataKey="temperature_mean" name="Mean" stroke="#f59e0b" dot={false} /><Line type="monotone" dataKey="temperature_max" name="Maximum" stroke="#ef4444" dot={false} /></LineChart>
              </ChartCard>
            </div>

            <ChartCard title="Precipitation and reference evapotranspiration" description="ET₀ is a climatic water-demand indicator, not measured groundwater recharge.">
              <AreaChart data={chartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" minTickGap={28} /><YAxis unit=" mm" /><Tooltip /><Legend /><Area type="monotone" dataKey="precipitation" name="Precipitation" stroke="#0284c7" fill="#7dd3fc" fillOpacity={0.7} /><Area type="monotone" dataKey="et0" name="Reference ET₀" stroke="#d97706" fill="#fcd34d" fillOpacity={0.55} /></AreaChart>
            </ChartCard>
          </div>
        </main>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, hint }: { icon: ReactNode; label: string; value: string; hint: string }) {
  return <Card><CardHeader className="pb-2"><div className="flex items-center justify-between"><CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>{icon}</div></CardHeader><CardContent><p className="text-3xl font-bold">{value}</p><p className="mt-1 text-xs text-muted-foreground">{hint}</p></CardContent></Card>
}

function ChartCard({ title, description, children }: { title: string; description: string; children: ReactElement }) {
  return <Card><CardHeader><CardTitle>{title}</CardTitle><CardDescription>{description}</CardDescription></CardHeader><CardContent><div className="h-80"><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div></CardContent></Card>
}
