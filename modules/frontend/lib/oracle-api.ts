/**
 * Oracle Autonomous Database API Client
 * Fetches data from Oracle Cloud Infrastructure
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface OraclePrecipitationData {
  avg_precip: number;
  max_precip: number;
  min_precip: number;
  total_precip: number;
  days_count: number;
  period_days: number;
  data_source: string;
}

export interface MonthlyPrecipitation {
  year_month: string;
  year: number;
  month: number;
  days_count: number;
  avg_precip: number;
  max_precip: number;
  total_precip: number;
}

export interface OracleHealthStatus {
  status: string;
  infrastructure: string;
  services: {
    oracle_atp: boolean;
    gee: boolean;
    models: boolean;
    settings: boolean;
    export: boolean;
  };
  data_source: string;
}

/**
 * Get latest precipitation data from Oracle ATP
 */
export async function getLatestPrecipitation(days: number = 7): Promise<OraclePrecipitationData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/oracle/precipitation/latest?days=${days}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch precipitation data');
    }
    
    const result = await response.json();
    return result.data;
  } catch (error) {
    console.error('Error fetching precipitation data:', error);
    return null;
  }
}

/**
 * Get monthly precipitation summary from Oracle ATP
 */
export async function getMonthlyPrecipitation(year?: number): Promise<MonthlyPrecipitation[]> {
  try {
    const url = year 
      ? `${API_BASE_URL}/api/v1/oracle/precipitation/monthly?year=${year}`
      : `${API_BASE_URL}/api/v1/oracle/precipitation/monthly`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error('Failed to fetch monthly data');
    }
    
    const result = await response.json();
    return result.data || [];
  } catch (error) {
    console.error('Error fetching monthly data:', error);
    return [];
  }
}

/**
 * Get Oracle Cloud health status
 */
export async function getOracleHealthStatus(): Promise<OracleHealthStatus | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch health status');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching health status:', error);
    return null;
  }
}
