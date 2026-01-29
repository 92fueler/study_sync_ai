import { Clock, Play, Pause, Eye, CheckCircle, Trophy, Calendar, MoreVertical, Cpu, Beaker, BookOpenText, Languages, BookOpen } from 'lucide-react';

interface LearningPlanCardProps {
    status: 'active' | 'paused' | 'completed';
    title: string;
    difficulty: string;
    percentage: number;
    nextSession?: string;
    pausedDate?: string;
    category?: string;
    categoryColor?: 'blue' | 'orange' | 'purple' | 'green';
    module?: string;
    timeRemaining?: string;
    totalModules?: number;
    completedModules?: number;
    achievement?: string;
}

const statusConfig = {
    active: {
        badge: 'ACTIVE',
        badgeColor: 'bg-green-100 text-green-700',
        progressColor: 'text-trust-blue',
        ringColor: 'stroke-trust-blue',
    },
    paused: {
        badge: 'PAUSED',
        badgeColor: 'bg-orange-100 text-orange-700',
        progressColor: 'text-orange-600',
        ringColor: 'stroke-orange-600',
    },
    completed: {
        badge: 'ACHIEVED',
        badgeColor: 'bg-green-100 text-green-700',
        progressColor: 'text-success-green',
        ringColor: 'stroke-success-green',
    },
};

const categoryColors = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    green: 'bg-green-50 text-green-600 border-green-200',
};

const categoryIcons = {
    TECH: Cpu,
    SCIENCE: Beaker,
    HUMANITIES: BookOpenText,
    LANGUAGE: Languages,
};

export default function LearningPlanCard({
    status,
    title,
    difficulty,
    percentage,
    nextSession,
    pausedDate,
    category,
    categoryColor = 'blue',
    module,
    timeRemaining,
    totalModules = 12,
    completedModules,
    achievement,
}: LearningPlanCardProps) {
    const config = statusConfig[status];
    const completed = completedModules || Math.floor((percentage / 100) * totalModules);

    return (
        <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border border-gray-100">
            {/* Header with status badge and menu */}
            <div className="flex items-start justify-between mb-4">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.badgeColor}`}>
                    {config.badge}
                </span>
                <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                    <MoreVertical className="w-4 h-4 text-gray-400" />
                </button>
            </div>

            {/* Category badge if provided */}
            {category && (
                <div className={`inline-block px-3 py-1 rounded border text-xs font-medium mb-3 ${categoryColors[categoryColor]}`}>
                    {category}
                </div>
            )}

            {/* Title with Icon */}
            <div className="flex items-start gap-3 mb-3">
                {category && (
                    <div className={`p-2 rounded-lg ${categoryColors[categoryColor]}`}>
                        {(() => {
                            const IconComponent = categoryIcons[category as keyof typeof categoryIcons] || BookOpen;
                            return <IconComponent className="w-5 h-5" />;
                        })()}
                    </div>
                )}
                <h3 className="text-lg font-bold text-gray-900 line-clamp-2 flex-1">{title}</h3>
            </div>

            {/* Progress Circle and Stats */}
            <div className="flex items-center gap-4 mb-4">
                <div className="relative">
                    <svg className="w-16 h-16 transform -rotate-90">
                        <circle
                            cx="32"
                            cy="32"
                            r="28"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                            className="text-gray-200"
                        />
                        <circle
                            cx="32"
                            cy="32"
                            r="28"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                            strokeDasharray={`${2 * Math.PI * 28}`}
                            strokeDashoffset={`${2 * Math.PI * 28 * (1 - percentage / 100)}`}
                            className={config.ringColor}
                            strokeLinecap="round"
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-lg font-bold ${config.progressColor}`}>{percentage}%</span>
                    </div>
                </div>

                <div className="flex-1">
                    <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                        <Clock className="w-4 h-4" />
                        <span>{timeRemaining || `${completed}/${totalModules} Modules`}</span>
                    </div>
                    {module && (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Trophy className="w-4 h-4" />
                            <span className="line-clamp-1">{module}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Next Session / Status Info */}
            {status === 'active' && nextSession && (
                <div className="bg-blue-50 rounded-lg p-3 mb-4">
                    <div className="text-xs font-semibold text-blue-900 mb-1">NEXT SESSION</div>
                    <div className="flex items-center gap-2 text-sm text-blue-700">
                        <Calendar className="w-4 h-4" />
                        <span>{nextSession}</span>
                    </div>
                </div>
            )}

            {status === 'paused' && pausedDate && (
                <div className="bg-orange-50 rounded-lg p-3 mb-4">
                    <div className="text-xs font-semibold text-orange-900 mb-1">STATUS</div>
                    <div className="flex items-center gap-2 text-sm text-orange-700">
                        <Pause className="w-4 h-4" />
                        <span>Plan is currently on hold</span>
                    </div>
                    <div className="text-xs text-orange-600 mt-1">Paused {pausedDate}</div>
                </div>
            )}

            {status === 'completed' && achievement && (
                <div className="bg-green-50 rounded-lg p-3 mb-4">
                    <div className="text-xs font-semibold text-green-900 mb-1">ACHIEVED</div>
                    <div className="flex items-center gap-2 text-sm text-green-700">
                        <CheckCircle className="w-4 h-4" />
                        <span>{achievement}</span>
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-2 pt-4 border-t border-gray-100">
                {status === 'active' && (
                    <>
                        <button className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                            <Pause className="w-4 h-4" />
                            Pause Plan
                        </button>
                        <button className="flex items-center gap-1 px-3 py-2 text-sm text-trust-blue hover:bg-blue-50 rounded-lg transition-colors ml-auto">
                            View Details
                            <Eye className="w-4 h-4" />
                        </button>
                    </>
                )}

                {status === 'paused' && (
                    <>
                        <button className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                            <Eye className="w-4 h-4" />
                            View Details
                        </button>
                        <button className="flex items-center gap-1 px-3 py-2 text-sm text-trust-blue hover:bg-blue-50 rounded-lg transition-colors ml-auto">
                            <Play className="w-4 h-4" />
                            Resume Plan
                        </button>
                    </>
                )}

                {status === 'completed' && (
                    <>
                        <button className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                            <Trophy className="w-4 h-4" />
                            Review
                        </button>
                        <button className="flex items-center gap-1 px-3 py-2 text-sm text-trust-blue hover:bg-blue-50 rounded-lg transition-colors ml-auto">
                            View Certificate
                            <Eye className="w-4 h-4" />
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}
