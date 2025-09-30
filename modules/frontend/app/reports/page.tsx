'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  FileText, 
  Download, 
  Calendar,
  MapPin,
  Droplets,
  TrendingUp,
  CheckCircle2,
  Clock,
  FileCheck
} from 'lucide-react'

const reports = [
  {
    id: 1,
    title: 'Kenya Water Footprint Assessment',
    type: 'ISO 14046',
    region: 'Kenya - National',
    date: '2024-01-15',
    status: 'completed',
    predictions: 1247,
    aquifers: 856,
    size: '4.2 MB',
  },
  {
    id: 2,
    title: 'Central Region Aquifer Analysis',
    type: 'Technical Report',
    region: 'Central Kenya',
    date: '2024-01-10',
    status: 'completed',
    predictions: 342,
    aquifers: 234,
    size: '2.8 MB',
  },
  {
    id: 3,
    title: 'Groundwater Recharge Forecast Q1 2024',
    type: 'Forecast Report',
    region: 'Kenya - National',
    date: '2024-01-05',
    status: 'completed',
    predictions: 856,
    aquifers: 589,
    size: '3.5 MB',
  },
  {
    id: 4,
    title: 'Eastern Region Sustainability Report',
    type: 'ISO 14046',
    region: 'Eastern Kenya',
    date: '2023-12-28',
    status: 'processing',
    predictions: 445,
    aquifers: 312,
    size: '-',
  },
]

export default function ReportsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedReport, setSelectedReport] = useState<number | null>(null)

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
                <h1 className="text-3xl font-bold">Reports</h1>
                <p className="text-muted-foreground mt-1">
                  Generate and download ISO 14046 compliant water sustainability reports
                </p>
              </div>
              <Button size="lg">
                <FileText className="mr-2 h-4 w-4" />
                Generate New Report
              </Button>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Reports</p>
                      <p className="text-2xl font-bold mt-1">24</p>
                    </div>
                    <FileText className="h-8 w-8 text-aqua-600 dark:text-aqua-400" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">This Month</p>
                      <p className="text-2xl font-bold mt-1">4</p>
                    </div>
                    <Calendar className="h-8 w-8 text-green-600 dark:text-green-400" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Processing</p>
                      <p className="text-2xl font-bold mt-1">1</p>
                    </div>
                    <Clock className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">ISO Compliant</p>
                      <p className="text-2xl font-bold mt-1">18</p>
                    </div>
                    <FileCheck className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Report Templates */}
            <Card>
              <CardHeader>
                <CardTitle>Report Templates</CardTitle>
                <CardDescription>
                  Choose a template to generate a new report
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="border rounded-lg p-4 hover:border-primary cursor-pointer transition-colors">
                    <FileText className="h-8 w-8 text-aqua-600 dark:text-aqua-400 mb-3" />
                    <h3 className="font-semibold mb-1">ISO 14046 Water Footprint</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      Complete water footprint assessment following ISO 14046 standards
                    </p>
                    <Badge>ISO Compliant</Badge>
                  </div>

                  <div className="border rounded-lg p-4 hover:border-primary cursor-pointer transition-colors">
                    <TrendingUp className="h-8 w-8 text-green-600 dark:text-green-400 mb-3" />
                    <h3 className="font-semibold mb-1">Recharge Forecast Report</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      Groundwater recharge forecasts with confidence intervals
                    </p>
                    <Badge variant="secondary">Technical</Badge>
                  </div>

                  <div className="border rounded-lg p-4 hover:border-primary cursor-pointer transition-colors">
                    <Droplets className="h-8 w-8 text-blue-600 dark:text-blue-400 mb-3" />
                    <h3 className="font-semibold mb-1">Aquifer Analysis Report</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      Detailed aquifer presence and depth classification analysis
                    </p>
                    <Badge variant="secondary">Technical</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Reports */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Reports</CardTitle>
                <CardDescription>
                  View and download your generated reports
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {reports.map((report) => (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-aqua-500 to-aqua-700 flex items-center justify-center">
                          <FileText className="h-6 w-6 text-white" />
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold">{report.title}</h3>
                            {report.status === 'completed' ? (
                              <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                Completed
                              </Badge>
                            ) : (
                              <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                                <Clock className="h-3 w-3 mr-1" />
                                Processing
                              </Badge>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              {report.type}
                            </span>
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {report.region}
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(report.date).toLocaleDateString()}
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                            <span>{report.predictions} predictions</span>
                            <span>{report.aquifers} aquifers found</span>
                            <span>{report.size}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {report.status === 'completed' && (
                          <>
                            <Button variant="outline" size="sm">
                              Preview
                            </Button>
                            <Button size="sm">
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
