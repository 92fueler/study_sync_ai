import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Link as LinkIcon, FileUp, Paperclip, Mic, Sparkles, ArrowRight } from 'lucide-react';
import LearningPlanCard from '../components/LearningPlanCard';
import LearningNoteCard from '../components/LearningNoteCard';

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState('raw-notes');

    const learningPlans = [
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
            nextSession: '12 mins remaining',
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
            nextSession: '45 mins remaining',
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
            nextSession: '2h 15m remaining',
        },
    ];

    const learningNotes = [
        {
            type: 'video' as const,
            title: 'Deep Learning Fundamentals',
            description: 'Comprehensive overview of neural network architectures and backpropagation algorithms.',
            tags: [
                { type: 'format' as const, label: 'Video' },
                { type: 'format' as const, label: 'Notes' },
                { type: 'topic' as const, label: 'DeepML' },
                { type: 'style' as const, label: 'Deep Dive' }
            ],
            author: 'AI Summary',
            timestamp: '2h ago',
        },
        {
            type: 'pdf' as const,
            title: 'The Renaissance Art Movement',
            description: 'Key figures like da Vinci and Michelangelo and their impact on European culture.',
            tags: [
                { type: 'format' as const, label: 'PDF' },
                { type: 'format' as const, label: 'Slides' },
                { type: 'topic' as const, label: 'History' },
                { type: 'topic' as const, label: 'Art' }
            ],
            author: 'Lecture Notes',
            timestamp: '5h ago',
        },
        {
            type: 'audio' as const,
            title: 'Quantum Physics: Superposition',
            description: 'Understanding the principles of superposition and quantum states.',
            tags: [
                { type: 'format' as const, label: 'Audio' },
                { type: 'format' as const, label: 'Transcript' },
                { type: 'style' as const, label: 'Deep Dive' },
                { type: 'topic' as const, label: 'Physics' }
            ],
            author: 'Transcript',
            timestamp: '1d ago',
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
                        <Link key={index} to={`/notes/${index + 1}`} className="block">
                            <LearningNoteCard {...note} />
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
