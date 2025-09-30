'use client'

import { Droplets, TrendingUp, MapPin, Activity } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

const stats = [
  {
    name: 'Predictions Made',
    value: '1,247',
    change: '+12.5%',
    icon: MapPin,
    color: 'text-aqua-600 dark:text-aqua-400',
    bgColor: 'bg-aqua-100 dark:bg-aqua-900/30',
  },
  {
    name: 'Aquifers Detected',
    value: '856',
    change: '+8.2%',
    icon: Droplets,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
  },
  {
    name: 'Avg Confidence',
    value: '87.3%',
    change: '+2.1%',
    icon: TrendingUp,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
  },
  {
    name: 'Active Forecasts',
    value: '342',
    change: '+5.4%',
    icon: Activity,
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
  },
]

export function StatsOverview() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.name} className="overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    {stat.name}
                  </p>
                  <p className="mt-2 text-2xl font-bold">{stat.value}</p>
                  <p className="mt-1 text-xs text-green-600 dark:text-green-400">
                    {stat.change} from last month
                  </p>
                </div>
                <div className={`rounded-full p-3 ${stat.bgColor}`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
