'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  BarChart3, 
  TrendingUp, 
  MapPin, 
  Droplets,
  Calendar,
  Download
} from 'lucide-react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'

// Sample data
const monthlyPredictions = [
  { month: 'Jan', predictions: 45, aquifers: 32 },
  { month: 'Feb', predictions: 52, aquifers: 38 },
  { month: 'Mar', predictions: 61, aquifers: 44 },
  { month: 'Apr', predictions: 58, aquifers: 41 },
  { month: 'May', predictions: 67, aquifers: 49 },
  { month: 'Jun', predictions: 73, aquifers: 54 },
]

const confidenceDistribution = [
  { range: '0-20%', count: 12 },
  { range: '20-40%', count: 28 },
  { range: '40-60%', count: 45 },
  { range: '60-80%', count: 89 },
  { range: '80-100%', count: 156 },
]

const regionData = [
  { name: 'Central', value: 145, color: '#1890ff' },
  { name: 'Eastern', value: 98, color: '#52c41a' },
  { name: 'Western', value: 76, color: '#faad14' },
  { name: 'Coastal', value: 54, color: '#f5222d' },
  { name: 'Northern', value: 32, color: '#722ed1' },
]

const rechargeData = [
  { month: 'Jan', actual: 45, forecast: 42 },
  { month: 'Feb', actual: 52, forecast: 49 },
  { month: 'Mar', actual: 61, forecast: 58 },
  { month: 'Apr', actual: 48, forecast: 51 },
  { month: 'May', actual: 55, forecast: 53 },
  { month: 'Jun', actual: 62, forecast: 60 },
]

export default function AnalyticsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [timeRange, setTimeRange] = useState('6m')

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
                <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
                <p className="text-muted-foreground mt-1">
                  Comprehensive insights into aquifer predictions and forecasts
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-lg border bg-card p-1">
                  {['1m', '3m', '6m', '1y'].map((range) => (
                    <Button
                      key={range}
                      variant={timeRange === range ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => setTimeRange(range)}
                    >
                      {range}
                    </Button>
                  ))}
                </div>
                <Button>
                  <Download className="mr-2 h-4 w-4" />
                  Export Report
                </Button>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Total Predictions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">1,247</div>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    +12.5% from last period
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Aquifers Found
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">856</div>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    68.6% success rate
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Avg Confidence
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">87.3%</div>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    +2.1% improvement
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Forecast Accuracy
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">92.1%</div>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    RMSE: 4.2mm
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Monthly Predictions */}
              <Card>
                <CardHeader>
                  <CardTitle>Monthly Predictions</CardTitle>
                  <CardDescription>
                    Prediction volume and aquifer detection over time
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={monthlyPredictions}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="month" className="text-xs" />
                        <YAxis className="text-xs" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '0.5rem',
                          }}
                        />
                        <Legend />
                        <Bar dataKey="predictions" fill="#1890ff" name="Total Predictions" />
                        <Bar dataKey="aquifers" fill="#52c41a" name="Aquifers Found" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Confidence Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Confidence Distribution</CardTitle>
                  <CardDescription>
                    Distribution of prediction confidence levels
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={confidenceDistribution}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="range" className="text-xs" />
                        <YAxis className="text-xs" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '0.5rem',
                          }}
                        />
                        <Bar dataKey="count" fill="#1890ff" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Charts Row 2 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Regional Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Regional Distribution</CardTitle>
                  <CardDescription>
                    Predictions by region across Kenya
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={regionData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {regionData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Forecast Accuracy */}
              <Card>
                <CardHeader>
                  <CardTitle>Forecast vs Actual Recharge</CardTitle>
                  <CardDescription>
                    Model accuracy over time
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={rechargeData}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="month" className="text-xs" />
                        <YAxis className="text-xs" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '0.5rem',
                          }}
                        />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="actual" 
                          stroke="#52c41a" 
                          strokeWidth={2}
                          name="Actual"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="forecast" 
                          stroke="#1890ff" 
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          name="Forecast"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Model Performance */}
            <Card>
              <CardHeader>
                <CardTitle>Model Performance Metrics</CardTitle>
                <CardDescription>
                  Detailed performance indicators for ML models
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-sm">Aquifer Classifier</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">ROC-AUC</span>
                        <span className="font-medium">0.923</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Precision</span>
                        <span className="font-medium">0.891</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Recall</span>
                        <span className="font-medium">0.876</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">F1-Score</span>
                        <span className="font-medium">0.883</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-semibold text-sm">Recharge Forecaster</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">RMSE</span>
                        <span className="font-medium">4.2 mm</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">MAE</span>
                        <span className="font-medium">3.1 mm</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">R²</span>
                        <span className="font-medium">0.912</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">MAPE</span>
                        <span className="font-medium">6.8%</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-semibold text-sm">Feature Importance</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">TWI</span>
                        <span className="font-medium">0.234</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">SPI-3</span>
                        <span className="font-medium">0.198</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Elevation</span>
                        <span className="font-medium">0.176</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">SPEI-6</span>
                        <span className="font-medium">0.145</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
