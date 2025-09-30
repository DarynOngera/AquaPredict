'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Settings as SettingsIcon, 
  User,
  Bell,
  Map,
  Database,
  Zap,
  Shield,
  Save,
  RefreshCw
} from 'lucide-react'

export default function SettingsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeSection, setActiveSection] = useState('general')

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6 space-y-6">
            {/* Page Header */}
            <div>
              <h1 className="text-3xl font-bold">Settings</h1>
              <p className="text-muted-foreground mt-1">
                Manage your application preferences and configuration
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Settings Navigation */}
              <div className="space-y-1">
                <button
                  onClick={() => setActiveSection('general')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === 'general'
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  <SettingsIcon className="h-4 w-4" />
                  General
                </button>
                <button
                  onClick={() => setActiveSection('map')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === 'map'
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Map className="h-4 w-4" />
                  Map Settings
                </button>
                <button
                  onClick={() => setActiveSection('models')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === 'models'
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Zap className="h-4 w-4" />
                  ML Models
                </button>
                <button
                  onClick={() => setActiveSection('notifications')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === 'notifications'
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Bell className="h-4 w-4" />
                  Notifications
                </button>
                <button
                  onClick={() => setActiveSection('data')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === 'data'
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Database className="h-4 w-4" />
                  Data Sources
                </button>
              </div>

              {/* Settings Content */}
              <div className="lg:col-span-3 space-y-6">
                {activeSection === 'general' && (
                  <>
                    <Card>
                      <CardHeader>
                        <CardTitle>General Settings</CardTitle>
                        <CardDescription>
                          Configure general application preferences
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Theme</label>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm">Light</Button>
                            <Button variant="outline" size="sm">Dark</Button>
                            <Button variant="default" size="sm">System</Button>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium">Language</label>
                          <select className="w-full px-3 py-2 border rounded-md bg-background">
                            <option>English</option>
                            <option>Swahili</option>
                            <option>French</option>
                          </select>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium">Time Zone</label>
                          <select className="w-full px-3 py-2 border rounded-md bg-background">
                            <option>Africa/Nairobi (EAT)</option>
                            <option>UTC</option>
                          </select>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Region Settings</CardTitle>
                        <CardDescription>
                          Configure default region and coordinates
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Default Region</label>
                          <select className="w-full px-3 py-2 border rounded-md bg-background">
                            <option>Kenya - National</option>
                            <option>Central Kenya</option>
                            <option>Eastern Kenya</option>
                            <option>Western Kenya</option>
                          </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Default Latitude</label>
                            <input
                              type="number"
                              defaultValue="0.0236"
                              step="0.0001"
                              className="w-full px-3 py-2 border rounded-md bg-background"
                            />
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Default Longitude</label>
                            <input
                              type="number"
                              defaultValue="37.9062"
                              step="0.0001"
                              className="w-full px-3 py-2 border rounded-md bg-background"
                            />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}

                {activeSection === 'map' && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Map Settings</CardTitle>
                      <CardDescription>
                        Configure map display and interaction preferences
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Base Map Layer</label>
                        <select className="w-full px-3 py-2 border rounded-md bg-background">
                          <option>OpenStreetMap</option>
                          <option>Satellite</option>
                          <option>Terrain</option>
                          <option>Hybrid</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Default Zoom Level</label>
                        <input
                          type="range"
                          min="1"
                          max="18"
                          defaultValue="6"
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>1 (World)</span>
                          <span>6 (Country)</span>
                          <span>18 (Street)</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">Show Prediction Markers</p>
                          <p className="text-xs text-muted-foreground">Display markers for past predictions</p>
                        </div>
                        <input type="checkbox" defaultChecked className="h-4 w-4" />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">Auto-center on Selection</p>
                          <p className="text-xs text-muted-foreground">Center map when location is selected</p>
                        </div>
                        <input type="checkbox" defaultChecked className="h-4 w-4" />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {activeSection === 'models' && (
                  <>
                    <Card>
                      <CardHeader>
                        <CardTitle>ML Model Configuration</CardTitle>
                        <CardDescription>
                          Configure machine learning model preferences
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Aquifer Classifier</label>
                          <select className="w-full px-3 py-2 border rounded-md bg-background">
                            <option>XGBoost (Recommended)</option>
                            <option>Random Forest</option>
                            <option>Ensemble</option>
                          </select>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium">Recharge Forecaster</label>
                          <select className="w-full px-3 py-2 border rounded-md bg-background">
                            <option>LSTM (Recommended)</option>
                            <option>TFT</option>
                          </select>
                        </div>

                        <div className="space-y-2">
                          <label className="text-sm font-medium">Confidence Threshold</label>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            defaultValue="60"
                            className="w-full"
                          />
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>0%</span>
                            <span>60%</span>
                            <span>100%</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Model Status</CardTitle>
                        <CardDescription>
                          Current model versions and performance
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium text-sm">Aquifer Classifier</p>
                            <p className="text-xs text-muted-foreground">Version 2.1.0 • ROC-AUC: 0.923</p>
                          </div>
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Active
                          </Badge>
                        </div>

                        <div className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium text-sm">Recharge Forecaster</p>
                            <p className="text-xs text-muted-foreground">Version 1.8.2 • RMSE: 4.2mm</p>
                          </div>
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Active
                          </Badge>
                        </div>

                        <Button variant="outline" className="w-full">
                          <RefreshCw className="mr-2 h-4 w-4" />
                          Check for Updates
                        </Button>
                      </CardContent>
                    </Card>
                  </>
                )}

                {activeSection === 'notifications' && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Notification Preferences</CardTitle>
                      <CardDescription>
                        Manage how you receive notifications
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">Prediction Complete</p>
                          <p className="text-xs text-muted-foreground">Notify when predictions finish</p>
                        </div>
                        <input type="checkbox" defaultChecked className="h-4 w-4" />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">Report Generated</p>
                          <p className="text-xs text-muted-foreground">Notify when reports are ready</p>
                        </div>
                        <input type="checkbox" defaultChecked className="h-4 w-4" />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">Model Updates</p>
                          <p className="text-xs text-muted-foreground">Notify about new model versions</p>
                        </div>
                        <input type="checkbox" className="h-4 w-4" />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">System Alerts</p>
                          <p className="text-xs text-muted-foreground">Important system notifications</p>
                        </div>
                        <input type="checkbox" defaultChecked className="h-4 w-4" />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {activeSection === 'data' && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Data Sources</CardTitle>
                      <CardDescription>
                        Configure data source connections and preferences
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium text-sm">Google Earth Engine</p>
                            <p className="text-xs text-muted-foreground">CHIRPS, ERA5, SRTM data</p>
                          </div>
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Connected
                          </Badge>
                        </div>

                        <div className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium text-sm">Oracle ADB</p>
                            <p className="text-xs text-muted-foreground">Spatial database</p>
                          </div>
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Connected
                          </Badge>
                        </div>

                        <div className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium text-sm">OCI Object Storage</p>
                            <p className="text-xs text-muted-foreground">Model and data storage</p>
                          </div>
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Connected
                          </Badge>
                        </div>
                      </div>

                      <div className="pt-4 border-t">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium">Cache Predictions</p>
                            <p className="text-xs text-muted-foreground">Store predictions locally</p>
                          </div>
                          <input type="checkbox" defaultChecked className="h-4 w-4" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Save Button */}
                <div className="flex justify-end gap-2">
                  <Button variant="outline">Cancel</Button>
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save Changes
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
