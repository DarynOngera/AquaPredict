"use client"

import { useEffect, useState } from 'react'
import { Database, CheckCircle, XCircle, Activity } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function OracleStatusIndicator() {
  const [status, setStatus] = useState<{
    connected: boolean
    dataSource: string
    recordCount: number
  }>({
    connected: false,
    dataSource: 'Unknown',
    recordCount: 0
  })

  useEffect(() => {
    checkOracleStatus()
    const interval = setInterval(checkOracleStatus, 10000) // Check every 10s
    return () => clearInterval(interval)
  }, [])

  async function checkOracleStatus() {
    try {
      const response = await fetch(`${API_URL}/api/v1/analytics/dashboard-summary`)
      const data = await response.json()
      
      if (data.status === 'success') {
        console.log('✅ Oracle ATP Status: Connected')
        console.log('📊 Total Records:', data.summary.chirps_records + data.summary.weather_observations + data.summary.predictions)
        
        setStatus({
          connected: true,
          dataSource: data.data_source,
          recordCount: data.summary.chirps_records + data.summary.weather_observations + data.summary.predictions
        })
      } else {
        setStatus({
          connected: false,
          dataSource: 'Unavailable',
          recordCount: 0
        })
      }
    } catch (error) {
      console.error('❌ Oracle ATP Status: Disconnected')
      setStatus({
        connected: false,
        dataSource: 'Error',
        recordCount: 0
      })
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Badge 
        className={`flex items-center gap-2 px-3 py-2 text-sm shadow-lg ${
          status.connected 
            ? 'bg-green-600 hover:bg-green-700 text-white' 
            : 'bg-gray-600 hover:bg-gray-700 text-white'
        }`}
      >
        <Database className="h-4 w-4" />
        <span className="font-medium">Oracle ATP</span>
        {status.connected ? (
          <>
            <CheckCircle className="h-4 w-4" />
            <span className="text-xs">
              {status.recordCount.toLocaleString()} records
            </span>
          </>
        ) : (
          <XCircle className="h-4 w-4" />
        )}
      </Badge>
    </div>
  )
}
