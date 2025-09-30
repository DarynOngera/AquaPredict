import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCoordinate(value: number, type: 'lat' | 'lon'): string {
  const abs = Math.abs(value)
  const direction = type === 'lat' 
    ? (value >= 0 ? 'N' : 'S')
    : (value >= 0 ? 'E' : 'W')
  return `${abs.toFixed(4)}° ${direction}`
}

export function formatProbability(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getPredictionColor(prediction: string): string {
  switch (prediction.toLowerCase()) {
    case 'present':
    case 'high':
      return 'text-green-600 dark:text-green-400'
    case 'absent':
    case 'low':
      return 'text-red-600 dark:text-red-400'
    case 'medium':
      return 'text-yellow-600 dark:text-yellow-400'
    default:
      return 'text-gray-600 dark:text-gray-400'
  }
}

export function getPredictionBadgeColor(prediction: string): string {
  switch (prediction.toLowerCase()) {
    case 'present':
    case 'high':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    case 'absent':
    case 'low':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
  }
}

export function getConfidenceColor(probability: number): string {
  if (probability >= 0.8) return 'text-green-600 dark:text-green-400'
  if (probability >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}
