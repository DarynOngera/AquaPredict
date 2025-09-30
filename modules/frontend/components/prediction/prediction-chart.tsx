'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Prediction } from '@/lib/store'

interface PredictionChartProps {
  prediction: Prediction
}

export function PredictionChart({ prediction }: PredictionChartProps) {
  const probability = prediction.probability * 100

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Confidence Visualization</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Probability Bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Probability</span>
              <span className="text-sm text-muted-foreground">
                {probability.toFixed(1)}%
              </span>
            </div>
            <div className="h-3 w-full rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-aqua-500 to-aqua-600 transition-all duration-500"
                style={{ width: `${probability}%` }}
              />
            </div>
          </div>

          {/* Confidence Interval */}
          {prediction.confidence_interval && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Confidence Range</span>
              </div>
              <div className="relative h-8 w-full rounded-full bg-muted">
                <div
                  className="absolute h-full rounded-full bg-aqua-200 dark:bg-aqua-800/50"
                  style={{
                    left: `${prediction.confidence_interval[0] * 100}%`,
                    width: `${
                      (prediction.confidence_interval[1] - prediction.confidence_interval[0]) *
                      100
                    }%`,
                  }}
                />
                <div
                  className="absolute top-1/2 h-4 w-1 -translate-y-1/2 rounded-full bg-aqua-600 dark:bg-aqua-400"
                  style={{ left: `${probability}%` }}
                />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-xs text-muted-foreground">
                  {(prediction.confidence_interval[0] * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-muted-foreground">
                  {(prediction.confidence_interval[1] * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}

          {/* Interpretation */}
          <div className="mt-4 rounded-lg bg-muted/50 p-3">
            <p className="text-xs text-muted-foreground">
              {probability >= 80
                ? '🎯 High confidence - Strong aquifer presence indicators'
                : probability >= 60
                ? '⚠️ Moderate confidence - Further investigation recommended'
                : '❌ Low confidence - Aquifer presence unlikely'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
