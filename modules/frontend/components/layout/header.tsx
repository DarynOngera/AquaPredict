'use client'

import { Menu, Droplets, Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, setTheme } = useTheme()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
      <div className="flex h-16 items-center px-4 gap-4">
        {/* Menu Button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onMenuClick}
          className="md:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Logo and Title */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-aqua-500 to-aqua-700 shadow-lg">
            <Droplets className="h-6 w-6 text-white" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-lg font-bold leading-none bg-gradient-to-r from-aqua-600 to-aqua-800 dark:from-aqua-400 dark:to-aqua-600 bg-clip-text text-transparent">
              AquaPredict
            </h1>
            <p className="text-xs text-muted-foreground">Geospatial AI Platform</p>
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Region Indicator */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted/50 border">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium">Kenya Pilot</span>
        </div>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        >
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </div>
    </header>
  )
}
