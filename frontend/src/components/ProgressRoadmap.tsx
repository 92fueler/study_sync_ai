import { CheckCircle2 } from 'lucide-react';

interface Milestone {
    id: string;
    title: string;
    isCompleted: boolean;
    isActive?: boolean;
}

interface ProgressRoadmapProps {
    milestones?: Milestone[];
}

export default function ProgressRoadmap({ milestones = [] }: ProgressRoadmapProps) {
    if (!milestones.length) {
        return (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-2">Session Roadmap</h3>
                <p className="text-sm text-gray-500">No roadmap data available yet.</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">Session Roadmap</h3>

            <div className="relative pl-2">
                {/* Vertical Line */}
                <div className="absolute left-[7px] top-2 bottom-4 w-0.5 bg-gray-100" />

                <div className="space-y-6">
                    {milestones.map((step) => (
                        <div key={step.id} className="relative flex items-start gap-4">
                            {/* Dot / Icon */}
                            <div className="relative z-10 flex-shrink-0 bg-white">
                                {step.isCompleted ? (
                                    <div className="w-4 h-4 rounded-full bg-green-500 border border-green-500 flex items-center justify-center">
                                        <span className="sr-only">Completed</span>
                                    </div>
                                ) : step.isActive ? (
                                    <div className="w-4 h-4 rounded-full border-2 border-trust-blue bg-white shadow-[0_0_0_2px_rgba(37,99,235,0.2)]">
                                        <span className="sr-only">Current</span>
                                    </div>
                                ) : (
                                    <div className="w-4 h-4 rounded-full border-2 border-gray-200 bg-white">
                                        <span className="sr-only">Future</span>
                                    </div>
                                )}
                            </div>

                            {/* Text */}
                            <div className="-mt-1">
                                <p className={`text-sm font-medium ${step.isActive ? 'text-trust-blue' :
                                    step.isCompleted ? 'text-gray-900' : 'text-gray-400'
                                    }`}>
                                    {step.title}
                                </p>
                                {step.isActive && (
                                    <p className="text-xs text-blue-600 mt-0.5 font-medium animate-pulse">
                                        In Progress
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="mt-8 pt-6 border-t border-gray-100">
                <button className="w-full py-2.5 bg-trust-blue text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Mark Topic Complete
                </button>
            </div>
        </div>
    );
}
