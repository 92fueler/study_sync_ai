import { useState } from 'react';
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import LearningPlanCard from '../components/LearningPlanCard';
import ProposedPlanCard from '../components/ProposedPlanCard';
import PlanDetailsModal from '../components/PlanDetailsModal';

export default function LearningPlan() {
    const [filter, setFilter] = useState('all');
    const [selectedPlan, setSelectedPlan] = useState<any>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handlePlanClick = (plan: any, isProposed: boolean) => {
        // Transform plan data for modal
        const modalPlan = {
            title: plan.title,
            description: plan.description,
            isProposed,
            duration: '5 Hours',
            timeline: isProposed ? plan.estimatedTime : 'Oct 10 - Oct 24',
            intensity: plan.difficulty || 'Moderate Pace',
            formatBreakdown: {
                audioSessions: 2,
                deepDives: 3,
            },
            proposedTimeline: [
                { week: 1, topic: 'Core Syntax' },
                { week: 1.5, topic: 'Type System' },
                { week: 2, topic: 'Error Handling' },
                { week: 2, topic: 'Project' },
            ],
            proposedSchedule: {
                week: 1,
                topic: 'Core Syntax',
                calendarInfo: "We'll need defaults to avoid conflicts with your work meetings.",
            },
        };
        setSelectedPlan(modalPlan);
        setIsModalOpen(true);
    };

    const handleApprove = () => {
        console.log('Plan approved!');
        setIsModalOpen(false);
        // Add logic to move plan from proposed to active
    };

    const handleCustomize = () => {
        console.log('Customize plan');
        // Add logic to open customization view
    };

    const handleRegenerate = () => {
        console.log('Regenerate plan');
        // Add logic to regenerate plan
    };

    const proposedPlans = [
        {
            title: 'Machine Learning Fundamentals',
            description: 'Master the core concepts of ML including supervised learning, neural networks, and model evaluation techniques.',
            estimatedTime: '6 weeks',
            moduleCount: 14,
            difficulty: 'Intermediate' as const,
            category: 'TECH',
            categoryColor: 'purple' as const,
        },
        {
            title: 'Ancient Greek Philosophy',
            description: 'Explore the foundational ideas of Socrates, Plato, and Aristotle that shaped Western thought.',
            estimatedTime: '4 weeks',
            moduleCount: 10,
            difficulty: 'Advanced' as const,
            category: 'HUMANITIES',
            categoryColor: 'orange' as const,
        },
        {
            title: 'Organic Chemistry Basics',
            description: 'Learn the fundamentals of carbon compounds, reaction mechanisms, and molecular structures.',
            estimatedTime: '8 weeks',
            moduleCount: 16,
            difficulty: 'Intermediate' as const,
            category: 'SCIENCE',
            categoryColor: 'blue' as const,
        },
        {
            title: 'Japanese Language for Beginners',
            description: 'Start your journey with hiragana, katakana, basic grammar, and everyday conversational phrases.',
            estimatedTime: '12 weeks',
            moduleCount: 24,
            difficulty: 'Beginner' as const,
            category: 'LANGUAGE',
            categoryColor: 'green' as const,
        },
    ];

    const allPlans = [
        {
            status: 'active' as const,
            category: 'SCIENCE',
            categoryColor: 'blue' as const,
            title: 'Introduction to Neuroscience',
            difficulty: 'Intermediate',
            percentage: 78,
            module: 'Synaptic Transmission & Plasticity',
            timeRemaining: '4h 30m left',
            totalModules: 12,
            completedModules: 9,
            nextSession: 'Tomorrow, 3:00 PM',
        },
        {
            status: 'active' as const,
            category: 'HUMANITIES',
            categoryColor: 'orange' as const,
            title: 'Modern European History',
            difficulty: 'Advanced',
            percentage: 34,
            module: 'The Industrial Revolution',
            timeRemaining: '12h left',
            totalModules: 15,
            completedModules: 5,
            nextSession: 'Today, 6:00 PM',
        },
        {
            status: 'active' as const,
            category: 'TECH',
            categoryColor: 'purple' as const,
            title: 'Python for Data Science',
            difficulty: 'Beginner',
            percentage: 12,
            module: 'Pandas & NumPy Basics',
            timeRemaining: '28h left',
            totalModules: 10,
            completedModules: 1,
            nextSession: 'Friday, 10:00 AM',
        },
        {
            status: 'paused' as const,
            category: 'SCIENCE',
            categoryColor: 'blue' as const,
            title: 'Quantum Mechanics Fundamentals',
            difficulty: 'Advanced',
            percentage: 45,
            module: 'Wave-Particle Duality',
            totalModules: 16,
            completedModules: 7,
            pausedDate: '2 weeks ago',
        },
        {
            status: 'paused' as const,
            category: 'LANGUAGE',
            categoryColor: 'green' as const,
            title: 'Spanish Language Basics',
            difficulty: 'Beginner',
            percentage: 23,
            module: 'Present Tense Verbs',
            totalModules: 20,
            completedModules: 4,
            pausedDate: '1 month ago',
        },
        {
            status: 'completed' as const,
            category: 'TECH',
            categoryColor: 'purple' as const,
            title: 'Introduction to React',
            difficulty: 'Intermediate',
            percentage: 100,
            module: 'Final Project Completed',
            totalModules: 12,
            completedModules: 12,
            achievement: 'Mastery Verified - Completed on Oct 12',
        },
        {
            status: 'completed' as const,
            category: 'HUMANITIES',
            categoryColor: 'orange' as const,
            title: 'World War II History',
            difficulty: 'Intermediate',
            percentage: 100,
            module: 'Post-War Reconstruction',
            totalModules: 10,
            completedModules: 10,
            achievement: 'Certificate Earned - Completed on Sep 28',
        },
    ];

    const filteredPlans = filter === 'all'
        ? allPlans
        : allPlans.filter(plan => plan.status === filter);

    const statusCounts = {
        all: allPlans.length,
        active: allPlans.filter(p => p.status === 'active').length,
        paused: allPlans.filter(p => p.status === 'paused').length,
        completed: allPlans.filter(p => p.status === 'completed').length,
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

                <button className="flex items-center gap-2 px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">
                    <Plus className="w-5 h-5" />
                    Create New Plan
                </button>
            </div>

            {/* Proposed Plans Carousel */}
            {proposedPlans.length > 0 && (
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
                            {proposedPlans.map((plan, index) => (
                                <ProposedPlanCard
                                    key={index}
                                    {...plan}
                                    onDetailsClick={() => handlePlanClick(plan, true)}
                                />
                            ))}
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
                    <button className="px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">
                        Create Plan
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredPlans.map((plan, index) => (
                        <LearningPlanCard key={index} {...plan} />
                    ))}
                </div>
            )}

            {/* Plan Details Modal */}
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
