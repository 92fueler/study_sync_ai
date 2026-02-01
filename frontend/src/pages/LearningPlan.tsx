import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import LearningPlanCard from '../components/LearningPlanCard';
import ProposedPlanCard from '../components/ProposedPlanCard';
import PlanDetailsModal from '../components/PlanDetailsModal';
import { approveLearningPlan, createLearningPlan, listLearningPlans, listProposedLearningPlans } from '../api/client';

export default function LearningPlan() {
    const [userId, setUserId] = useState('');
    const [filter, setFilter] = useState('all');
    const [selectedPlan, setSelectedPlan] = useState<any>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [proposedPlansData, setProposedPlansData] = useState<any[]>([]);
    const [plansData, setPlansData] = useState<any[]>([]);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);

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

    const loadPlans = async (resolvedUserId: string) => {
        try {
            const [proposedResponse, plansResponse] = await Promise.all([
                listProposedLearningPlans(resolvedUserId, { limit: 6 }),
                listLearningPlans(resolvedUserId, { limit: 30 }),
            ]);
            setProposedPlansData(proposedResponse.items || []);
            setPlansData(plansResponse.items || []);
        } catch (error) {
            console.error('Failed to load learning plans', error);
        }
    };

    useEffect(() => {
        if (!userId) return;
        void loadPlans(userId);
    }, [userId]);

    useEffect(() => {
        if (!userId) return;
        const handler = () => {
            void loadPlans(userId);
        };
        window.addEventListener('notifications:ready', handler);
        return () => {
            window.removeEventListener('notifications:ready', handler);
        };
    }, [userId]);

    useEffect(() => {
        if (!statusMessage) return;
        const timer = window.setTimeout(() => setStatusMessage(null), 3000);
        return () => window.clearTimeout(timer);
    }, [statusMessage]);

    const handlePlanClick = (plan: any, isProposed: boolean) => {
        const timelineFromItems = Array.isArray(plan.items)
            ? plan.items.map((item: any, index: number) => ({
                week: index + 1,
                topic: item.title || `Module ${index + 1}`,
            }))
            : [];
        const timelineFromDetails = Array.isArray(plan.details?.timeline)
            ? plan.details.timeline
            : Array.isArray(plan.details?.proposed_timeline)
                ? plan.details.proposed_timeline
                : [];
        const proposedTimeline = timelineFromDetails.length ? timelineFromDetails : timelineFromItems;
        const modalPlan = {
            id: plan.id,
            title: plan.title,
            description: plan.description,
            isProposed,
            duration: plan.details?.duration || plan.estimated_time || 'Unknown',
            timeline: plan.details?.timeline_label || plan.estimatedTime || plan.estimated_time || 'Unknown',
            intensity: plan.difficulty || 'Moderate Pace',
            formatBreakdown: plan.details?.format_breakdown || {
                audioSessions: 0,
                deepDives: 0,
            },
            proposedTimeline,
            proposedSchedule: plan.details?.proposed_schedule,
        };
        setSelectedPlan(modalPlan);
        setIsModalOpen(true);
    };

    const handleApprove = async () => {
        if (!selectedPlan?.id || !userId) return;
        try {
            await approveLearningPlan(selectedPlan.id, userId);
            setIsModalOpen(false);
            setStatusMessage('Plan approved successfully.');
            await loadPlans(userId);
        } catch (error) {
            console.error('Failed to approve plan', error);
            setStatusMessage('Plan approval failed. Please try again.');
        }
    };

    const handleCustomize = () => {
        console.log('Customize plan');
    };

    const handleRegenerate = () => {
        console.log('Regenerate plan');
    };

    const handleCreatePlan = async () => {
        if (!userId) return;
        try {
            const response = await createLearningPlan({
                user_id: userId,
                title: 'New Learning Plan',
                description: 'Generated from plan page',
                status: 'active',
                difficulty: 'Intermediate',
                category: 'TECH',
                category_color: 'blue',
                estimated_time: '4 weeks',
                module_count: 6,
                details: { source: 'plan-page' },
            });
            const plan = response?.plan || response;
            if (plan) {
                await loadPlans(userId);
            }
            setStatusMessage('Plan created successfully.');
        } catch (error) {
            console.error('Failed to create plan', error);
            setStatusMessage('Plan creation failed. Please try again.');
        }
    };

    const normalizeProposedPlan = (plan: any) => ({
        id: plan.id,
        title: plan.title || 'Untitled Plan',
        description: plan.description || 'No description provided.',
        estimatedTime: plan.estimated_time || '4 weeks',
        moduleCount: plan.module_count || 8,
        difficulty: (plan.difficulty || 'Intermediate') as 'Beginner' | 'Intermediate' | 'Advanced',
        category: plan.category || 'TECH',
        categoryColor: plan.category_color || 'blue',
    });

    const normalizePlan = (plan: any) => {
        const statusMap: Record<string, 'active' | 'paused' | 'completed'> = {
            active: 'active',
            paused: 'paused',
            completed: 'completed',
        };
        return {
            id: plan.id,
            status: statusMap[plan.status] || 'active',
            category: plan.category || 'TECH',
            categoryColor: plan.category_color || 'blue',
            title: plan.title || 'Untitled Plan',
            goal: plan.goal || undefined,
            difficulty: plan.difficulty || 'Intermediate',
            percentage: plan.progress_percent ?? 0,
            module: plan.details?.current_module || plan.details?.module || undefined,
            timeRemaining: plan.estimated_time || undefined,
            totalModules: plan.total_modules || plan.module_count || 0,
            completedModules: plan.completed_modules || 0,
            nextSession: plan.next_session_at
                ? new Date(plan.next_session_at).toLocaleString()
                : undefined,
        };
    };

    const resolvedProposedPlans = proposedPlansData.map(normalizeProposedPlan);
    const resolvedPlans = plansData.map(normalizePlan);

    const filteredPlans = filter === 'all'
        ? resolvedPlans
        : resolvedPlans.filter(plan => plan.status === filter);

    const statusCounts = {
        all: resolvedPlans.length,
        active: resolvedPlans.filter(p => p.status === 'active').length,
        paused: resolvedPlans.filter(p => p.status === 'paused').length,
        completed: resolvedPlans.filter(p => p.status === 'completed').length,
    };

    return (
        <div className="max-w-7xl mx-auto px-6 py-12">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-4xl font-serif font-bold text-gray-900 mb-2">
                        Learning Plans
                    </h1>
                    <p className="text-gray-600">
                        Manage your personalized learning journeys
                    </p>
                </div>

                <button
                    onClick={handleCreatePlan}
                    className="flex items-center gap-2 px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                    <Plus className="w-5 h-5" />
                    Create New Plan
                </button>
            </div>

            {statusMessage && (
                <div className="mb-6 rounded-md bg-blue-50 text-blue-700 text-sm px-4 py-2">
                    {statusMessage}
                </div>
            )}

            {resolvedProposedPlans.length > 0 && (
                <div className="mb-10">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold text-gray-900">New Study Plans Designed for You</h2>
                        <div className="flex items-center gap-2">
                            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                <ChevronLeft className="w-5 h-5 text-gray-600" />
                            </button>
                            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                <ChevronRight className="w-5 h-5 text-gray-600" />
                            </button>
                        </div>
                    </div>

                    <div className="overflow-x-auto pb-4 -mx-6 px-6 scrollbar-hide">
                        <div className="flex gap-4">
                            {resolvedProposedPlans.map((plan, index) => {
                                const planId = (plan as { id?: string }).id;
                                return (
                                    <ProposedPlanCard
                                        key={planId || index}
                                        {...plan}
                                        onDetailsClick={() => handlePlanClick(plan, true)}
                                    />
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}

            <div className="flex items-center gap-4 mb-8 border-b border-gray-200">
                <button
                    onClick={() => setFilter('all')}
                    className={`px-4 py-3 text-sm font-medium transition-colors ${filter === 'all'
                        ? 'text-trust-blue border-b-2 border-trust-blue'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    All Plans ({statusCounts.all})
                </button>
                <button
                    onClick={() => setFilter('active')}
                    className={`px-4 py-3 text-sm font-medium transition-colors ${filter === 'active'
                        ? 'text-trust-blue border-b-2 border-trust-blue'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    Active ({statusCounts.active})
                </button>
                <button
                    onClick={() => setFilter('paused')}
                    className={`px-4 py-3 text-sm font-medium transition-colors ${filter === 'paused'
                        ? 'text-trust-blue border-b-2 border-trust-blue'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    Paused ({statusCounts.paused})
                </button>
                <button
                    onClick={() => setFilter('completed')}
                    className={`px-4 py-3 text-sm font-medium transition-colors ${filter === 'completed'
                        ? 'text-trust-blue border-b-2 border-trust-blue'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    Completed ({statusCounts.completed})
                </button>
            </div>

            {filteredPlans.length === 0 ? (
                <div className="text-center py-16">
                    <div className="text-6xl mb-4">📚</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        No {filter !== 'all' ? filter : ''} plans yet
                    </h3>
                    <p className="text-gray-600 mb-6">
                        Create your first learning plan to get started
                    </p>
                    <button
                        onClick={handleCreatePlan}
                        className="px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                        Create Plan
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredPlans.map((plan, index) => {
                        const planId = (plan as { id?: string }).id;
                        return (
                            <Link key={planId || index} to={`/plans/${planId || index + 1}`}>
                                <LearningPlanCard {...plan} />
                            </Link>
                        );
                    })}
                </div>
            )}

            {selectedPlan && (
                <PlanDetailsModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    plan={selectedPlan}
                    onApprove={handleApprove}
                    onCustomize={handleCustomize}
                    onRegenerate={handleRegenerate}
                />
            )}
        </div>
    );
}
