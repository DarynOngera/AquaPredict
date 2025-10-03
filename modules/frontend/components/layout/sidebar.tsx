'use client'

import { X, Map, BarChart3, FileText, History, Settings, Database, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

interface SidebarProps {
  open: boolean
  onClose: () => void
  onToggle?: () => void
}

const navigation = [
  { name: 'Dashboard', icon: Map, href: '/' },
  { name: 'Datasets', icon: Database, href: '/datasets' },
  { name: 'Analytics', icon: BarChart3, href: '/analytics' },
  { name: 'Reports', icon: FileText, href: '/reports' },
  { name: 'History', icon: History, href: '/history' },
  { name: 'Settings', icon: Settings, href: '/settings' },
]

export function Sidebar({ open, onClose, onToggle }: SidebarProps) {
  const pathname = usePathname()
  const handleToggle = onToggle || onClose

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Open button when sidebar is closed (desktop only) */}
      {!open && (
        <button
          onClick={handleToggle}
          className="hidden md:flex fixed left-0 top-20 z-40 items-center justify-center w-8 h-12 bg-card border border-l-0 rounded-r-lg shadow-md hover:bg-muted transition-colors"
          aria-label="Open sidebar"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      )}

      {/* Sidebar */}
      {open && (
        <aside
          className="fixed inset-y-0 left-0 z-50 w-64 border-r bg-card transition-all duration-300 ease-in-out md:relative md:flex md:flex-col"
        >
        <div className="flex h-full flex-col">
          {/* Header with toggle button */}
          <div className="flex h-16 items-center justify-between px-4 border-b">
            <span className="text-sm font-semibold">Navigation</span>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => {
                // On mobile, close. On desktop, toggle
                if (window.innerWidth < 768) {
                  onClose()
                } else {
                  handleToggle()
                }
              }}
              className="hover:bg-muted"
            >
              {/* Show X on mobile, chevron on desktop */}
              <X className="h-5 w-5 md:hidden" />
              <ChevronLeft className="h-5 w-5 hidden md:block" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                  onClick={() => {
                    // Close sidebar on mobile after navigation
                    if (window.innerWidth < 768) {
                      onClose()
                    }
                  }}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="border-t p-4">
            <div className="rounded-lg bg-gradient-to-br from-aqua-50 to-aqua-100 dark:from-aqua-950 dark:to-aqua-900 p-4">
              <p className="text-xs font-medium text-aqua-900 dark:text-aqua-100">
                Need Help?
              </p>
              <p className="mt-1 text-xs text-aqua-700 dark:text-aqua-300">
                Check our documentation or contact support
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full border-aqua-300 dark:border-aqua-700"
              >
                View Docs
              </Button>
            </div>
          </div>
        </div>
        </aside>
      )}
    </>
  )
}
