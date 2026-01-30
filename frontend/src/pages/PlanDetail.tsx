import { Link } from 'react-router-dom';
import {
    ChevronLeft, Clock, BookOpen, Play, CheckCircle,
    Lock, Calendar, Award, ArrowRight
} from 'lucide-react';

export default function PlanDetail() {
    // Mock Data for a specific plan
    const plan = {
        id: '1',
        title: 'Introduction to Neuroscience',
        description: 'Explore the biological foundations of behavior, from the structure of a single neuron to the complex organization of the brain.',
        category: 'SCIENCE',
        categoryColor: 'blue' as const,
        difficulty: 'Intermediate',
        progress: 65,
        totalModules: 12,
        completedModules: 7,
        estimatedTimeLeft: '5h 30m',
        nextSession: 'Tomorrow, 3:00 PM',
        instructors: ['Dr. Sarah Chen', 'AI Tutor'],
        modules: [
            {
                id: '1',
                title: 'Neuron Structure & Function',
                description: 'Anatomy of neurons, membrane potential, and action potentials.',
                duration: '45 min',
                status: 'completed' as const,
                type: 'video',
            },
            {
                id: '2',
                title: 'Synaptic Transmission',
                description: 'Mechanisms of neurotransmitter release and receptor activation.',
                duration: '60 min',
                status: 'in-progress' as const,
                type: 'reading',
                progress: 45,
            },
            {
                id: '3',
                title: 'Neuroplasticity',
                description: 'How the brain changes in response to experience.',
                duration: '50 min',
                status: 'locked' as const,
                type: 'quiz',
            },
            {
                id: '4',
                title: 'Sensory Systems',
                description: 'Visual, auditory, and somatosensory processing pathways.',
                duration: '1h 15m',
                status: 'locked' as const,
                type: 'video',
            },
            {
                id: '5',
                title: 'Motor Control',
                description: 'From cortex to muscle: the spinal cord and motor pathways.',
                duration: '55 min',
                status: 'locked' as const,
                type: 'video',
            }
        ]
    };

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
                    <div className="flex items-center gap-2 mb-6 text-sm text-gray-500">
                        <Link to="/plan" className="hover:text-gray-900 flex items-center gap-1">
                            <ChevronLeft className="w-4 h-4" />
                            Back to Plans
                        </Link>
                        <span>/</span>
                        <span>{plan.title}</span>
                    </div>

                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-3">
                                <span className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded uppercase tracking-wide">
                                    {plan.category}
                                </span>
                                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-bold rounded uppercase tracking-wide">
                                    {plan.difficulty}
                                </span>
                            </div>
                            <h1 className="text-3xl md:text-4xl font-serif font-bold text-gray-900 mb-4">
                                {plan.title}
                            </h1>
                            <p className="text-gray-600 max-w-2xl text-lg leading-relaxed mb-6">
                                {plan.description}
                            </p>

                            <div className="flex items-center gap-6 text-sm text-gray-600">
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-blue-500" />
                                    <span>{plan.estimatedTimeLeft} left</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <BookOpen className="w-4 h-4 text-purple-500" />
                                    <span>{plan.completedModules}/{plan.totalModules} modules</span>
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
                                <span className="text-2xl font-bold text-blue-600">{plan.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2 mb-6">
                                <div
                                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${plan.progress}%` }}
                                />
                            </div>

                            <div className="flex items-center gap-3 mb-6 p-3 bg-blue-50 rounded-lg">
                                <Calendar className="w-5 h-5 text-blue-600" />
                                <div>
                                    <p className="text-xs uppercase font-bold text-blue-400 mb-0.5">Next Session</p>
                                    <p className="text-sm font-semibold text-blue-900">{plan.nextSession}</p>
                                </div>
                            </div>

                            <Link
                                to={`/session/1`} // Linking to our StudySession page
                                className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors shadow-md hover:shadow-lg"
                            >
                                <Play className="w-4 h-4 fill-current" />
                                Resume Learning
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* Modules List */}
            <div className="max-w-4xl mx-auto px-6 py-12">
                <h2 className="text-xl font-bold text-gray-900 mb-6">Course Modules</h2>
                <div className="space-y-4">
                    {plan.modules.map((module, index) => {
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
                                                    style={{ width: `${module.progress}%` }}
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
                                                    <Link to={`/session/${module.id}`} className="text-blue-600 hover:text-blue-700 flex items-center gap-1">
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
        </div>
    );
}
