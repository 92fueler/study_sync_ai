import { Link, useLocation } from 'react-router-dom';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Search, Bell, User } from 'lucide-react';
import { API_BASE_URL, getNotificationBadge, getNotifications, markNotificationRead, searchAll } from '../api/client';

export default function Layout({ children }: { children: React.ReactNode }) {
    const location = useLocation();
    const [userId, setUserId] = useState('');
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searchError, setSearchError] = useState<string | null>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);
    const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
    const [notifications, setNotifications] = useState<any[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);
    const notificationsStreamRef = useRef<EventSource | null>(null);
    const [toastQueue, setToastQueue] = useState<any[]>([]);
    const toastTimerRef = useRef<number | null>(null);

    const isActive = (path: string) => location.pathname === path;

    useEffect(() => {
        const storedUserId = localStorage.getItem('user_id');
        if (storedUserId) {
            setUserId(storedUserId);
            return;
        }
        const tempUserId = `user_${Date.now()}`;
        localStorage.setItem('user_id', tempUserId);
        setUserId(tempUserId);
    }, []);

    const loadBadge = async () => {
        if (!userId) return;
        try {
            const response = await getNotificationBadge(userId);
            setUnreadCount(response.unread_count || 0);
        } catch (error) {
            console.error('Failed to load notification badge', error);
            setUnreadCount(0);
        }
    };

    const normalizeNotification = (item: any) => {
        if (!item) return item;
        const data = typeof item.data === 'string' ? safeParseJson(item.data) : item.data;
        return { ...item, data };
    };

    const safeParseJson = (value: string) => {
        try {
            return JSON.parse(value);
        } catch {
            return null;
        }
    };

    const loadNotifications = async () => {
        if (!userId) return;
        setIsLoadingNotifications(true);
        try {
            const response = await getNotifications(userId);
            const items = Array.isArray(response.notifications) ? response.notifications : [];
            setNotifications(items.map((item: any) => normalizeNotification(item)));
        } catch (error) {
            console.error('Failed to load notifications', error);
            setNotifications([]);
        } finally {
            setIsLoadingNotifications(false);
        }
    };

    useEffect(() => {
        if (!userId) return;
        void loadBadge();
    }, [userId]);

    useEffect(() => {
        if (!isSearchOpen) return;
        searchInputRef.current?.focus();
    }, [isSearchOpen]);

    useEffect(() => {
        if (!isSearchOpen) return;
        const trimmed = searchQuery.trim();
        if (!trimmed || trimmed.length < 2) {
            setSearchResults([]);
            setSearchError(null);
            return;
        }
        if (!userId) return;
        setIsSearching(true);
        setSearchError(null);
        const timer = window.setTimeout(async () => {
            try {
                const response = await searchAll(userId, trimmed, 8);
                setSearchResults(response.items || []);
            } catch (error) {
                console.error('Search failed', error);
                setSearchError('Search failed');
                setSearchResults([]);
            } finally {
                setIsSearching(false);
            }
        }, 300);

        return () => window.clearTimeout(timer);
    }, [isSearchOpen, searchQuery, userId]);

    const searchHint = useMemo(() => {
        if (searchError) return searchError;
        if (isSearching) return 'Searching...';
        if (searchQuery.trim().length < 2) return 'Type at least 2 characters';
        if (!searchResults.length) return 'No matches yet';
        return null;
    }, [isSearching, searchError, searchQuery, searchResults.length]);

    const handleSearchClose = () => {
        setIsSearchOpen(false);
        setSearchQuery('');
        setSearchResults([]);
        setSearchError(null);
    };

    const handleNotificationsToggle = () => {
        setIsNotificationsOpen((prev) => !prev);
    };

    const handleNotificationsClose = () => {
        setIsNotificationsOpen(false);
    };

    useEffect(() => {
        if (!isNotificationsOpen || !userId) return;
        if (notifications.length === 0) {
            void loadNotifications();
        }
    }, [isNotificationsOpen, userId, notifications.length]);

    useEffect(() => {
        if (!userId) return;
        if (notificationsStreamRef.current) {
            notificationsStreamRef.current.close();
        }
        const sseUrl = `${API_BASE_URL.replace(/\/$/, '')}/notifications/stream?user_id=${userId}`;
        const stream = new EventSource(sseUrl, { withCredentials: false });
        notificationsStreamRef.current = stream;

        stream.addEventListener('notifications', (event) => {
            try {
                const payload = JSON.parse((event as MessageEvent).data || '{}');
                const incoming = Array.isArray(payload.notifications) ? payload.notifications.map((item: any) => normalizeNotification(item)) : [];
                if (incoming.length) {
                    setNotifications((prev) => {
                        const seen = new Set(prev.map((item: any) => item.id));
                        const newItems = incoming.filter((item: any) => !seen.has(item.id));
                        if (newItems.length) {
                            const now = Date.now();
                            const recent = newItems.filter((item: any) => {
                                const created = item?.created_at ? Date.parse(item.created_at) : NaN;
                                return Number.isNaN(created) || now - created < 15_000;
                            });
                            if (recent.length) {
                                setToastQueue((prevQueue) => [...recent, ...prevQueue].slice(0, 3));
                            }
                            if (toastTimerRef.current) {
                                window.clearTimeout(toastTimerRef.current);
                            }
                            toastTimerRef.current = window.setTimeout(() => {
                                setToastQueue([]);
                            }, 4000);
                        }
                        const merged = [...newItems, ...prev];
                        return merged;
                    });
                }
                if (payload.unread_count !== undefined && payload.unread_count !== null) {
                    const count = typeof payload.unread_count === 'number'
                        ? payload.unread_count
                        : Number(payload.unread_count);
                    if (!Number.isNaN(count)) {
                        setUnreadCount(count);
                    }
                } else if (incoming.length) {
                    const unreadCount = incoming.filter((item: any) => item?.read === false).length;
                    setUnreadCount(unreadCount);
                }
                if (incoming.some((item: any) => item?.data?.status === 'ready')) {
                    window.dispatchEvent(new CustomEvent('notifications:ready'));
                }
            } catch (error) {
                console.error('Failed to parse notification stream', error);
            }
        });

        stream.addEventListener('error', () => {
            stream.close();
            notificationsStreamRef.current = null;
            void loadBadge();
        });

        return () => {
            stream.close();
            notificationsStreamRef.current = null;
            if (toastTimerRef.current) {
                window.clearTimeout(toastTimerRef.current);
                toastTimerRef.current = null;
            }
        };
    }, [userId]);

    return (
        <div className="min-h-screen bg-gray-50">
            {toastQueue.length > 0 && (
                <div className="fixed top-20 right-6 z-[60] space-y-2">
                    {toastQueue.map((item: any) => (
                        <div
                            key={item.id || item.created_at}
                            className="bg-white border border-gray-200 shadow-lg rounded-xl px-4 py-3 w-80"
                        >
                            <div className="text-xs text-gray-400 uppercase font-semibold">
                                {item.type || 'Notification'}
                            </div>
                            <div className="text-sm font-semibold text-gray-900 mt-1">
                                {item.title || item.message || 'Update'}
                            </div>
                            {item.body && (
                                <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                                    {item.body}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
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
                        <button
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            onClick={() => setIsSearchOpen((prev) => !prev)}
                            aria-label="Search"
                        >
                            <Search className="w-5 h-5 text-gray-600" />
                        </button>
                        <button
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative"
                            onClick={handleNotificationsToggle}
                            aria-label="Notifications"
                        >
                            <Bell className="w-5 h-5 text-gray-600" />
                            {unreadCount > 0 && (
                                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-semibold rounded-full px-1.5 py-0.5">
                                    {unreadCount > 9 ? '9+' : unreadCount}
                                </span>
                            )}
                        </button>
                        <button className="w-8 h-8 bg-orange-400 rounded-full flex items-center justify-center">
                            <User className="w-5 h-5 text-white" />
                        </button>
                    </div>
                </div>
            </nav>

            {isSearchOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/10"
                    onClick={handleSearchClose}
                    role="presentation"
                />
            )}

            {isSearchOpen && (
                <div className="fixed top-16 w-full z-50">
                    <div className="max-w-3xl mx-auto px-6">
                        <div
                            className="bg-white border border-gray-200 rounded-xl shadow-lg p-4"
                            onClick={(event) => event.stopPropagation()}
                            role="presentation"
                        >
                            <div className="flex items-center gap-2 border border-gray-200 rounded-lg px-3 py-2">
                                <Search className="w-4 h-4 text-gray-400" />
                                <input
                                    ref={searchInputRef}
                                    value={searchQuery}
                                    onChange={(event) => setSearchQuery(event.target.value)}
                                    onKeyDown={(event) => {
                                        if (event.key === 'Escape') {
                                            handleSearchClose();
                                        }
                                    }}
                                    placeholder="Search notes and plans"
                                    className="w-full text-sm text-gray-700 outline-none"
                                />
                            </div>

                            <div className="mt-3 max-h-80 overflow-y-auto">
                                {searchResults.length > 0 ? (
                                    <div className="space-y-2">
                                        {searchResults.map((item) => (
                                            <Link
                                                key={`${item.type}-${item.id}`}
                                                to={item.type === 'plan' ? `/plans/${item.id}` : `/notes/${item.id}`}
                                                onClick={handleSearchClose}
                                                className="block rounded-lg border border-gray-100 hover:border-trust-blue/40 hover:bg-blue-50/40 transition-colors p-3"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span className="text-xs uppercase font-semibold text-gray-400">
                                                        {item.type}
                                                    </span>
                                                    {item.status && (
                                                        <span className="text-xs text-gray-500">{item.status}</span>
                                                    )}
                                                </div>
                                                <div className="text-sm font-semibold text-gray-900 mt-1">
                                                    {item.title || 'Untitled'}
                                                </div>
                                                {item.description && (
                                                    <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                                                        {item.description}
                                                    </div>
                                                )}
                                            </Link>
                                        ))}
                                    </div>
                                ) : (
                                    searchHint && (
                                        <div className="text-xs text-gray-500 px-2 py-4 text-center">
                                            {searchHint}
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {isNotificationsOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/10"
                    onClick={handleNotificationsClose}
                    role="presentation"
                />
            )}

            {isNotificationsOpen && (
                <div className="fixed top-16 right-6 z-50 w-96 max-w-[90vw]">
                    <div
                        className="bg-white border border-gray-200 rounded-xl shadow-lg p-4"
                        onClick={(event) => event.stopPropagation()}
                        role="presentation"
                    >
                        <div className="flex items-center justify-between mb-3">
                            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
                            {unreadCount > 0 && (
                                <span className="text-xs text-gray-500">{unreadCount} unread</span>
                            )}
                        </div>

                        {isLoadingNotifications ? (
                            <div className="text-xs text-gray-500 py-6 text-center">Loading...</div>
                        ) : notifications.length === 0 ? (
                            <div className="text-xs text-gray-500 py-6 text-center">No notifications</div>
                        ) : (
                            <div className="space-y-2 max-h-80 overflow-y-auto">
                                {notifications.map((item) => {
                                    const status = item?.data?.status;
                                    return (
                                    <button
                                        key={item.id || item.created_at}
                                        className="w-full text-left rounded-lg border border-gray-100 hover:border-trust-blue/40 hover:bg-blue-50/40 transition-colors p-3"
                                        onClick={async () => {
                                            if (item.id) {
                                                await markNotificationRead(item.id, userId);
                                                setUnreadCount((prev) => Math.max(0, prev - 1));
                                            }
                                            handleNotificationsClose();
                                        }}
                                    >
                                        <div className="text-xs text-gray-400 uppercase font-semibold">
                                            {item.type || 'Notification'}
                                        </div>
                                        <div className="text-sm font-semibold text-gray-900 mt-1">
                                            {item.title || item.message || 'Update'}
                                        </div>
                                        {status && (
                                            <div className="mt-2 flex items-center gap-2 text-[11px] text-gray-500">
                                                <span className={`px-2 py-0.5 rounded-full border ${status === 'ready' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-blue-50 text-blue-700 border-blue-200'}`}>
                                                    {status}
                                                </span>
                                                <span>Received</span>
                                                <span>→</span>
                                                <span className={status === 'processing' ? 'font-semibold text-blue-700' : ''}>Generating</span>
                                                <span>→</span>
                                                <span className={status === 'ready' ? 'font-semibold text-green-700' : ''}>Ready</span>
                                            </div>
                                        )}
                                        {item.body && (
                                            <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                                                {item.body}
                                            </div>
                                        )}
                                    </button>
                                )})}
                            </div>
                        )}
                    </div>
                </div>
            )}

            <main className="pt-16">
                {children}
            </main>
        </div>
    );
}
