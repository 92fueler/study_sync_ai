import { Link, useNavigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
    ChevronLeft, Clock, BookOpen, Play, CheckCircle,
    Lock, Calendar, Award, ArrowRight, RefreshCw, Edit, Trash2, Pause, X, Save
} from 'lucide-react';
import { getLearningPlan, updateLearningPlan, deleteLearningPlan, pauseLearningPlan, resumeLearningPlan, getGoogleCalendarAuthUrl } from '../api/client';

export default function PlanDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [userId, setUserId] = useState('');
    const [plan, setPlan] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [calendarMessage, setCalendarMessage] = useState<string | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [difficultyChoice, setDifficultyChoice] = useState<'easier' | 'ok' | 'harder'>('ok');
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState({ title: '', description: '', goal: '' });
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [isPausing, setIsPausing] = useState(false);
    const [isResuming, setIsResuming] = useState(false);

    const handleCheckAvailability = async () => {
        if (isConnecting) return;
        setIsConnecting(true);
        setCalendarMessage(null);
        try {
            const storedUserId = localStorage.getItem('user_id') || '';
            if (!storedUserId) {
                setCalendarMessage('Missing user id');
                return;
            }
            const response = await getGoogleCalendarAuthUrl(storedUserId);
            if (response?.auth_url) {
                window.location.href = response.auth_url;
            } else {
                setCalendarMessage('Unable to start Google auth.');
            }
        } catch (error) {
            console.error('Google auth error', error);
            setCalendarMessage('Google auth failed.');
        } finally {
            setIsConnecting(false);
        }
    };

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

    useEffect(() => {
        if (!id || !userId) return;
        const loadPlan = async () => {
            try {
                setLoading(true);
                const response = await getLearningPlan(id, userId);
                const loadedPlan = response.plan || null;
                setPlan(loadedPlan);
                if (loadedPlan) {
                    setEditForm({
                        title: loadedPlan.title || '',
                        description: loadedPlan.description || '',
                        goal: loadedPlan.goal || '',
                    });
                }
                const current = loadedPlan?.difficulty?.toLowerCase();
                if (current === 'beginner') setDifficultyChoice('easier');
                else if (current === 'advanced') setDifficultyChoice('harder');
                else setDifficultyChoice('ok');
            } catch (error) {
                console.error('Failed to load plan details', error);
                setErrorMessage('Unable to load plan details.');
            } finally {
                setLoading(false);
            }
        };
        void loadPlan();
    }, [id, userId]);

    useEffect(() => {
        if (!id || !userId) return;
        const handler = () => {
            void (async () => {
                try {
                    const response = await getLearningPlan(id, userId);
                    setPlan(response.plan || null);
                } catch (error) {
                    console.error('Failed to refresh plan details', error);
                }
            })();
        };
        window.addEventListener('notifications:ready', handler);
        return () => {
            window.removeEventListener('notifications:ready', handler);
        };
    }, [id, userId]);

    const handleDifficultyUpdate = async (choice: 'easier' | 'ok' | 'harder') => {
        if (!plan || !userId) return;
        setDifficultyChoice(choice);
        const difficultyMap = {
            easier: 'Beginner',
            ok: 'Intermediate',
            harder: 'Advanced',
        } as const;
        try {
            const response = await updateLearningPlan(plan.id, userId, { difficulty: difficultyMap[choice] });
            if (response?.plan) {
                setPlan(response.plan);
            }
        } catch (error) {
            console.error('Failed to update difficulty', error);
        }
    };

    const handleEdit = () => {
        setIsEditing(true);
    };

    const handleCancelEdit = () => {
        setIsEditing(false);
        if (plan) {
            setEditForm({
                title: plan.title || '',
                description: plan.description || '',
                goal: plan.goal || '',
            });
        }
    };

    const handleSaveEdit = async () => {
        if (!plan || !userId) return;
        try {
            const response = await updateLearningPlan(plan.id, userId, {
                title: editForm.title,
                description: editForm.description,
                goal: editForm.goal,
            });
            if (response?.plan) {
                setPlan(response.plan);
                setIsEditing(false);
            }
        } catch (error) {
            console.error('Failed to update plan', error);
            setErrorMessage('Failed to save changes.');
        }
    };

    const handleDelete = async () => {
        if (!plan || !userId || !id) return;
        setIsDeleting(true);
        try {
            await deleteLearningPlan(id, userId);
            navigate('/plan');
        } catch (error) {
            console.error('Failed to delete plan', error);
            setErrorMessage('Failed to delete plan.');
            setIsDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    const handlePause = async () => {
        if (!plan || !userId) return;
        setIsPausing(true);
        try {
            const response = await pauseLearningPlan(plan.id, userId);
            if (response?.plan) {
                setPlan(response.plan);
            }
        } catch (error) {
            console.error('Failed to pause plan', error);
            setErrorMessage('Failed to pause plan.');
        } finally {
            setIsPausing(false);
        }
    };

    const handleResume = async () => {
        if (!plan || !userId) return;
        setIsResuming(true);
        try {
            const response = await resumeLearningPlan(plan.id, userId);
            if (response?.plan) {
                setPlan(response.plan);
            }
        } catch (error) {
            console.error('Failed to resume plan', error);
            setErrorMessage('Failed to resume plan.');
        } finally {
            setIsResuming(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-gray-500">Loading plan...</div>
            </div>
        );
    }

    if (!plan || errorMessage) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-gray-500">{errorMessage || 'Plan not found.'}</div>
            </div>
        );
    }

    type ModuleStatus = 'completed' | 'in-progress' | 'locked';
    type ModuleItem = {
        id: string;
        title: string;
        description: string;
        duration: string;
        status: ModuleStatus;
        progress?: number;
    };

    const modules: ModuleItem[] = (plan.items || []).map((item: any, index: number) => ({
        id: item.id,
        title: item.title || `Module ${index + 1}`,
        description: item.description || 'No description provided.',
        duration: item.estimated_minutes ? `${item.estimated_minutes} min` : '45 min',
        status: item.status === 'done' ? 'completed' : item.status === 'scheduled' ? 'in-progress' : 'locked',
        progress: item.progress_percent ?? undefined,
    }));

    const statusIcons = {
        completed: CheckCircle,
        'in-progress': Play,
        locked: Lock,
    };

    const statusColors = {
        completed: 'text-green-500 bg-green-50',
        'in-progress': 'text-blue-500 bg-blue-50',
        locked: 'text-gray-400 bg-gray-50',
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header / Hero Section */}
            <div className="bg-white border-b border-gray-200 sticky top-16 z-30 shadow-sm">
                <div className="max-w-7xl mx-auto px-6 py-6">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                            <Link to="/plan" className="hover:text-gray-900 flex items-center gap-1">
                                <ChevronLeft className="w-4 h-4" />
                                Back to Plans
                            </Link>
                            <span>/</span>
                            <span>{plan.title}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            {plan.status === 'active' && (
                                <button
                                    onClick={handlePause}
                                    disabled={isPausing}
                                    className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                                >
                                    <Pause className="w-4 h-4" />
                                    {isPausing ? 'Pausing...' : 'Pause'}
                                </button>
                            )}
                            {plan.status === 'paused' && (
                                <button
                                    onClick={handleResume}
                                    disabled={isResuming}
                                    className="flex items-center gap-2 px-4 py-2 text-sm text-blue-700 bg-white border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50"
                                >
                                    <Play className="w-4 h-4" />
                                    {isResuming ? 'Resuming...' : 'Resume'}
                                </button>
                            )}
                            <button
                                onClick={handleEdit}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                <Edit className="w-4 h-4" />
                                Edit
                            </button>
                            <button
                                onClick={() => setShowDeleteConfirm(true)}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-red-700 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                            >
                                <Trash2 className="w-4 h-4" />
                                Delete
                            </button>
                        </div>
                    </div>

                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                        <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                                <span className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded uppercase tracking-wide">
                                    {plan.category || 'GENERAL'}
                                </span>
                                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-bold rounded uppercase tracking-wide">
                                    {plan.difficulty}
                                </span>
                            </div>
                            {isEditing ? (
                                <div className="space-y-4 mb-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                                        <input
                                            type="text"
                                            value={editForm.title}
                                            onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg font-bold"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                        <textarea
                                            value={editForm.description}
                                            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                                            rows={4}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Goal</label>
                                        <input
                                            type="text"
                                            value={editForm.goal}
                                            onChange={(e) => setEditForm({ ...editForm, goal: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        />
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={handleSaveEdit}
                                            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                                        >
                                            <Save className="w-4 h-4" />
                                            Save Changes
                                        </button>
                                        <button
                                            onClick={handleCancelEdit}
                                            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                        >
                                            <X className="w-4 h-4" />
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <h1 className="text-3xl md:text-4xl font-serif font-bold text-gray-900 mb-4">
                                        {plan.title}
                                    </h1>
                                    <p className="text-gray-600 max-w-2xl text-lg leading-relaxed mb-3">
                                        {plan.description}
                                    </p>
                                    {plan.goal && (
                                        <div className="text-sm text-gray-500 max-w-2xl">
                                            <span className="font-semibold text-gray-700">Goal:</span> {plan.goal}
                                        </div>
                                    )}
                                </>
                            )}
                            <div className="mt-4">
                                <div className="text-xs uppercase font-semibold text-gray-400 mb-2">
                                    Difficulty feedback
                                </div>
                                <div className="inline-flex rounded-lg border border-gray-200 overflow-hidden">
                                    <button
                                        onClick={() => handleDifficultyUpdate('easier')}
                                        className={`px-4 py-2 text-sm font-medium ${difficultyChoice === 'easier'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-white text-gray-600 hover:bg-gray-50'
                                            }`}
                                    >
                                        Easier
                                    </button>
                                    <button
                                        onClick={() => handleDifficultyUpdate('ok')}
                                        className={`px-4 py-2 text-sm font-medium ${difficultyChoice === 'ok'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-white text-gray-600 hover:bg-gray-50'
                                            }`}
                                    >
                                        All good
                                    </button>
                                    <button
                                        onClick={() => handleDifficultyUpdate('harder')}
                                        className={`px-4 py-2 text-sm font-medium ${difficultyChoice === 'harder'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-white text-gray-600 hover:bg-gray-50'
                                            }`}
                                    >
                                        Harder
                                    </button>
                                </div>
                            </div>

                            <div className="flex items-center gap-6 text-sm text-gray-600">
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-blue-500" />
                                    <span>{plan.estimated_time || '4 weeks'} left</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <BookOpen className="w-4 h-4 text-purple-500" />
                                    <span>{plan.completed_modules || 0}/{plan.total_modules || plan.module_count || 0} modules</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Award className="w-4 h-4 text-orange-500" />
                                    <span>Certificate on completion</span>
                                </div>
                            </div>
                        </div>

                        {/* Progress Card */}
                        <div className="w-full md:w-80 bg-white p-6 rounded-xl border border-gray-100 shadow-lg">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-semibold text-gray-900">Total Progress</span>
                                <span className="text-2xl font-bold text-blue-600">{plan.progress_percent ?? 0}%</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2 mb-6">
                                <div
                                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${plan.progress_percent ?? 0}%` }}
                                />
                            </div>

                            <div className="flex items-center gap-3 mb-6 p-3 bg-blue-50 rounded-lg">
                                <Calendar className="w-5 h-5 text-blue-600" />
                                <div>
                                    <p className="text-xs uppercase font-bold text-blue-400 mb-0.5">Next Session</p>
                                    <p className="text-sm font-semibold text-blue-900">
                                        {plan.next_session_at ? new Date(plan.next_session_at).toLocaleString() : 'No session scheduled'}
                                    </p>
                                </div>
                            </div>

                            <Link
                                to={`/session/${plan.id}`} // Linking to our StudySession page
                                className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-md hover:shadow-lg"
                            >
                                <Play className="w-4 h-4 fill-current" />
                                Resume Learning
                            </Link>

                            <button
                                onClick={handleCheckAvailability}
                                className="w-full mt-3 flex items-center justify-center gap-2 py-2.5 bg-white border border-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                <RefreshCw className="w-4 h-4" />
                                {isConnecting ? 'Connecting...' : 'Connect Google Calendar'}
                            </button>
                            {calendarMessage && (
                                <div className="text-xs text-gray-500 mt-2">{calendarMessage}</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Modules List */}
            <div className="max-w-4xl mx-auto px-6 py-12">
                <h2 className="text-xl font-bold text-gray-900 mb-6">Course Modules</h2>
                <div className="space-y-4">
                    {modules.map((module: ModuleItem, index: number) => {
                        const Icon = statusIcons[module.status];
                        const colorClass = statusColors[module.status];
                        const isLocked = module.status === 'locked';

                        return (
                            <div
                                key={module.id}
                                className={`
                                    group relative bg-white rounded-xl border transition-all duration-200
                                    ${module.status === 'in-progress'
                                        ? 'border-blue-500 ring-1 ring-blue-500 shadow-md'
                                        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                                    }
                                    ${isLocked ? 'opacity-75 bg-gray-50' : ''}
                                `}
                            >
                                <div className="p-6 flex items-start gap-4">
                                    <div className={`
                                        flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                                        ${colorClass}
                                    `}>
                                        <Icon className="w-5 h-5" />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-1">
                                            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                                                Module 0{index + 1}
                                            </p>
                                            <span className="text-xs font-medium text-gray-500">
                                                {module.duration}
                                            </span>
                                        </div>
                                        <h3 className={`text-lg font-bold mb-2 ${isLocked ? 'text-gray-500' : 'text-gray-900'}`}>
                                            {module.title}
                                        </h3>
                                        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                                            {module.description}
                                        </p>

                                        {module.status === 'in-progress' && (
                                            <div className="w-full bg-gray-100 rounded-full h-1.5 mb-2">
                                                <div
                                                    className="bg-blue-500 h-1.5 rounded-full"
                                                    style={{ width: `${module.progress ?? 0}%` }}
                                                />
                                            </div>
                                        )}

                                        {!isLocked && (
                                            <div className="flex items-center gap-4 text-sm font-medium">
                                                {module.status === 'completed' ? (
                                                    <button className="text-green-600 hover:text-green-700 flex items-center gap-1">
                                                        Review Material <ArrowRight className="w-4 h-4" />
                                                    </button>
                                                ) : (
                                                    <Link to={`/session/${plan.id}`} className="text-blue-600 hover:text-blue-700 flex items-center gap-1">
                                                        {module.status === 'in-progress' ? 'Continue' : 'Start'} Module
                                                        <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                                                    </Link>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Delete Learning Plan</h3>
                        <p className="text-gray-600 mb-6">
                            Are you sure you want to delete "{plan.title}"? This action cannot be undone and will delete all associated modules and progress.
                        </p>
                        <div className="flex items-center gap-3 justify-end">
                            <button
                                onClick={() => setShowDeleteConfirm(false)}
                                disabled={isDeleting}
                                className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDelete}
                                disabled={isDeleting}
                                className="px-4 py-2 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                            >
                                {isDeleting ? 'Deleting...' : 'Delete Plan'}
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
