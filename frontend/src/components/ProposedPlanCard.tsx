import { Clock, BookOpen, ChevronRight, Cpu, Beaker, BookOpenText, Languages } from 'lucide-react';

interface ProposedPlanCardProps {
    title: string;
    description: string;
    estimatedTime: string;
    moduleCount: number;
    difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
    category: string;
    categoryColor?: 'blue' | 'orange' | 'purple' | 'green';
    aiGenerated?: boolean;
    onDetailsClick?: () => void;
}


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

const difficultyColors = {
    Beginner: 'bg-green-100 text-green-700',
    Intermediate: 'bg-yellow-100 text-yellow-700',
    Advanced: 'bg-red-100 text-red-700',
};

export default function ProposedPlanCard({
    title,
    description,
    estimatedTime,
    moduleCount,
    difficulty,
    category,
    categoryColor = 'blue',
    aiGenerated = true,
    onDetailsClick,
}: ProposedPlanCardProps) {
    return (
        <div className="flex-shrink-0 w-80 bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-all border-2 border-blue-100 hover:border-blue-300">
            {/* Difficulty Badge */}
            {aiGenerated && (
                <div className="mb-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${difficultyColors[difficulty]}`}>
                        {difficulty}
                    </span>
                </div>
            )}

            {/* Category Badge */}
            <div className={`inline-block px-3 py-1 rounded border text-xs font-medium mb-3 ${categoryColors[categoryColor]}`}>
                {category}
            </div>

            {/* Title with Icon */}
            <div className="flex items-start gap-3 mb-2">
                <div className={`p-2 rounded-lg ${categoryColors[categoryColor]}`}>
                    {(() => {
                        const IconComponent = categoryIcons[category as keyof typeof categoryIcons] || BookOpen;
                        return <IconComponent className="w-5 h-5" />;
                    })()}
                </div>
                <h3 className="text-lg font-bold text-gray-900 line-clamp-2 flex-1">{title}</h3>
            </div>

            {/* Description */}
            <p className="text-sm text-gray-600 mb-4 line-clamp-3">{description}</p>

            {/* Stats */}
            <div className="flex items-center gap-4 mb-4 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{estimatedTime}</span>
                </div>
                <div className="flex items-center gap-1">
                    <BookOpen className="w-4 h-4" />
                    <span>{moduleCount} modules</span>
                </div>
            </div>

            {/* Action Button */}
            <button
                onClick={onDetailsClick}
                className="w-full px-4 py-2 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center justify-center gap-1"
            >
                View Details
                <ChevronRight className="w-4 h-4" />
            </button>
        </div>
    );
}
