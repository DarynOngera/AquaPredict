"use client";

import { useEffect, useState } from 'react';
import { Database, Cloud, Activity, TrendingUp } from 'lucide-react';
import { getLatestPrecipitation, getOracleHealthStatus, type OraclePrecipitationData, type OracleHealthStatus } from '@/lib/oracle-api';

export default function OracleDashboard() {
  const [precipData, setPrecipData] = useState<OraclePrecipitationData | null>(null);
  const [healthStatus, setHealthStatus] = useState<OracleHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const [precip, health] = await Promise.all([
        getLatestPrecipitation(7),
        getOracleHealthStatus()
      ]);
      
      setPrecipData(precip);
      setHealthStatus(health);
      setLoading(false);
    }

    fetchData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950 dark:to-orange-950 rounded-lg p-6 border border-red-200 dark:border-red-800">
        <div className="flex items-center gap-3 mb-4">
          <Cloud className="w-6 h-6 text-red-600 animate-pulse" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Oracle Cloud Infrastructure
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">Loading data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Oracle Cloud Header */}
      <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950 dark:to-orange-950 rounded-lg p-6 border border-red-200 dark:border-red-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Cloud className="w-6 h-6 text-red-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Powered by Oracle Cloud
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {healthStatus?.infrastructure || 'Oracle Cloud Infrastructure'}
              </p>
            </div>
          </div>
          
          {healthStatus?.services.oracle_atp && (
            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900 rounded-full">
              <Activity className="w-4 h-4 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium text-green-700 dark:text-green-300">
                Connected
              </span>
            </div>
          )}
        </div>

        {/* Data Source Badge */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Database className="w-4 h-4" />
          <span>Data Source: {healthStatus?.data_source || 'Oracle Autonomous Database'}</span>
        </div>
      </div>

      {/* Precipitation Data from Oracle ATP */}
      {precipData && precipData.avg_precip !== undefined && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Average Precipitation */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Avg Precipitation</span>
              <TrendingUp className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(precipData.avg_precip || 0).toFixed(2)} mm
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Last {precipData.period_days || 7} days
            </p>
          </div>

          {/* Max Precipitation */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Max Precipitation</span>
              <TrendingUp className="w-4 h-4 text-red-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(precipData.max_precip || 0).toFixed(2)} mm
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Peak rainfall
            </p>
          </div>

          {/* Total Precipitation */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Precipitation</span>
              <Database className="w-4 h-4 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(precipData.total_precip || 0).toFixed(2)} mm
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Cumulative
            </p>
          </div>

          {/* Data Points */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Data Points</span>
              <Activity className="w-4 h-4 text-purple-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {precipData.days_count || 0}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              From Oracle ATP
            </p>
          </div>
        </div>
      )}

      {/* Oracle Services Status */}
      {healthStatus && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            Oracle Cloud Services Status
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <ServiceStatus 
              name="Autonomous DB" 
              status={healthStatus.services.oracle_atp} 
            />
            <ServiceStatus 
              name="ML Models" 
              status={healthStatus.services.models} 
            />
            <ServiceStatus 
              name="GEE Integration" 
              status={healthStatus.services.gee} 
            />
            <ServiceStatus 
              name="Settings" 
              status={healthStatus.services.settings} 
            />
            <ServiceStatus 
              name="Export" 
              status={healthStatus.services.export} 
            />
          </div>
        </div>
      )}
    </div>
  );
}

function ServiceStatus({ name, status }: { name: string; status: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${status ? 'bg-green-500' : 'bg-gray-400'}`} />
      <span className="text-xs text-gray-600 dark:text-gray-400">{name}</span>
    </div>
  );
}
