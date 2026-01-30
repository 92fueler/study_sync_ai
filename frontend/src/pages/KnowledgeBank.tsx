import { useState } from 'react';
import { Link } from 'react-router-dom';
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
    const [processingFiles] = useState<ProcessingFile[]>([
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
    const [selectedFormat, setSelectedFormat] = useState<string>('all');
    const [selectedStyle, setSelectedStyle] = useState<string>('all');

    const topicClusters = {
        'Neural Networks': [
            {
                type: 'video' as const,
                title: 'Deep Learning Fundamentals',
                description: 'Comprehensive overview of neural network architectures and backpropagation...',
                tags: [
                    { type: 'format' as const, label: 'Video' },
                    { type: 'format' as const, label: 'PDF' },
                    { type: 'style' as const, label: 'Deep Dive' },
                    { type: 'topic' as const, label: 'DeepML' },
                    { type: 'topic' as const, label: 'Architecture' }
                ],
                author: 'AI Summary',
                timestamp: '2h ago',
            },
            {
                type: 'pdf' as const,
                title: 'Intro to Neural Networks',
                description: 'Foundational concepts of backpropagation and activation functions...',
                tags: [
                    { type: 'format' as const, label: 'PDF' },
                    { type: 'style' as const, label: 'Core Concept' },
                    { type: 'style' as const, label: 'Interactive' },
                    { type: 'topic' as const, label: 'AI' }
                ],
                author: 'Key Concepts',
                timestamp: '1d ago',
            },
        ],
        'History': [
            {
                type: 'video' as const,
                title: 'The Renaissance Art Movement',
                description: 'Comprehensive overview of key figures like da Vinci and Michelangelo...',
                tags: [
                    { type: 'format' as const, label: 'Video' },
                    { type: 'format' as const, label: 'Transcripts' },
                    { type: 'style' as const, label: 'Deep Dive' },
                    { type: 'topic' as const, label: 'Art' },
                    { type: 'topic' as const, label: 'History' }
                ],
                author: 'AI Summary',
                timestamp: '2h ago',
            },
            {
                type: 'audio' as const,
                title: 'World War II Timeline',
                description: 'Audio recording covering major events from 1939 to 1945...',
                tags: [
                    { type: 'format' as const, label: 'Audio' },
                    { type: 'style' as const, label: 'Timeline' },
                    { type: 'topic' as const, label: 'WWII' },
                    { type: 'topic' as const, label: 'Europe' }
                ],
                author: 'Transcript',
                timestamp: '3d ago',
            },
        ],
        'Chemistry': [
            {
                type: 'audio' as const,
                title: 'Organic Compounds List',
                description: 'Audio recording of the professor listing essential organic compounds...',
                tags: [
                    { type: 'format' as const, label: 'Audio' },
                    { type: 'format' as const, label: 'Flashcards' },
                    { type: 'style' as const, label: 'List' },
                    { type: 'topic' as const, label: 'Organic' }
                ],
                author: 'Transcript',
                timestamp: '5d ago',
            },
            {
                type: 'pdf' as const,
                title: 'Chemical Bonding Basics',
                description: 'Overview of ionic, covalent, and metallic bonds with examples...',
                tags: [
                    { type: 'format' as const, label: 'PDF' },
                    { type: 'style' as const, label: 'Core Concept' },
                    { type: 'style' as const, label: 'Quiz' },
                    { type: 'topic' as const, label: 'Bonding' }
                ],
                author: 'Key Concepts',
                timestamp: '1w ago',
            },
        ],
    };

    const allNotes = Object.values(topicClusters).flat();

    // Extract unique formats and styles
    const formats = Array.from(new Set(allNotes.flatMap(note => note.tags.filter(t => t.type === 'format').map(t => t.label))));
    const styles = Array.from(new Set(allNotes.flatMap(note => note.tags.filter(t => t.type === 'style').map(t => t.label))));

    // Filter Logic
    const filteredNotes = allNotes.filter(note => {
        let matchesTopic = true;
        if (selectedTopic !== 'all') {
            // Safe check if selectedTopic is a valid key
            matchesTopic = Object.keys(topicClusters).includes(selectedTopic)
                ? topicClusters[selectedTopic as keyof typeof topicClusters].includes(note as any)
                : false;
        }

        const matchesFormat = selectedFormat === 'all' || note.tags.some(t => t.type === 'format' && t.label === selectedFormat);

        const matchesStyle = selectedStyle === 'all' || note.tags.some(t => t.type === 'style' && t.label === selectedStyle);

        return matchesTopic && matchesFormat && matchesStyle;
    });

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

            {/* Filters Bar */}
            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm mb-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center gap-2 text-gray-700">
                        <Filter className="w-5 h-5 text-trust-blue" />
                        <span className="font-medium">Filter by:</span>
                    </div>

                    <div className="flex flex-1 flex-wrap gap-4">
                        {/* Topic Filter */}
                        <div className="relative group">
                            <select
                                value={selectedTopic}
                                onChange={(e) => setSelectedTopic(e.target.value)}
                                className="appearance-none bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg pl-3 pr-8 py-2 focus:ring-2 focus:ring-trust-blue focus:border-trust-blue transition-all cursor-pointer hover:bg-gray-100 min-w-[140px]"
                            >
                                <option value="all">All Topics</option>
                                {Object.keys(topicClusters).map(topic => (
                                    <option key={topic} value={topic}>{topic}</option>
                                ))}
                            </select>
                            <div className="absolute right-2.5 top-2.5 pointer-events-none text-gray-500">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>

                        {/* Format Filter */}
                        <div className="relative group">
                            <select
                                value={selectedFormat}
                                onChange={(e) => setSelectedFormat(e.target.value)}
                                className="appearance-none bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg pl-3 pr-8 py-2 focus:ring-2 focus:ring-trust-blue focus:border-trust-blue transition-all cursor-pointer hover:bg-gray-100 min-w-[140px]"
                            >
                                <option value="all">All Formats</option>
                                {formats.map(format => (
                                    <option key={format} value={format}>{format}</option>
                                ))}
                            </select>
                            <div className="absolute right-2.5 top-2.5 pointer-events-none text-gray-500">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>

                        {/* Style Filter */}
                        <div className="relative group">
                            <select
                                value={selectedStyle}
                                onChange={(e) => setSelectedStyle(e.target.value)}
                                className="appearance-none bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg pl-3 pr-8 py-2 focus:ring-2 focus:ring-trust-blue focus:border-trust-blue transition-all cursor-pointer hover:bg-gray-100 min-w-[140px]"
                            >
                                <option value="all">All Styles</option>
                                {styles.map(style => (
                                    <option key={style} value={style}>{style}</option>
                                ))}
                            </select>
                            <div className="absolute right-2.5 top-2.5 pointer-events-none text-gray-500">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>

                        {/* Active Filter Pills */}
                        {(selectedTopic !== 'all' || selectedFormat !== 'all' || selectedStyle !== 'all') && (
                            <button
                                onClick={() => {
                                    setSelectedTopic('all');
                                    setSelectedFormat('all');
                                    setSelectedStyle('all');
                                }}
                                className="text-sm text-red-600 hover:text-red-700 font-medium underline decoration-dotted underline-offset-4"
                            >
                                Clear Filters
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Content Area */}
            {selectedTopic === 'all' && selectedFormat === 'all' && selectedStyle === 'all' ? (
                // Default View: Topic Clusters
                <div className="space-y-10">
                    {Object.entries(topicClusters).map(([topic, notes]) => (
                        <div key={topic}>
                            <div className="flex items-center gap-3 mb-4">
                                <h2 className="text-2xl font-serif font-bold text-gray-900">{topic}</h2>
                                <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium border border-gray-200">
                                    {notes.length} resources
                                </span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {notes.map((note, index) => (
                                    <Link key={index} to={`/notes/${index + 1}`} className="block h-full">
                                        <LearningNoteCard {...note} />
                                    </Link>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                // Filtered List View
                <div>
                    <div className="flex items-center gap-3 mb-6">
                        <h2 className="text-2xl font-semibold text-gray-900">
                            {filteredNotes.length > 0 ? 'Filtered Resources' : 'No matches found'}
                        </h2>
                        <span className="px-3 py-1 bg-trust-blue/10 text-trust-blue rounded-full text-sm font-medium">
                            {filteredNotes.length} results
                        </span>
                    </div>

                    {filteredNotes.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredNotes.map((note, index) => (
                                <Link key={index} to={`/notes/${index + 1}`} className="block h-full">
                                    <LearningNoteCard {...note} />
                                </Link>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-20 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                            <Filter className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No resources found</h3>
                            <p className="text-gray-500">Try adjusting your filters to find what you're looking for.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
