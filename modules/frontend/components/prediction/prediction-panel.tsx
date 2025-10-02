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

  const [activeTab, setActiveTab] = useState<'prediction' | 'precipitation' | 'forecast'>('prediction')
  const [precipitationResult, setPrecipitationResult] = useState<any>(null)
  const [isLoadingPrecipitation, setIsLoadingPrecipitation] = useState(false)
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [selectedModel, setSelectedModel] = useState<string>('random_forest')

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

  const handlePrecipitationPredict = async () => {
    if (!selectedLocation) return

    setIsLoadingPrecipitation(true)
    try {
      const result = await api.predictPrecipitation(selectedLocation, selectedDate, selectedModel)
      setPrecipitationResult(result)
    } catch (error) {
      console.error('Precipitation prediction failed:', error)
      // TODO: Show error toast
    } finally {
      setIsLoadingPrecipitation(false)
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
          Aquifer
        </button>
        <button
          onClick={() => setActiveTab('precipitation')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'precipitation'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Precipitation
        </button>
        <button
          onClick={() => setActiveTab('forecast')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'forecast'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Forecast
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
        ) : activeTab === 'precipitation' ? (
          <>
            {/* Date and Model Selection */}
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-1.5 block">Date</label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md text-sm"
                >
                  <option value="random_forest">Random Forest</option>
                  <option value="xgboost">XGBoost</option>
                  <option value="linear_regression">Linear Regression</option>
                </select>
              </div>
            </div>

            {/* Prediction Button */}
            {!precipitationResult && (
              <Button
                onClick={handlePrecipitationPredict}
                disabled={isLoadingPrecipitation}
                className="w-full"
                size="lg"
              >
                {isLoadingPrecipitation ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Predicting...
                  </>
                ) : (
                  <>
                    <Droplets className="mr-2 h-4 w-4" />
                    Predict Precipitation
                  </>
                )}
              </Button>
            )}

            {/* Precipitation Results */}
            {precipitationResult && (
              <div className="space-y-4 animate-fade-in">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Precipitation Prediction</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="text-center py-4">
                      <div className="text-4xl font-bold text-primary">
                        {precipitationResult.prediction_mm.toFixed(2)} mm
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        Predicted precipitation
                      </p>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Model</span>
                      <Badge variant="outline">{precipitationResult.model}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Date</span>
                      <span className="font-medium">{precipitationResult.date}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Features Used</span>
                      <span className="font-medium">{precipitationResult.features_extracted}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <Badge className="bg-green-500">{precipitationResult.status}</Badge>
                    </div>
                  </CardContent>
                </Card>

                <Button
                  onClick={handlePrecipitationPredict}
                  variant="outline"
                  className="w-full"
                  disabled={isLoadingPrecipitation}
                >
                  Repredict
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
