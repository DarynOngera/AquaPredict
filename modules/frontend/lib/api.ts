import { Location, Prediction, Forecast } from './store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new APIError(response.status, error.detail || 'Request failed')
  }

  return response.json()
}

export const api = {
  // Health check
  health: () => fetchAPI<{ status: string }>('/health'),

  // Predict aquifer presence
  predictAquifer: async (location: Location, useRealData: boolean = true) => {
    return fetchAPI<Prediction>('/api/v1/predict/aquifer', {
      method: 'POST',
      body: JSON.stringify({
        location,
        use_real_data: useRealData,
      }),
    })
  },

  // Forecast recharge
  forecastRecharge: async (location: Location, horizon: number = 12, useRealData: boolean = true) => {
    return fetchAPI<Forecast>('/api/v1/predict/recharge', {
      method: 'POST',
      body: JSON.stringify({
        location,
        horizon,
        use_real_data: useRealData,
      }),
    })
  },

  // Get extraction recommendations
  getExtractionRecommendations: async (location: Location, useRealData: boolean = true) => {
    return fetchAPI<any>('/api/v1/recommendations/extraction', {
      method: 'POST',
      body: JSON.stringify({
        location,
        use_real_data: useRealData,
      }),
    })
  },

  // Settings
  getSettings: () => fetchAPI<any>('/api/v1/settings'),

  updateSettings: (settings: any) => {
    return fetchAPI<{ status: string; settings: any }>('/api/v1/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    })
  },

  resetSettings: () => {
    return fetchAPI<{ status: string; settings: any }>('/api/v1/settings/reset', {
      method: 'POST',
    })
  },

  // Export
  exportData: async (
    exportType: 'prediction' | 'forecast' | 'history' | 'report',
    format: 'csv' | 'json' | 'geojson' | 'pdf',
    data: any,
    includeMetadata: boolean = true
  ) => {
    const response = await fetch(`${API_URL}/api/v1/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        export_type: exportType,
        format,
        data,
        include_metadata: includeMetadata,
      }),
    })

    if (!response.ok) {
      throw new APIError(response.status, 'Export failed')
    }

    return response.blob()
  },

  // Models
  listModels: () => fetchAPI<any>('/api/v1/models'),

  reloadModels: () => {
    return fetchAPI<{ status: string; models: any }>('/api/v1/models/reload', {
      method: 'POST',
    })
  },

  // Data sources
  getDataSources: () => fetchAPI<any>('/api/v1/data/sources'),

  getFeatureInfo: () => fetchAPI<any>('/api/v1/data/features'),

  // Dataset preview
  getDatasetPreview: (datasetId: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    const query = params.toString() ? `?${params.toString()}` : ''
    return fetchAPI<any>(`/api/v1/data/preview/${datasetId}${query}`)
  },
}

export { APIError }
