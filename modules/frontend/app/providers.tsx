'use client'

import { ThemeProvider } from 'next-themes'
import { SWRConfig } from 'swr'
import { Toaster } from '@/components/ui/toaster'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      enableSystem
      disableTransitionOnChange
    >
      <SWRConfig
        value={{
          fetcher,
          revalidateOnFocus: false,
          dedupingInterval: 60000,
        }}
      >
        {children}
        <Toaster />
      </SWRConfig>
    </ThemeProvider>
  )
}
