'use client'

import { X, Map, BarChart3, FileText, History, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navigation = [
  { name: 'Map View', icon: Map, href: '/', current: true },
  { name: 'Analytics', icon: BarChart3, href: '/analytics', current: false },
  { name: 'Reports', icon: FileText, href: '/reports', current: false },
  { name: 'History', icon: History, href: '/history', current: false },
  { name: 'Settings', icon: Settings, href: '/settings', current: false },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform border-r bg-card transition-transform duration-300 ease-in-out md:relative md:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Close button (mobile) */}
          <div className="flex h-16 items-center justify-between px-4 md:hidden">
            <span className="text-sm font-semibold">Navigation</span>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <a
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    item.current
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  <span>{item.name}</span>
                </a>
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
    </>
  )
}
