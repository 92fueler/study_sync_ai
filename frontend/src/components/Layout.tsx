import { Link, useLocation } from 'react-router-dom';
import { Search, Bell, User } from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
    const location = useLocation();

    const isActive = (path: string) => location.pathname === path;

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="fixed top-0 w-full bg-white border-b border-gray-200 z-50">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-trust-blue rounded-full flex items-center justify-center">
                                <span className="text-white font-bold text-sm">S</span>
                            </div>
                            <span className="font-semibold text-gray-900">StudySync AI</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-8">
                        <Link
                            to="/"
                            className={`text-sm font-medium transition-colors ${isActive('/') ? 'text-trust-blue' : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            Dashboard
                        </Link>
                        <Link
                            to="/dna"
                            className={`text-sm font-medium transition-colors ${isActive('/dna') ? 'text-trust-blue' : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            My DNA
                        </Link>
                        <Link
                            to="/plan"
                            className={`text-sm font-medium transition-colors ${isActive('/plan') ? 'text-trust-blue' : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            Learning Plan
                        </Link>
                        <Link
                            to="/bank"
                            className={`text-sm font-medium transition-colors ${isActive('/bank') ? 'text-trust-blue' : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            Knowledge Bank
                        </Link>
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                            <Search className="w-5 h-5 text-gray-600" />
                        </button>
                        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                            <Bell className="w-5 h-5 text-gray-600" />
                        </button>
                        <button className="w-8 h-8 bg-orange-400 rounded-full flex items-center justify-center">
                            <User className="w-5 h-5 text-white" />
                        </button>
                    </div>
                </div>
            </nav>

            <main className="pt-16">
                {children}
            </main>
        </div>
    );
}
