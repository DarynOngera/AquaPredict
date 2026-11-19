import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Location {
  lat: number
  lon: number
}

export interface Prediction {
  location: Location
  prediction: string
  probability: number
  confidence_interval?: [number, number]
  data_source?: string
  timestamp: string
  [key: string]: unknown
}

export interface Forecast {
  location: Location
  forecast: any[]
  horizon?: number
  confidence_intervals?: [number, number][]
  summary?: Record<string, unknown>
  data_source?: string
  timestamp: string
}

export interface HistoryPrediction extends Prediction {
  id: string
}

export interface HistoryForecast extends Forecast {
  id: string
}

export interface GeneratedReport {
  id: string
  title: string
  createdAt: string
  prediction?: HistoryPrediction
  forecast?: HistoryForecast
}

interface AppState {
  selectedLocation: Location | null
  setSelectedLocation: (location: Location | null) => void

  prediction: Prediction | null
  setPrediction: (prediction: Prediction | null) => void
  isLoadingPrediction: boolean
  setIsLoadingPrediction: (loading: boolean) => void

  forecast: Forecast | null
  setForecast: (forecast: Forecast | null) => void
  isLoadingForecast: boolean
  setIsLoadingForecast: (loading: boolean) => void

  mapCenter: [number, number]
  setMapCenter: (center: [number, number]) => void
  mapZoom: number
  setMapZoom: (zoom: number) => void

  predictionHistory: HistoryPrediction[]
  forecastHistory: HistoryForecast[]
  addToPredictionHistory: (prediction: Prediction) => void
  addToForecastHistory: (forecast: Forecast) => void
  removePredictionHistory: (id: string) => void
  removeForecastHistory: (id: string) => void
  clearHistory: () => void

  reports: GeneratedReport[]
  addReport: (report: GeneratedReport) => void
  removeReport: (id: string) => void
}

const recordId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      selectedLocation: null,
      setSelectedLocation: (location) => set({ selectedLocation: location }),

      prediction: null,
      setPrediction: (prediction) => set({ prediction }),
      isLoadingPrediction: false,
      setIsLoadingPrediction: (loading) => set({ isLoadingPrediction: loading }),

      forecast: null,
      setForecast: (forecast) => set({ forecast }),
      isLoadingForecast: false,
      setIsLoadingForecast: (loading) => set({ isLoadingForecast: loading }),

      mapCenter: [0.0236, 37.9062],
      setMapCenter: (center) => set({ mapCenter: center }),
      mapZoom: 6,
      setMapZoom: (zoom) => set({ mapZoom: zoom }),

      predictionHistory: [],
      forecastHistory: [],
      addToPredictionHistory: (prediction) => set((state) => ({
        predictionHistory: [{ ...prediction, id: recordId() }, ...state.predictionHistory].slice(0, 50),
      })),
      addToForecastHistory: (forecast) => set((state) => ({
        forecastHistory: [{ ...forecast, id: recordId() }, ...state.forecastHistory].slice(0, 50),
      })),
      removePredictionHistory: (id) => set((state) => ({
        predictionHistory: state.predictionHistory.filter((item) => item.id !== id),
      })),
      removeForecastHistory: (id) => set((state) => ({
        forecastHistory: state.forecastHistory.filter((item) => item.id !== id),
      })),
      clearHistory: () => set({ predictionHistory: [], forecastHistory: [] }),

      reports: [],
      addReport: (report) => set((state) => ({ reports: [report, ...state.reports].slice(0, 30) })),
      removeReport: (id) => set((state) => ({ reports: state.reports.filter((report) => report.id !== id) })),
    }),
    {
      name: 'aquapredict-demo-history',
      partialize: (state) => ({
        predictionHistory: state.predictionHistory,
        forecastHistory: state.forecastHistory,
        reports: state.reports,
      }),
    },
  ),
)
