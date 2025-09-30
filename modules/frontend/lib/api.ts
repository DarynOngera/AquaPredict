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
  predictAquifer: async (location: Location, features?: Record<string, number>) => {
    return fetchAPI<Prediction>('/api/v1/predict/aquifer', {
      method: 'POST',
      body: JSON.stringify({
        location,
        features,
        use_cached_features: !features,
      }),
    })
  },

  // Forecast recharge
  forecastRecharge: async (location: Location, horizon: number = 12) => {
    return fetchAPI<Forecast>('/api/v1/predict/recharge', {
      method: 'POST',
      body: JSON.stringify({
        location,
        horizon,
      }),
    })
  },

  // Batch predictions
  batchPredict: async (locations: Location[], type: 'aquifer' | 'recharge') => {
    return fetchAPI<{ predictions: (Prediction | Forecast)[]; count: number }>(
      '/api/v1/predict/batch',
      {
        method: 'POST',
        body: JSON.stringify({
          locations,
          prediction_type: type,
        }),
      }
    )
  },

  // Get available features
  getFeatures: () => fetchAPI<{ features: string[]; count: number }>('/api/v1/data/features'),

  // Query spatial data
  querySpatialData: (bbox: [number, number, number, number], feature?: string) => {
    const params = new URLSearchParams({
      bbox: bbox.join(','),
      ...(feature && { feature }),
    })
    return fetchAPI<{ data: any[]; bbox: number[]; count: number }>(
      `/api/v1/data/query?${params}`
    )
  },

  // List models
  listModels: () => fetchAPI<{ models: any[]; timestamp: string }>('/api/v1/models'),
}

export { APIError }
