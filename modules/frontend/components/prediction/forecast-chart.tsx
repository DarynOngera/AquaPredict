'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Forecast } from '@/lib/store'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'

interface ForecastChartProps {
  forecast: Forecast
}

export function ForecastChart({ forecast }: ForecastChartProps) {
  // Prepare data for chart
  const chartData = forecast.forecast.map((value, index) => ({
    month: `Month ${index + 1}`,
    recharge: value,
    lower: forecast.confidence_intervals?.[index]?.[0] || value * 0.9,
    upper: forecast.confidence_intervals?.[index]?.[1] || value * 1.1,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recharge Forecast</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Chart */}
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorRecharge" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1890ff" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#1890ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="month"
                  className="text-xs"
                  tick={{ fill: 'currentColor' }}
                />
                <YAxis
                  className="text-xs"
                  tick={{ fill: 'currentColor' }}
                  label={{ value: 'Recharge (mm)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '0.5rem',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="upper"
                  stroke="none"
                  fill="#1890ff"
                  fillOpacity={0.1}
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  stroke="none"
                  fill="#1890ff"
                  fillOpacity={0.1}
                />
                <Line
                  type="monotone"
                  dataKey="recharge"
                  stroke="#1890ff"
                  strokeWidth={2}
                  dot={{ fill: '#1890ff', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4 rounded-lg bg-muted/50 p-3">
            <div>
              <p className="text-xs text-muted-foreground">Average</p>
              <p className="text-sm font-semibold">
                {(forecast.forecast.reduce((a, b) => a + b, 0) / forecast.forecast.length).toFixed(1)} mm
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Maximum</p>
              <p className="text-sm font-semibold">
                {Math.max(...forecast.forecast).toFixed(1)} mm
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Minimum</p>
              <p className="text-sm font-semibold">
                {Math.min(...forecast.forecast).toFixed(1)} mm
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
