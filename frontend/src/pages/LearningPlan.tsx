import { useEffect, useState } from 'react';
import { Plus, ChevronLeft, ChevronRight, Sparkles, Trash2 } from 'lucide-react';
import LearningPlanCard from '../components/LearningPlanCard';
import ProposedPlanCard from '../components/ProposedPlanCard';
import PlanDetailsModal from '../components/PlanDetailsModal';
import { approveLearningPlan, createLearningPlan, listLearningPlans, listProposedLearningPlans, generateSuggestedPlans, pauseLearningPlan, resumeLearningPlan, deleteLearningPlan, getLearningPlan, checkLearningPlanContent } from '../api/client';
import { useNavigate } from 'react-router-dom';

export default function LearningPlan() {
    const navigate = useNavigate();
    const [userId, setUserId] = useState('');
    const [filter, setFilter] = useState('all');
    const [selectedPlan, setSelectedPlan] = useState<any>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [proposedPlansData, setProposedPlansData] = useState<any[]>([]);
    const [plansData, setPlansData] = useState<any[]>([]);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [deleteConfirmPlan, setDeleteConfirmPlan] = useState<string | null>(null);
    const [hasContent, setHasContent] = useState<boolean | null>(null);

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
        checkLearningPlanContent(userId)
            .then((res: { has_content?: boolean }) => setHasContent(res?.has_content ?? false))
            .catch(() => { /* On network/API failure leave hasContent null so we don't disable Generate or show "no content" banner */ });
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
        const buildModalPlan = (p: any) => {
            const timelineFromItems = Array.isArray(p.items)
                ? p.items.map((item: any, index: number) => ({
                    week: index + 1,
                    topic: item.title || `Module ${index + 1}`,
                }))
                : [];
            const timelineFromDetails = Array.isArray(p.details?.timeline)
                ? p.details.timeline
                : Array.isArray(p.details?.proposed_timeline)
                    ? p.details.proposed_timeline
                    : [];
            const proposedTimeline = timelineFromDetails.length ? timelineFromDetails : timelineFromItems;
            return {
                id: p.id,
                title: p.title,
                description: p.description,
                isProposed,
                duration: p.details?.duration || p.estimated_time || 'Unknown',
                timeline: p.details?.timeline_label || p.estimatedTime || p.estimated_time || 'Unknown',
                intensity: p.difficulty || 'Moderate Pace',
                formatBreakdown: p.details?.format_breakdown || {
                    audioSessions: 0,
                    deepDives: 0,
                },
                proposedTimeline,
                proposedSchedule: p.details?.proposed_schedule,
            };
        };
        if (plan?.id && userId && !Array.isArray(plan.items)) {
            getLearningPlan(plan.id, userId)
                .then((res: any) => {
                    const fullPlan = res?.plan ? { ...res.plan, items: res.items ?? [] } : plan;
                    setSelectedPlan(buildModalPlan(fullPlan));
                    setIsModalOpen(true);
                })
                .catch(() => {
                    setSelectedPlan(buildModalPlan(plan));
                    setIsModalOpen(true);
                });
        } else {
            setSelectedPlan(buildModalPlan(plan));
            setIsModalOpen(true);
        }
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

    const handlePausePlan = async (planId: string) => {
        if (!userId) return;
        try {
            await pauseLearningPlan(planId, userId);
            setStatusMessage('Plan paused successfully.');
            await loadPlans(userId);
        } catch (error) {
            console.error('Failed to pause plan', error);
            setStatusMessage('Failed to pause plan. Please try again.');
        }
    };

    const handleResumePlan = async (planId: string) => {
        if (!userId) return;
        try {
            await resumeLearningPlan(planId, userId);
            setStatusMessage('Plan resumed successfully.');
            await loadPlans(userId);
        } catch (error) {
            console.error('Failed to resume plan', error);
            setStatusMessage('Failed to resume plan. Please try again.');
        }
    };

    const handleEditPlan = (planId: string) => {
        navigate(`/plans/${planId}`);
    };

    const handleDeletePlan = async (planId: string) => {
        if (!userId || !planId) return;
        try {
            await deleteLearningPlan(planId, userId);
            await loadPlans(userId);
            setDeleteConfirmPlan(null);
            setStatusMessage('Plan deleted successfully!');
        } catch (error) {
            console.error('Failed to delete plan', error);
            setStatusMessage('Failed to delete plan. Please try again.');
            setDeleteConfirmPlan(null);
        }
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
                // Don't set category - let it be inferred from content or remain null
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

    const handleGenerateSuggested = async () => {
        if (!userId || isGenerating) return;
        setIsGenerating(true);
        try {
            const response = await generateSuggestedPlans(userId, 'growth', 3);
            if (response.status === 'success' && response.plans_generated > 0) {
                if (Array.isArray(response.plans) && response.plans.length > 0) {
                    setProposedPlansData((prev) => [...response.plans, ...prev]);
                }
                await loadPlans(userId);
                setStatusMessage(`Successfully generated ${response.plans_generated} suggested plan(s)!`);
            } else {
                setStatusMessage('No plans could be generated. Upload content and try again.');
            }
        } catch (error: any) {
            console.error('Failed to generate suggested plans', error);
            const detail = error.response?.data?.detail;
            if (typeof detail === 'string' && (detail.includes('No content') || detail.includes('No content available'))) {
                setStatusMessage('Upload content first, then try again.');
            } else if (typeof detail === 'string' && (detail.includes('planner agent') || detail.includes('Failed to communicate'))) {
                setStatusMessage('Planner service is unavailable. Try again later.');
            } else if (typeof detail === 'string' && detail.includes('Could not parse plans')) {
                setStatusMessage('Generation completed but we couldn\'t read the result. Try again.');
            } else if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
                setStatusMessage('Connection failed. Check your network and try again.');
            } else {
                setStatusMessage(detail || 'Failed to generate suggested plans. Please try again.');
            }
        } finally {
            setIsGenerating(false);
        }
    };

    const normalizeProposedPlan = (plan: any) => ({
        id: plan.id,
        title: plan.title || 'Untitled Plan',
        description: plan.description || 'No description provided.',
        estimatedTime: plan.estimated_time || '4 weeks',
        moduleCount: plan.module_count || 8,
        difficulty: (plan.difficulty || 'Intermediate') as 'Beginner' | 'Intermediate' | 'Advanced',
        category: plan.category || undefined, // Don't default to 'TECH'
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
            category: plan.category || undefined, // Don't default to 'TECH'
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

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleGenerateSuggested}
                        disabled={isGenerating || hasContent === false}
                        className="flex items-center gap-2 px-6 py-3 bg-white border-2 border-trust-blue text-trust-blue rounded-lg hover:bg-blue-50 transition-colors font-medium disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        <Sparkles className={`w-5 h-5 ${isGenerating ? 'animate-pulse' : ''}`} />
                        {isGenerating ? 'Generating...' : 'Generate Suggested Plans'}
                    </button>
                    <button
                        onClick={handleCreatePlan}
                        className="flex items-center gap-2 px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                        <Plus className="w-5 h-5" />
                        Create New Plan
                    </button>
                </div>
            </div>

            {hasContent === false && (
                <div className="mb-6 rounded-md bg-amber-50 text-amber-800 text-sm px-4 py-2">
                    Upload and process content first to generate plans.
                </div>
            )}

            {statusMessage && (
                <div className="mb-6 rounded-md bg-blue-50 text-blue-700 text-sm px-4 py-2">
                    {statusMessage}
                </div>
            )}

            {/* Active Plan Box - Show current active plan prominently */}
            {(() => {
                const activePlan = resolvedPlans.find(p => p.status === 'active');
                if (activePlan) {
                    // Find the full plan data (with items) for modal
                    const fullActivePlan = plansData.find(p => p.id === activePlan.id);
                    return (
                        <div className="mb-10">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Currently Active Plan</h2>
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border-2 border-trust-blue shadow-sm">
                                <LearningPlanCard 
                                    {...activePlan}
                                    id={activePlan.id}
                                    onPause={handlePausePlan}
                                    onResume={handleResumePlan}
                                    onViewDetails={() => {
                                        if (fullActivePlan) {
                                            handlePlanClick(fullActivePlan, false);
                                        }
                                    }}
                                    onEdit={handleEditPlan}
                                    onDelete={(planId) => setDeleteConfirmPlan(planId)}
                                />
                            </div>
                        </div>
                    );
                }
                return null;
            })()}

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
                    <p className="text-gray-600">
                        Use the "Create New Plan" button above to get started
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredPlans
                        .filter(plan => {
                            // If filter is 'all' and we're showing active plan in featured box, exclude it from grid to avoid duplication
                            if (filter === 'all' && plan.status === 'active' && resolvedPlans.some(p => p.status === 'active')) {
                                return false;
                            }
                            return true;
                        })
                        .map((plan, index) => {
                            const planId = (plan as { id?: string }).id;
                            return (
                                <div key={planId || index} className="group">
                                    <LearningPlanCard 
                                        {...plan} 
                                        id={planId}
                                        onPause={handlePausePlan}
                                        onResume={handleResumePlan}
                                        onEdit={handleEditPlan}
                                        onDelete={(planId) => setDeleteConfirmPlan(planId)}
                                    />
                                </div>
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

            {/* Delete Confirmation Modal */}
            {deleteConfirmPlan && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Delete Learning Plan</h3>
                        <p className="text-gray-600 mb-6">
                            Are you sure you want to delete this plan? This action cannot be undone and will delete all associated modules and progress.
                        </p>
                        <div className="flex items-center gap-3 justify-end">
                            <button
                                onClick={() => setDeleteConfirmPlan(null)}
                                className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => handleDeletePlan(deleteConfirmPlan)}
                                className="px-4 py-2 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
                            >
                                Delete Plan
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
