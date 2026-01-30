import { X, Clock, Calendar, Zap, Headphones, Video, Edit, RefreshCw, CheckCircle } from 'lucide-react';

interface PlanDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    plan: {
        title: string;
        description?: string;
        isProposed?: boolean;
        duration: string;
        timeline: string;
        intensity: string;
        formatBreakdown: {
            audioSessions: number;
            deepDives: number;
        };
        proposedTimeline: {
            week: number;
            topic: string;
        }[];
        proposedSchedule?: {
            week: number;
            topic: string;
            calendarInfo?: string;
        };
    };
    onApprove?: () => void;
    onCustomize?: () => void;
    onRegenerate?: () => void;
}

export default function PlanDetailsModal({
    isOpen,
    onClose,
    plan,
    onApprove,
    onCustomize,
    onRegenerate,
}: PlanDetailsModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-start justify-between">
                    <div className="flex-1">
                        {plan.isProposed && (
                            <div className="inline-flex items-center gap-1 px-3 py-1 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full text-xs font-semibold mb-2">
                                <Zap className="w-3 h-3" />
                                AI PROPOSAL
                            </div>
                        )}
                        <h2 className="text-2xl font-serif font-bold text-gray-900 mb-1">
                            {plan.title}
                        </h2>
                        {plan.description && (
                            <p className="text-sm text-gray-600">{plan.description}</p>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors ml-4"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="px-6 py-6 space-y-6">
                    {/* Key Metrics */}
                    <div className="grid grid-cols-3 gap-4">
                        <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center gap-2 text-gray-600 mb-2">
                                <Clock className="w-4 h-4" />
                                <span className="text-xs font-medium">Total Duration</span>
                            </div>
                            <p className="text-xl font-bold text-gray-900">{plan.duration}</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center gap-2 text-gray-600 mb-2">
                                <Calendar className="w-4 h-4" />
                                <span className="text-xs font-medium">Timeline</span>
                            </div>
                            <p className="text-xl font-bold text-gray-900">{plan.timeline}</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center gap-2 text-gray-600 mb-2">
                                <Zap className="w-4 h-4" />
                                <span className="text-xs font-medium">Intensity</span>
                            </div>
                            <p className="text-xl font-bold text-gray-900">{plan.intensity}</p>
                        </div>
                    </div>

                    {/* Format Breakdown */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">Format Breakdown</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-100 rounded-lg">
                                        <Headphones className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-blue-900">{plan.formatBreakdown.audioSessions}</p>
                                        <p className="text-sm text-blue-700">Audio Sessions</p>
                                        <p className="text-xs text-blue-600 mt-1">Optimized for your commute</p>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-purple-100 rounded-lg">
                                        <Video className="w-5 h-5 text-purple-600" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-purple-900">{plan.formatBreakdown.deepDives}</p>
                                        <p className="text-sm text-purple-700">Deep Dives</p>
                                        <p className="text-xs text-purple-600 mt-1">Interactive text & code review</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Proposed Timeline */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">Proposed Timeline</h3>
                        <div className="relative">
                            <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-blue-200"></div>
                            <div className="space-y-4">
                                {plan.proposedTimeline.map((item, index) => (
                                    <div key={index} className="flex items-start gap-4 relative">
                                        <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center border-4 border-white relative z-10">
                                            <span className="text-sm font-bold text-blue-700">W{item.week}</span>
                                        </div>
                                        <div className="flex-1 bg-gray-50 rounded-lg p-3 mt-1">
                                            <p className="text-xs text-gray-500 mb-1">WEEK {item.week}</p>
                                            <p className="font-semibold text-gray-900">{item.topic}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Proposed Schedule */}
                    {plan.proposedSchedule && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">Proposed Schedule</h3>
                            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                                <div className="flex items-start gap-3">
                                    <div className="p-2 bg-blue-100 rounded-lg">
                                        <Calendar className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="font-semibold text-gray-900 mb-1">
                                            Week {plan.proposedSchedule.week}: {plan.proposedSchedule.topic}
                                        </p>
                                        {plan.proposedSchedule.calendarInfo && (
                                            <p className="text-sm text-gray-600 mb-3">{plan.proposedSchedule.calendarInfo}</p>
                                        )}
                                        <button className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
                                            <Calendar className="w-4 h-4" />
                                            Connect Calendar
                                        </button>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" className="sr-only peer" />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                    </label>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer Actions */}
                <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex items-center justify-between">
                    {plan.isProposed ? (
                        <>
                            <button
                                onClick={onCustomize}
                                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors font-medium"
                            >
                                <Edit className="w-4 h-4" />
                                Customize Plan
                            </button>
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={onRegenerate}
                                    className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors font-medium"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Regenerate
                                </button>
                                <button
                                    onClick={onApprove}
                                    className="flex items-center gap-2 px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                                >
                                    <CheckCircle className="w-5 h-5" />
                                    Approve & Sync Schedule
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center gap-3 ml-auto">
                            <button
                                onClick={onClose}
                                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors font-medium"
                            >
                                Close
                            </button>
                            <button
                                onClick={onCustomize}
                                className="flex items-center gap-2 px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                            >
                                <Edit className="w-4 h-4" />
                                Edit Plan
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
