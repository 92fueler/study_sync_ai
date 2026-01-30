import { useState } from 'react';
import { X, Clock, Calendar, Zap, Headphones, Video, Edit, RefreshCw, CheckCircle, ChevronDown, MonitorPlay } from 'lucide-react';

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
    const [isRegenerateMenuOpen, setIsRegenerateMenuOpen] = useState(false);

    if (!isOpen) return null;

    // Regeneration Options
    const regenOptions = [
        { label: 'Longer Plan (+2 weeks)', icon: Calendar },
        { label: 'Shorter Plan (-1 week)', icon: Clock },
        { label: 'Longer Sessions (>1h)', icon: MonitorPlay },
        { label: 'Shorter Sessions (<30m)', icon: Zap },
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex-shrink-0 border-b border-gray-100 px-6 py-4 flex items-start justify-between bg-white rounded-t-2xl">
                    <div className="flex-1">
                        <h2 className="text-2xl font-serif font-bold text-gray-900 leading-tight">
                            {plan.title}
                        </h2>
                        {plan.description && (
                            <p className="text-sm text-gray-500 mt-1 line-clamp-1">{plan.description}</p>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors ml-4 text-gray-400 hover:text-gray-600"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar">
                    {/* Compact Metrics & Breakdown Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        {/* Metrics */}
                        <div className="grid grid-cols-3 gap-3">
                            <div className="bg-gray-50 rounded-xl p-3 border border-gray-100 text-center">
                                <Clock className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                                <p className="text-sm font-bold text-gray-900">{plan.duration}</p>
                                <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Duration</span>
                            </div>
                            <div className="bg-gray-50 rounded-xl p-3 border border-gray-100 text-center">
                                <Calendar className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                                <p className="text-sm font-bold text-gray-900 whitespace-nowrap">{plan.timeline}</p>
                                <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Timeline</span>
                            </div>
                            <div className="bg-gray-50 rounded-xl p-3 border border-gray-100 text-center">
                                <Zap className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                                <p className="text-sm font-bold text-gray-900">{plan.intensity}</p>
                                <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Intensity</span>
                            </div>
                        </div>

                        {/* Breakdown */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-white rounded-xl p-3 border border-blue-100 shadow-sm flex items-center gap-3">
                                <div className="p-2 bg-blue-50 rounded-lg">
                                    <Headphones className="w-4 h-4 text-blue-600" />
                                </div>
                                <div>
                                    <p className="text-lg font-bold text-gray-900 leading-none">{plan.formatBreakdown.audioSessions}</p>
                                    <p className="text-xs text-gray-500">Audio Sessions</p>
                                </div>
                            </div>
                            <div className="bg-white rounded-xl p-3 border border-purple-100 shadow-sm flex items-center gap-3">
                                <div className="p-2 bg-purple-50 rounded-lg">
                                    <Video className="w-4 h-4 text-purple-600" />
                                </div>
                                <div>
                                    <p className="text-lg font-bold text-gray-900 leading-none">{plan.formatBreakdown.deepDives}</p>
                                    <p className="text-xs text-gray-500">Deep Dives</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Timeline */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-base font-bold text-gray-900">Proposed Timeline (6 Weeks)</h3>
                            <button className="text-xs font-semibold text-trust-blue hover:text-blue-700">View Details</button>
                        </div>

                        <div className="relative pt-2 pb-2">
                            {/* Horizontal Line connecting dots */}
                            <div className="absolute top-4 left-4 right-4 h-0.5 bg-gray-100" />

                            <div className="grid grid-cols-6 gap-2 relative z-10">
                                {plan.proposedTimeline.map((item, index) => (
                                    <div key={index} className="text-center group flex flex-col items-center">
                                        <div className="w-2.5 h-2.5 bg-trust-blue rounded-full border-2 border-white shadow-sm mb-2 relative z-10 box-content group-hover:scale-125 transition-transform" />
                                        <p className="text-[9px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">W{item.week}</p>
                                        <p className="text-[10px] font-semibold text-gray-900 leading-tight w-full truncate px-1" title={item.topic}>
                                            {item.topic.split(' ')[0]} {/* Show first word only for compactness, full text in tooltip */}
                                        </p>
                                    </div>
                                ))}
                                {/* Mocking extra weeks if needed to show 6 columns layout visual */}
                                {[4, 5, 6].map(week => (
                                    <div key={week} className="text-center group flex flex-col items-center opacity-50">
                                        <div className="w-2.5 h-2.5 bg-gray-200 rounded-full border-2 border-white shadow-sm mb-2 relative z-10 box-content" />
                                        <p className="text-[9px] font-bold text-gray-300 uppercase tracking-wider mb-0.5">W{week}</p>
                                        <p className="text-[10px] font-semibold text-gray-400 leading-tight w-full truncate px-1">Concept</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Google Calendar Banner (Proposed Schedule) */}
                    {plan.proposedSchedule && (
                        <div className="bg-blue-50 rounded-xl p-5 border border-blue-100 flex items-center justify-between shadow-sm">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-white rounded-xl shadow-sm border border-blue-50">
                                    <Calendar className="w-6 h-6 text-trust-blue" />
                                </div>
                                <div>
                                    <h4 className="font-bold text-gray-900 text-sm">Connect Google Calendar</h4>
                                    <p className="text-xs text-blue-700 mt-1">
                                        Sync <strong>{plan.proposedSchedule.topic}</strong> sessions to avoid conflicts.
                                    </p>
                                </div>
                            </div>
                            <button className="px-4 py-2 bg-white text-trust-blue text-sm font-bold rounded-lg shadow-sm border border-blue-100 hover:bg-blue-50 transition-colors">
                                Connect Calendar
                            </button>
                        </div>
                    )}
                </div>

                {/* Footer Actions */}
                <div className="flex-shrink-0 border-t border-gray-100 px-6 py-4 bg-gray-50 rounded-b-2xl flex items-center justify-between">
                    <button
                        onClick={onCustomize}
                        className="text-sm font-semibold text-gray-600 hover:text-gray-900 flex items-center gap-2"
                    >
                        <Edit className="w-4 h-4" />
                        Customize Plan
                    </button>

                    <div className="flex items-center gap-3">
                        {/* Regenerate Menu */}
                        <div className="relative">
                            <button
                                onClick={() => setIsRegenerateMenuOpen(!isRegenerateMenuOpen)}
                                className="px-4 py-2.5 bg-white border border-gray-200 text-gray-700 text-sm font-semibold rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2 shadow-sm"
                            >
                                <RefreshCw className="w-4 h-4" />
                                Regenerate
                                <ChevronDown className="w-3 h-3 text-gray-400" />
                            </button>

                            {isRegenerateMenuOpen && (
                                <div className="absolute bottom-full mb-2 left-0 w-64 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden z-20 py-1 slide-up-animation">
                                    <p className="px-4 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-wider bg-gray-50 border-b border-gray-100">
                                        Adjust Plan
                                    </p>
                                    {regenOptions.map((opt, idx) => (
                                        <button
                                            key={idx}
                                            className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 flex items-center gap-3 transition-colors"
                                            onClick={() => {
                                                console.log(`Regenerate: ${opt.label}`);
                                                setIsRegenerateMenuOpen(false);
                                                onRegenerate?.(); // Call parent handler
                                            }}
                                        >
                                            <opt.icon className="w-4 h-4 opacity-50" />
                                            {opt.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        <button
                            onClick={onApprove}
                            className="px-6 py-2.5 bg-trust-blue text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-md flex items-center gap-2"
                        >
                            <CheckCircle className="w-4 h-4" />
                            Approve & Sync Schedule
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
