import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Upload, FileText, Video, Headphones, Link as LinkIcon, Filter } from 'lucide-react';
import LearningNoteCard from '../components/LearningNoteCard';
import { createIngestionJob, listArtifacts, listNotes, listNoteTopics, uploadFiles } from '../api/client';

type NoteTag = {
    type: 'format' | 'style' | 'topic';
    label: string;
};

export default function KnowledgeBank() {
    const [userId, setUserId] = useState('');
    const [notesData, setNotesData] = useState<any[]>([]);
    const [topicCounts, setTopicCounts] = useState<Record<string, number>>({});
    const [selectedTopic, setSelectedTopic] = useState<string>('all');
    const [selectedFormat, setSelectedFormat] = useState<string>('all');
    const [selectedStyle, setSelectedStyle] = useState<string>('all');
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [materials, setMaterials] = useState<any[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const messageTimerRef = useRef<number | null>(null);

    useEffect(() => {
        const storedUserId = localStorage.getItem('user_id');
        if (storedUserId) {
            setUserId(storedUserId);
            return;
        }
        const tempUserId = `user_${Date.now()}`;
        localStorage.setItem('user_id', tempUserId);
        setUserId(tempUserId);
    }, []);

    useEffect(() => {
        return () => {
            if (messageTimerRef.current) {
                window.clearTimeout(messageTimerRef.current);
            }
        };
    }, []);

    const showStatus = (message: string) => {
        setStatusMessage(message);
        if (messageTimerRef.current) {
            window.clearTimeout(messageTimerRef.current);
        }
        messageTimerRef.current = window.setTimeout(() => {
            setStatusMessage(null);
        }, 3000);
    };

    const loadNotes = async (resolvedUserId: string) => {
        try {
            const [notesResponse, topicsResponse, materialsResponse] = await Promise.all([
                listNotes(resolvedUserId, { limit: 60 }),
                listNoteTopics(resolvedUserId),
                listArtifacts(resolvedUserId),
            ]);
            setNotesData(notesResponse.items || []);
            const topicMap: Record<string, number> = {};
            (topicsResponse.items || []).forEach((topic: any) => {
                if (topic.topic) topicMap[topic.topic] = topic.count || 0;
            });
            setTopicCounts(topicMap);
            setMaterials(materialsResponse.items || []);
        } catch (error) {
            console.error('Failed to load knowledge bank', error);
        }
    };

    useEffect(() => {
        if (!userId) return;
        void loadNotes(userId);
    }, [userId]);

    const formatTimestamp = (value?: string | null) => {
        if (!value) return 'just now';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return 'just now';
        const diffMs = Date.now() - date.getTime();
        const diffMinutes = Math.floor(diffMs / 60000);
        if (diffMinutes < 60) return `${Math.max(diffMinutes, 1)}m ago`;
        const diffHours = Math.floor(diffMinutes / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    };

    const normalizeNote = (note: any) => {
        const rawTags = Array.isArray(note.tags) ? note.tags : [];
        const tags = rawTags.length
            ? rawTags
            : [
                { type: 'format', label: (note.note_type || 'Notes').toString().toUpperCase() },
                ...(note.topic ? [{ type: 'topic', label: note.topic }] : []),
            ];
        const typeMap: Record<string, 'pdf' | 'video' | 'audio' | 'image'> = {
            pdf: 'pdf',
            video: 'video',
            audio: 'audio',
            image: 'image',
            url: 'pdf',
            text: 'pdf',
        };
        const noteId = note.id || note.note_id || note.uuid || null;
        return {
            id: noteId,
            type: typeMap[note.note_type] || 'pdf',
            title: note.title || 'Untitled Note',
            description: note.description || 'No description provided.',
            tags,
            author: note.author || 'AI Summary',
            timestamp: formatTimestamp(note.created_at),
            thumbnail: note.thumbnail_url || undefined,
            topic: note.topic || 'Uncategorized',
        };
    };

    const apiNotes = notesData.map(normalizeNote);
    const clusters = apiNotes.reduce<Record<string, typeof apiNotes>>((acc, note: any) => {
        const topic = note.topic || 'Uncategorized';
        if (!acc[topic]) acc[topic] = [];
        acc[topic].push(note);
        return acc;
    }, {});

    const allNotes = apiNotes;

    const formats = Array.from(new Set(allNotes.flatMap((note: { tags: NoteTag[] }) =>
        note.tags.filter((t: NoteTag) => t.type === 'format').map((t: NoteTag) => t.label)
    )));
    const styles = Array.from(new Set(allNotes.flatMap((note: { tags: NoteTag[] }) =>
        note.tags.filter((t: NoteTag) => t.type === 'style').map((t: NoteTag) => t.label)
    )));

    const filteredNotes = allNotes.filter(note => {
        let matchesTopic = true;
        if (selectedTopic !== 'all') {
            matchesTopic = Object.keys(clusters).includes(selectedTopic)
                ? clusters[selectedTopic as keyof typeof clusters].includes(note as any)
                : false;
        }

        const matchesFormat = selectedFormat === 'all'
            || (note.tags as NoteTag[]).some((t: NoteTag) => t.type === 'format' && t.label === selectedFormat);

        const matchesStyle = selectedStyle === 'all'
            || (note.tags as NoteTag[]).some((t: NoteTag) => t.type === 'style' && t.label === selectedStyle);

        return matchesTopic && matchesFormat && matchesStyle;
    });

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

            <div className="mb-10">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-semibold text-gray-900">Generated Materials</h2>
                    <span className="text-sm text-gray-500">AI-generated summaries and notes</span>
                </div>
                {materials.length === 0 ? (
                    <div className="text-sm text-gray-500">No generated materials yet.</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
                        {materials.slice(0, 6).map((artifact: any) => (
                            <Link key={artifact.id} to={`/materials/${artifact.id}`} className="block">
                                <LearningNoteCard
                                    type="pdf"
                                    title={artifact.title || `Material (${artifact.artifact_type})`}
                                    description={`Generated on ${new Date(artifact.created_at).toLocaleDateString()}`}
                                    tags={[{ type: 'format', label: 'AI MATERIAL' }]}
                                    author="AI"
                                    timestamp={new Date(artifact.created_at).toLocaleTimeString()}
                                />
                            </Link>
                        ))}
                    </div>
                )}
            </div>

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
                        {statusMessage && (
                            <div className="mb-4 rounded-md bg-blue-50 text-blue-700 text-sm px-3 py-2 inline-block">
                                {statusMessage}
                            </div>
                        )}
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
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            className="hidden"
                            onChange={async (event) => {
                                const files = event.target.files ? Array.from(event.target.files) : [];
                                if (!files.length || !userId) return;
                                try {
                                    const response = await uploadFiles(userId, files);
                                    if (response?.results) {
                                        await Promise.all(
                                            response.results.map((item: any) => createIngestionJob({
                                                user_id: userId,
                                                name: item.filename || 'Upload',
                                                job_type: 'pdf',
                                                status: 'ingesting',
                                                progress: 0,
                                                metadata: { source: 'knowledge-bank', task_id: item.task_id, content_id: item.content_id },
                                            }))
                                        );
                                    }
                                    showStatus('Files uploaded successfully.');
                                    await loadNotes(userId);
                                } catch (error) {
                                    console.error('Knowledge bank upload failed', error);
                                    showStatus('Upload failed. Please try again.');
                                } finally {
                                    event.target.value = '';
                                }
                            }}
                        />
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                        >
                            Browse Files
                        </button>
                    </div>
                </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm mb-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center gap-2 text-gray-700">
                        <Filter className="w-5 h-5 text-trust-blue" />
                        <span className="font-medium">Filter by:</span>
                    </div>

                    <div className="flex flex-1 flex-wrap gap-4">
                        <div className="relative group">
                            <select
                                value={selectedTopic}
                                onChange={(e) => setSelectedTopic(e.target.value)}
                                className="appearance-none bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg pl-3 pr-8 py-2 focus:ring-2 focus:ring-trust-blue focus:border-trust-blue transition-all cursor-pointer hover:bg-gray-100 min-w-[140px]"
                            >
                                <option value="all">All Topics</option>
                                {Object.keys(clusters).map(topic => (
                                    <option key={topic} value={topic}>{topic}</option>
                                ))}
                            </select>
                            <div className="absolute right-2.5 top-2.5 pointer-events-none text-gray-500">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>

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

            {allNotes.length === 0 ? (
                <div className="text-center py-20 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                    <Filter className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No resources yet</h3>
                    <p className="text-gray-500">Upload files to start building your knowledge bank.</p>
                </div>
            ) : selectedTopic === 'all' && selectedFormat === 'all' && selectedStyle === 'all' ? (
                <div className="space-y-10">
                    {Object.entries(clusters).map(([topic, notes]) => (
                        <div key={topic}>
                            <div className="flex items-center gap-3 mb-4">
                                <h2 className="text-2xl font-serif font-bold text-gray-900">{topic}</h2>
                                <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium border border-gray-200">
                                    {topicCounts[topic] || notes.length} resources
                                </span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {notes.map((note, index) => (
                                    <Link
                                        key={note.id ?? index}
                                        to={`/notes/${note.id ?? index + 1}`}
                                        className="block h-full"
                                    >
                                        <LearningNoteCard {...note} />
                                    </Link>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
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
                                <Link
                                    key={note.id ?? index}
                                    to={`/notes/${note.id ?? index + 1}`}
                                    className="block h-full"
                                >
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
