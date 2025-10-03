"use client";

import { useEffect, useState } from 'react';
import { Database, Cloud, Activity, TrendingUp, Calendar, Droplets } from 'lucide-react';
import { getLatestPrecipitation, getMonthlyPrecipitation, getOracleHealthStatus, type OraclePrecipitationData, type MonthlyPrecipitation, type OracleHealthStatus } from '@/lib/oracle-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function OracleDataView() {
  const [precipData, setPrecipData] = useState<OraclePrecipitationData | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyPrecipitation[]>([]);
  const [healthStatus, setHealthStatus] = useState<OracleHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<number>(7);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [selectedPeriod]);

  async function fetchData() {
    setLoading(true);
    const [precip, monthly, health] = await Promise.all([
      getLatestPrecipitation(selectedPeriod),
      getMonthlyPrecipitation(),
      getOracleHealthStatus()
    ]);
    
    setPrecipData(precip);
    setMonthlyData(monthly.slice(-12)); // Last 12 months
    setHealthStatus(health);
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      {/* Oracle Cloud Header */}
      <Card className="border-red-200 dark:border-red-800 bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950 dark:to-orange-950">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                <Cloud className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <CardTitle className="text-lg sm:text-xl">Oracle Cloud Infrastructure</CardTitle>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Data powered by Oracle Autonomous Database
                </p>
              </div>
            </div>
            
            {healthStatus?.services.oracle_atp && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 dark:bg-green-900 rounded-full self-start sm:self-center">
                <Activity className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                  Connected
                </span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Database className="w-4 h-4" />
            <span>Source: {healthStatus?.data_source || 'Oracle Autonomous Database'}</span>
          </div>
        </CardContent>
      </Card>

      {/* Period Selector */}
      <div className="flex flex-wrap gap-2">
        {[7, 14, 30, 90].map((days) => (
          <button
            key={days}
            onClick={() => setSelectedPeriod(days)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedPeriod === days
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            Last {days} days
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Loading data from Oracle ATP...</p>
        </div>
      )}

      {/* Precipitation Statistics */}
      {!loading && precipData && precipData.avg_precip !== undefined && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Average Precipitation
                </CardTitle>
                <TrendingUp className="w-4 h-4 text-blue-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                {(precipData.avg_precip || 0).toFixed(2)}
                <span className="text-lg text-gray-500 dark:text-gray-400 ml-1">mm</span>
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Last {precipData.period_days || selectedPeriod} days
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Peak Precipitation
                </CardTitle>
                <Droplets className="w-4 h-4 text-red-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                {(precipData.max_precip || 0).toFixed(2)}
                <span className="text-lg text-gray-500 dark:text-gray-400 ml-1">mm</span>
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Maximum recorded
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Precipitation
                </CardTitle>
                <Database className="w-4 h-4 text-green-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                {(precipData.total_precip || 0).toFixed(2)}
                <span className="text-lg text-gray-500 dark:text-gray-400 ml-1">mm</span>
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Cumulative total
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Data Points
                </CardTitle>
                <Activity className="w-4 h-4 text-purple-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                {precipData.days_count || 0}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                From Oracle ATP
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Monthly Trends */}
      {!loading && monthlyData.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              <CardTitle>Monthly Precipitation Trends</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b dark:border-gray-700">
                    <th className="text-left py-3 px-2 font-medium text-gray-700 dark:text-gray-300">Month</th>
                    <th className="text-right py-3 px-2 font-medium text-gray-700 dark:text-gray-300">Days</th>
                    <th className="text-right py-3 px-2 font-medium text-gray-700 dark:text-gray-300">Avg (mm)</th>
                    <th className="text-right py-3 px-2 font-medium text-gray-700 dark:text-gray-300">Max (mm)</th>
                    <th className="text-right py-3 px-2 font-medium text-gray-700 dark:text-gray-300">Total (mm)</th>
                  </tr>
                </thead>
                <tbody>
                  {monthlyData.map((month, idx) => (
                    <tr key={idx} className="border-b dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="py-3 px-2 font-medium">{month.year_month}</td>
                      <td className="py-3 px-2 text-right">{month.days_count}</td>
                      <td className="py-3 px-2 text-right">{month.avg_precip?.toFixed(2) || '0.00'}</td>
                      <td className="py-3 px-2 text-right">{month.max_precip?.toFixed(2) || '0.00'}</td>
                      <td className="py-3 px-2 text-right font-semibold">{month.total_precip?.toFixed(2) || '0.00'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Oracle Services Status */}
      {healthStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Oracle Cloud Services Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              <ServiceStatus name="Autonomous DB" status={healthStatus.services.oracle_atp} />
              <ServiceStatus name="ML Models" status={healthStatus.services.models} />
              <ServiceStatus name="GEE Integration" status={healthStatus.services.gee} />
              <ServiceStatus name="Settings" status={healthStatus.services.settings} />
              <ServiceStatus name="Export" status={healthStatus.services.export} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ServiceStatus({ name, status }: { name: string; status: boolean }) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-800">
      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${status ? 'bg-green-500' : 'bg-gray-400'}`} />
      <span className="text-xs text-gray-700 dark:text-gray-300 truncate">{name}</span>
    </div>
  );
}
