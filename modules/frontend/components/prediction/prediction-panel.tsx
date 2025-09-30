'use client'

import { useState } from 'react'
import { X, MapPin, Droplets, TrendingUp, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useStore } from '@/lib/store'
import { api } from '@/lib/api'
import { formatCoordinate, formatProbability, getPredictionBadgeColor } from '@/lib/utils'
import { PredictionChart } from './prediction-chart'
import { ForecastChart } from './forecast-chart'

export function PredictionPanel() {
  const {
    selectedLocation,
    setSelectedLocation,
    prediction,
    setPrediction,
    forecast,
    setForecast,
    isLoadingPrediction,
    setIsLoadingPrediction,
    isLoadingForecast,
    setIsLoadingForecast,
    addToPredictionHistory,
  } = useStore()

  const [activeTab, setActiveTab] = useState<'prediction' | 'forecast'>('prediction')

  const handlePredict = async () => {
    if (!selectedLocation) return

    setIsLoadingPrediction(true)
    try {
      const result = await api.predictAquifer(selectedLocation)
      setPrediction(result)
      addToPredictionHistory(result)
    } catch (error) {
      console.error('Prediction failed:', error)
      // TODO: Show error toast
    } finally {
      setIsLoadingPrediction(false)
    }
  }

  const handleForecast = async () => {
    if (!selectedLocation) return

    setIsLoadingForecast(true)
    try {
      const result = await api.forecastRecharge(selectedLocation, 12)
      setForecast(result)
    } catch (error) {
      console.error('Forecast failed:', error)
      // TODO: Show error toast
    } finally {
      setIsLoadingForecast(false)
    }
  }

  if (!selectedLocation) return null

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-primary" />
          <div>
            <h3 className="font-semibold">Location Analysis</h3>
            <p className="text-xs text-muted-foreground">
              {formatCoordinate(selectedLocation.lat, 'lat')},{' '}
              {formatCoordinate(selectedLocation.lon, 'lon')}
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => {
            setSelectedLocation(null)
            setPrediction(null)
            setForecast(null)
          }}
        >
          <X className="h-5 w-5" />
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab('prediction')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'prediction'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Aquifer Prediction
        </button>
        <button
          onClick={() => setActiveTab('forecast')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'forecast'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Recharge Forecast
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'prediction' ? (
          <>
            {/* Prediction Button */}
            {!prediction && (
              <Button
                onClick={handlePredict}
                disabled={isLoadingPrediction}
                className="w-full"
                size="lg"
              >
                {isLoadingPrediction ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Droplets className="mr-2 h-4 w-4" />
                    Predict Aquifer
                  </>
                )}
              </Button>
            )}

            {/* Prediction Results */}
            {prediction && (
              <div className="space-y-4 animate-fade-in">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Prediction Result</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Status</span>
                      <Badge className={getPredictionBadgeColor(prediction.prediction)}>
                        {prediction.prediction}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Confidence</span>
                      <span className="text-sm font-semibold">
                        {formatProbability(prediction.probability)}
                      </span>
                    </div>
                    {prediction.confidence_interval && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Range</span>
                        <span className="text-xs text-muted-foreground">
                          {formatProbability(prediction.confidence_interval[0])} -{' '}
                          {formatProbability(prediction.confidence_interval[1])}
                        </span>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <PredictionChart prediction={prediction} />

                <Button
                  onClick={handlePredict}
                  variant="outline"
                  className="w-full"
                  disabled={isLoadingPrediction}
                >
                  Reanalyze
                </Button>
              </div>
            )}
          </>
        ) : (
          <>
            {/* Forecast Button */}
            {!forecast && (
              <Button
                onClick={handleForecast}
                disabled={isLoadingForecast}
                className="w-full"
                size="lg"
              >
                {isLoadingForecast ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Forecasting...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Generate Forecast
                  </>
                )}
              </Button>
            )}

            {/* Forecast Results */}
            {forecast && (
              <div className="space-y-4 animate-fade-in">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Recharge Forecast</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {forecast.horizon}-month forecast for groundwater recharge
                    </p>
                  </CardContent>
                </Card>

                <ForecastChart forecast={forecast} />

                <Button
                  onClick={handleForecast}
                  variant="outline"
                  className="w-full"
                  disabled={isLoadingForecast}
                >
                  Regenerate Forecast
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
