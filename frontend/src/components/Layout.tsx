import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { GraduationCap, BookOpen, Calendar, Settings, User } from 'lucide-react'
import { cn } from '../utils/cn'

interface LayoutProps {
  children: ReactNode
  userId: string
}

const navigation = [
  { name: 'Knowledge Bank', href: '/knowledge-bank', icon: BookOpen },
  { name: 'Learning Plans', href: '/plans', icon: GraduationCap },
  { name: 'Calendar', href: '/calendar', icon: Calendar },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Layout({ children, userId }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
          {/* Logo */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <GraduationCap className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">StudySync AI</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.href === '/knowledge-bank' && location.pathname === '/')
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <User className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {userId.replace('user_', 'User ')}
                </p>
                <p className="text-xs text-gray-500">Pro Plan</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  )
}
