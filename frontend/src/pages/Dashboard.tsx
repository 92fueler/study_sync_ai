import { useState } from 'react';
import { FileText, Link as LinkIcon, FileUp, Paperclip, Mic, Sparkles, ArrowRight } from 'lucide-react';
import LearningPlanCard from '../components/LearningPlanCard';
import LearningNoteCard from '../components/LearningNoteCard';

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState('raw-notes');

    const learningPlans = [
        {
            status: 'active' as const,
            title: 'Introduction to Neuroscience',
            difficulty: 'Intermediate',
            percentage: 78,
            nextSession: '12 mins remaining',
        },
        {
            status: 'active' as const,
            title: 'Modern European History',
            difficulty: 'Advanced',
            percentage: 34,
            nextSession: '45 mins remaining',
        },
        {
            status: 'active' as const,
            title: 'Python for Data Science',
            difficulty: 'Beginner',
            percentage: 12,
            nextSession: '2h 15m remaining',
        },
    ];

    const learningNotes = [
        {
            type: 'video' as const,
            title: 'The Renaissance Art Movement',
            description: 'Comprehensive overview of key figures like da Vinci and...',
            tags: ['History', '16thCentury'],
            author: 'AI Summary',
            timestamp: '2h ago',
        },
        {
            type: 'pdf' as const,
            title: 'Intro to Neural Networks',
            description: 'Foundational concepts of backpropagation and activation...',
            tags: ['DeepML', 'AI'],
            author: 'Key Concepts',
            timestamp: '1d ago',
        },
        {
            type: 'audio' as const,
            title: 'Organic Compounds List',
            description: 'Audio recording of the professor fixing essential organic...',
            tags: ['Science', 'Chem'],
            author: 'Transcript',
            timestamp: '5d ago',
        },
    ];

    return (
        <div className="max-w-7xl mx-auto px-6 py-12">
            <div className="text-center mb-12">
                <h1 className="text-5xl font-serif font-bold text-gray-900 mb-8">
                    Structure your chaos<br />into clarity
                </h1>

                <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center gap-4 mb-4 border-b border-gray-200">
                        <button
                            onClick={() => setActiveTab('raw-notes')}
                            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${activeTab === 'raw-notes'
                                    ? 'text-trust-blue border-b-2 border-trust-blue'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            <FileText className="w-4 h-4" />
                            Raw Notes
                        </button>
                        <button
                            onClick={() => setActiveTab('url-input')}
                            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${activeTab === 'url-input'
                                    ? 'text-trust-blue border-b-2 border-trust-blue'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            <LinkIcon className="w-4 h-4" />
                            URL Input
                        </button>
                        <button
                            onClick={() => setActiveTab('upload-pdf')}
                            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${activeTab === 'upload-pdf'
                                    ? 'text-trust-blue border-b-2 border-trust-blue'
                                    : 'text-gray-600 hover:text-gray-900'
                                }`}
                        >
                            <FileUp className="w-4 h-4" />
                            Upload PDF
                        </button>
                    </div>

                    <textarea
                        className="w-full h-32 p-4 text-gray-600 placeholder-gray-400 resize-none focus:outline-none"
                        placeholder="Paste a lecture URL, drag & drop a PDF, or start typing your chaotic thoughts here..."
                    />

                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                        <div className="flex items-center gap-3">
                            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                <Paperclip className="w-5 h-5 text-gray-400" />
                            </button>
                            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                <Mic className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        <button className="flex items-center gap-2 px-6 py-2.5 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">
                            <Sparkles className="w-4 h-4" />
                            Generate Structure
                        </button>
                    </div>
                </div>
            </div>

            <div className="mb-12">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900">Active Learning Plans</h2>
                    <button className="flex items-center gap-1 text-sm font-medium text-trust-blue hover:text-blue-700 transition-colors">
                        View All
                        <ArrowRight className="w-4 h-4" />
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {learningPlans.map((plan, index) => (
                        <LearningPlanCard key={index} {...plan} />
                    ))}
                </div>
            </div>

            <div className="mb-8">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900">Recent Learning Notes</h2>
                    <button className="flex items-center gap-1 text-sm font-medium text-trust-blue hover:text-blue-700 transition-colors">
                        View All
                        <ArrowRight className="w-4 h-4" />
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {learningNotes.map((note, index) => (
                        <LearningNoteCard key={index} {...note} />
                    ))}
                </div>
            </div>
        </div>
    );
}
