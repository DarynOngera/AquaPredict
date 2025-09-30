import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AquaPredict - Geospatial AI for Aquifer Prediction',
  description: 'Predict aquifers, forecast groundwater recharge, and generate ISO-compliant water sustainability reports',
  keywords: ['aquifer', 'groundwater', 'water', 'AI', 'geospatial', 'prediction', 'Kenya'],
  authors: [{ name: 'AquaPredict Team' }],
  openGraph: {
    title: 'AquaPredict',
    description: 'Geospatial AI for Aquifer Prediction',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
