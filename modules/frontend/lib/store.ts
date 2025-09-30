import { create } from 'zustand'

export interface Location {
  lat: number
  lon: number
}

export interface Prediction {
  location: Location
  prediction: string
  probability: number
  confidence_interval?: [number, number]
  timestamp: string
}

export interface Forecast {
  location: Location
  forecast: number[]
  horizon: number
  confidence_intervals?: [number, number][]
  timestamp: string
}

interface AppState {
  // Location state
  selectedLocation: Location | null
  setSelectedLocation: (location: Location | null) => void
  
  // Prediction state
  prediction: Prediction | null
  setPrediction: (prediction: Prediction | null) => void
  isLoadingPrediction: boolean
  setIsLoadingPrediction: (loading: boolean) => void
  
  // Forecast state
  forecast: Forecast | null
  setForecast: (forecast: Forecast | null) => void
  isLoadingForecast: boolean
  setIsLoadingForecast: (loading: boolean) => void
  
  // UI state
  mapCenter: [number, number]
  setMapCenter: (center: [number, number]) => void
  mapZoom: number
  setMapZoom: (zoom: number) => void
  
  // History
  predictionHistory: Prediction[]
  addToPredictionHistory: (prediction: Prediction) => void
  clearHistory: () => void
}

export const useStore = create<AppState>((set) => ({
  // Location
  selectedLocation: null,
  setSelectedLocation: (location) => set({ selectedLocation: location }),
  
  // Prediction
  prediction: null,
  setPrediction: (prediction) => set({ prediction }),
  isLoadingPrediction: false,
  setIsLoadingPrediction: (loading) => set({ isLoadingPrediction: loading }),
  
  // Forecast
  forecast: null,
  setForecast: (forecast) => set({ forecast }),
  isLoadingForecast: false,
  setIsLoadingForecast: (loading) => set({ isLoadingForecast: loading }),
  
  // Map state - Kenya center
  mapCenter: [0.0236, 37.9062],
  setMapCenter: (center) => set({ mapCenter: center }),
  mapZoom: 6,
  setMapZoom: (zoom) => set({ mapZoom: zoom }),
  
  // History
  predictionHistory: [],
  addToPredictionHistory: (prediction) =>
    set((state) => ({
      predictionHistory: [prediction, ...state.predictionHistory].slice(0, 10),
    })),
  clearHistory: () => set({ predictionHistory: [] }),
}))
