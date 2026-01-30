import { useState } from 'react';
import { Upload, FileText, Video, Headphones, Image as ImageIcon, Link as LinkIcon, Loader2, CheckCircle, Sparkles, Filter } from 'lucide-react';
import LearningNoteCard from '../components/LearningNoteCard';

type ProcessingStatus = 'ingesting' | 'style-matching' | 'ready';

interface ProcessingFile {
    id: string;
    name: string;
    type: 'pdf' | 'video' | 'audio' | 'image' | 'url';
    status: ProcessingStatus;
    progress?: number;
}

export default function KnowledgeBank() {
    const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([
        {
            id: '1',
            name: 'Neural Networks Lecture.mp4',
            type: 'video',
            status: 'ingesting',
            progress: 45,
        },
        {
            id: '2',
            name: 'Quantum Physics Notes.pdf',
            type: 'pdf',
            status: 'style-matching',
            progress: 78,
        },
    ]);

    const [selectedTopic, setSelectedTopic] = useState<string>('all');

    // Topic clusters with notes
    const topicClusters = {
        'Neural Networks': [
            {
                type: 'video' as const,
                title: 'Deep Learning Fundamentals',
                description: 'Comprehensive overview of neural network architectures and backpropagation...',
                tags: ['DeepML', 'AI', 'CNN'],
                author: 'AI Summary',
                timestamp: '2h ago',
            },
            {
                type: 'pdf' as const,
                title: 'Intro to Neural Networks',
                description: 'Foundational concepts of backpropagation and activation functions...',
                tags: ['DeepML', 'AI'],
                author: 'Key Concepts',
                timestamp: '1d ago',
            },
        ],
        'History': [
            {
                type: 'video' as const,
                title: 'The Renaissance Art Movement',
                description: 'Comprehensive overview of key figures like da Vinci and Michelangelo...',
                tags: ['History', '16thCentury'],
                author: 'AI Summary',
                timestamp: '2h ago',
            },
            {
                type: 'audio' as const,
                title: 'World War II Timeline',
                description: 'Audio recording covering major events from 1939 to 1945...',
                tags: ['History', 'WWII'],
                author: 'Transcript',
                timestamp: '3d ago',
            },
        ],
        'Chemistry': [
            {
                type: 'audio' as const,
                title: 'Organic Compounds List',
                description: 'Audio recording of the professor listing essential organic compounds...',
                tags: ['Science', 'Chem'],
                author: 'Transcript',
                timestamp: '5d ago',
            },
            {
                type: 'pdf' as const,
                title: 'Chemical Bonding Basics',
                description: 'Overview of ionic, covalent, and metallic bonds with examples...',
                tags: ['Science', 'Chem'],
                author: 'Key Concepts',
                timestamp: '1w ago',
            },
        ],
    };

    const allNotes = Object.values(topicClusters).flat();
    const topics = ['all', ...Object.keys(topicClusters)];

    const displayedNotes = selectedTopic === 'all'
        ? allNotes
        : topicClusters[selectedTopic as keyof typeof topicClusters] || [];

    const statusConfig = {
        ingesting: {
            label: 'Ingesting',
            color: 'bg-blue-100 text-blue-700',
            icon: Loader2,
            iconClass: 'animate-spin',
        },
        'style-matching': {
            label: 'Style-Matching',
            color: 'bg-purple-100 text-purple-700',
            icon: Sparkles,
            iconClass: 'animate-pulse',
        },
        ready: {
            label: 'Ready',
            color: 'bg-green-100 text-green-700',
            icon: CheckCircle,
            iconClass: '',
        },
    };

    const fileTypeIcons = {
        pdf: FileText,
        video: Video,
        audio: Headphones,
        image: ImageIcon,
        url: LinkIcon,
    };

    return (
        <div className="max-w-7xl mx-auto px-6 py-12">
            <div className="mb-8">
                <h1 className="text-4xl font-serif font-bold text-gray-900 mb-2">
                    Knowledge Bank
                </h1>
                <p className="text-gray-600">
                    Your repository for all raw and processed intelligence
                </p>
            </div>

            {/* Batch Ingestion Hub */}
            <div className="mb-10">
                <div className="border-2 border-dashed border-blue-300 rounded-xl p-12 bg-blue-50/50 hover:bg-blue-50 transition-colors">
                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                            <Upload className="w-8 h-8 text-blue-600" />
                        </div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">
                            Batch Ingestion Hub
                        </h3>
                        <p className="text-gray-600 mb-6">
                            Drag & drop multiple files or click to browse
                        </p>
                        <div className="flex items-center justify-center gap-4 mb-6">
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <FileText className="w-4 h-4" />
                                <span>PDF</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <Video className="w-4 h-4" />
                                <span>MP4</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <Headphones className="w-4 h-4" />
                                <span>MP3</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <FileText className="w-4 h-4" />
                                <span>Markdown</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <LinkIcon className="w-4 h-4" />
                                <span>URL</span>
                            </div>
                        </div>
                        <button className="px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">
                            Browse Files
                        </button>
                    </div>
                </div>
            </div>

            {/* Live Processing Status */}
            {processingFiles.length > 0 && (
                <div className="mb-10">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Processing</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {processingFiles.map((file) => {
                            const config = statusConfig[file.status];
                            const Icon = config.icon;
                            const FileIcon = fileTypeIcons[file.type];

                            return (
                                <div key={file.id} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                                    <div className="flex items-start gap-3 mb-3">
                                        <div className="p-2 bg-gray-100 rounded">
                                            <FileIcon className="w-5 h-5 text-gray-600" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-medium text-gray-900 truncate">{file.name}</h3>
                                            <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold mt-1 ${config.color}`}>
                                                <Icon className={`w-3 h-3 ${config.iconClass}`} />
                                                {config.label}
                                            </div>
                                        </div>
                                    </div>
                                    {file.progress !== undefined && (
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div
                                                className="bg-trust-blue h-2 rounded-full transition-all duration-300"
                                                style={{ width: `${file.progress}%` }}
                                            ></div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Topic Filter */}
            <div className="flex items-center gap-4 mb-6">
                <div className="flex items-center gap-2 text-gray-700">
                    <Filter className="w-5 h-5" />
                    <span className="font-medium">Topics:</span>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                    {topics.map((topic) => (
                        <button
                            key={topic}
                            onClick={() => setSelectedTopic(topic)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${selectedTopic === topic
                                    ? 'bg-trust-blue text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            {topic === 'all' ? 'All Topics' : topic}
                        </button>
                    ))}
                </div>
            </div>

            {/* Topic Clusters / All Notes */}
            {selectedTopic === 'all' ? (
                // Show all topics with clusters
                <div className="space-y-10">
                    {Object.entries(topicClusters).map(([topic, notes]) => (
                        <div key={topic}>
                            <div className="flex items-center gap-3 mb-4">
                                <h2 className="text-2xl font-semibold text-gray-900">{topic}</h2>
                                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                                    {notes.length} notes
                                </span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {notes.map((note, index) => (
                                    <LearningNoteCard key={index} {...note} />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                // Show filtered topic
                <div>
                    <div className="flex items-center gap-3 mb-6">
                        <h2 className="text-2xl font-semibold text-gray-900">{selectedTopic}</h2>
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                            {displayedNotes.length} notes
                        </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {displayedNotes.map((note, index) => (
                            <LearningNoteCard key={index} {...note} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
