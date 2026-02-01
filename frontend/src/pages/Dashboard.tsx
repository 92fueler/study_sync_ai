import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Link as LinkIcon, FileUp, Paperclip, Mic, Sparkles, ArrowRight } from 'lucide-react';
import LearningPlanCard from '../components/LearningPlanCard';
import LearningNoteCard from '../components/LearningNoteCard';
import {
    createIngestionJob,
    createNote,
    listLearningPlans,
    listRecentNotes,
    uploadFiles,
} from '../api/client';

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState('raw-notes');
    const [userId, setUserId] = useState('');
    const [inputText, setInputText] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [recentNotes, setRecentNotes] = useState<any[]>([]);
    const [activePlans, setActivePlans] = useState<any[]>([]);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const audioInputRef = useRef<HTMLInputElement>(null);
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

    const loadData = async (resolvedUserId: string) => {
        try {
            const [notesResponse, plansResponse] = await Promise.all([
                listRecentNotes(resolvedUserId, 6),
                listLearningPlans(resolvedUserId, { limit: 3 }),
            ]);
            setRecentNotes(notesResponse.items || []);
            setActivePlans(plansResponse.items || []);
        } catch (error) {
            console.error('Failed to load dashboard data', error);
        }
    };

    useEffect(() => {
        if (!userId) return;
        void loadData(userId);
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
        return {
            id: note.id || note.note_id || note.uuid || null,
            type: typeMap[note.note_type] || 'pdf',
            title: note.title || 'Untitled Note',
            description: note.description || 'No description provided.',
            tags,
            author: note.author || 'AI Summary',
            timestamp: formatTimestamp(note.created_at),
            thumbnail: note.thumbnail_url || undefined,
        };
    };

    const normalizePlan = (plan: any) => {
        const statusMap: Record<string, 'active' | 'paused' | 'completed'> = {
            active: 'active',
            paused: 'paused',
            completed: 'completed',
        };
        return {
            id: plan.id,
            status: statusMap[plan.status] || 'active',
            category: plan.category || 'TECH',
            categoryColor: plan.category_color || 'blue',
            title: plan.title || 'Untitled Plan',
            goal: plan.goal || undefined,
            difficulty: plan.difficulty || 'Intermediate',
            percentage: plan.progress_percent ?? 0,
            module: plan.details?.current_module || plan.details?.module || undefined,
            timeRemaining: plan.estimated_time || undefined,
            totalModules: plan.total_modules || plan.module_count || 0,
            completedModules: plan.completed_modules || 0,
            nextSession: plan.next_session_at
                ? new Date(plan.next_session_at).toLocaleString()
                : undefined,
        };
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleAudioClick = () => {
        audioInputRef.current?.click();
    };

    const handleFilesSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files ? Array.from(event.target.files) : [];
        if (!files.length || !userId) return;
        try {
            const response = await uploadFiles(userId, files);
            if (response?.results) {
                await Promise.all(
                    response.results.map((item: any) => {
                        const ext = (item.filename || '').split('.').pop()?.toLowerCase();
                        const jobType = ['pdf', 'mp3', 'wav', 'mp4'].includes(ext || '') ? ext : 'text';
                        return createIngestionJob({
                            user_id: userId,
                            name: item.filename || 'Upload',
                            job_type: jobType,
                            status: 'ingesting',
                            progress: 0,
                            metadata: { source: 'upload', task_id: item.task_id, content_id: item.content_id },
                        });
                    })
                );
            }
            showStatus('Files uploaded successfully.');
            await loadData(userId);
        } catch (error) {
            console.error('Upload failed', error);
            showStatus('Upload failed. Please try again.');
        }
        event.target.value = '';
    };

    const handleAudioSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files ? Array.from(event.target.files) : [];
        if (!files.length || !userId) return;
        try {
            const response = await uploadFiles(userId, files);
            if (response?.results) {
                await Promise.all(
                    response.results.map((item: any) => createIngestionJob({
                        user_id: userId,
                        name: item.filename || 'Audio Upload',
                        job_type: 'audio',
                        status: 'ingesting',
                        progress: 0,
                        metadata: { source: 'audio-upload', task_id: item.task_id, content_id: item.content_id },
                    }))
                );
            }
            showStatus('Audio uploaded successfully.');
            await loadData(userId);
        } catch (error) {
            console.error('Audio upload failed', error);
            showStatus('Audio upload failed. Please try again.');
        }
        event.target.value = '';
    };

    const handleGenerateStructure = async () => {
        if (!inputText.trim() || !userId) return;
        setIsSubmitting(true);
        try {
            const ingestion = await createIngestionJob({
                user_id: userId,
                name: 'Dashboard input',
                job_type: activeTab === 'url-input' ? 'url' : 'text',
                status: 'ingesting',
                progress: 0,
                metadata: { source: 'dashboard', input: inputText.slice(0, 500) },
            });
            const note = await createNote({
                user_id: userId,
                note_type: activeTab === 'url-input' ? 'url' : 'text',
                title: inputText.split('\n')[0]?.slice(0, 64) || 'New Note',
                description: inputText.slice(0, 160),
                tags: [
                    { type: 'format', label: activeTab === 'url-input' ? 'URL' : 'Notes' },
                    { type: 'topic', label: 'Dashboard' },
                ],
                author: 'AI Summary',
            });
            if (note) {
                await loadData(userId);
            }
            if (ingestion) {
                console.log('Ingestion job created', ingestion);
            }
            showStatus('Saved. Generating structure now.');
            setInputText('');
        } catch (error) {
            console.error('Generate structure failed', error);
            showStatus('Save failed. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

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

                    {statusMessage && (
                        <div className="mb-3 rounded-md bg-blue-50 text-blue-700 text-sm px-3 py-2">
                            {statusMessage}
                        </div>
                    )}

                    <textarea
                        className="w-full h-32 p-4 text-gray-600 placeholder-gray-400 resize-none focus:outline-none"
                        placeholder="Paste a lecture URL, drag & drop a PDF, or start typing your chaotic thoughts here..."
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                    />

                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                        <div className="flex items-center gap-3">
                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                className="hidden"
                                onChange={handleFilesSelected}
                            />
                            <input
                                ref={audioInputRef}
                                type="file"
                                accept="audio/*"
                                className="hidden"
                                onChange={handleAudioSelected}
                            />
                            <button
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                onClick={handleUploadClick}
                                aria-label="Attach files"
                            >
                                <Paperclip className="w-5 h-5 text-gray-400" />
                            </button>
                            <button
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                onClick={handleAudioClick}
                                aria-label="Upload audio"
                            >
                                <Mic className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        <button
                            className="flex items-center gap-2 px-6 py-2.5 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-60"
                            onClick={handleGenerateStructure}
                            disabled={isSubmitting || !inputText.trim()}
                        >
                            <Sparkles className="w-4 h-4" />
                            {isSubmitting ? 'Generating...' : 'Generate Structure'}
                        </button>
                    </div>
                </div>
            </div>

            <div className="mb-12">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900">Active Learning Plans</h2>
                    <Link
                        to="/plan"
                        className="flex items-center gap-1 text-sm font-medium text-trust-blue hover:text-blue-700 transition-colors"
                    >
                        View All
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                </div>

                {activePlans.length === 0 ? (
                    <div className="text-sm text-gray-500">No active plans yet.</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {activePlans.map(normalizePlan).map((plan, index) => {
                            const planId = (plan as { id?: string }).id;
                            return (
                                <Link key={planId || index} to={`/plans/${planId || index + 1}`}>
                                    <LearningPlanCard {...plan} />
                                </Link>
                            );
                        })}
                    </div>
                )}
            </div>

            <div className="mb-8">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900">Recent Learning Notes</h2>
                    <Link
                        to="/bank"
                        className="flex items-center gap-1 text-sm font-medium text-trust-blue hover:text-blue-700 transition-colors"
                    >
                        View All
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                </div>

                {recentNotes.length === 0 ? (
                    <div className="text-sm text-gray-500">No notes yet.</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {recentNotes.map(normalizeNote).map((note, index) => (
                            <Link key={`${note.id ?? note.title}-${index}`} to={`/notes/${note.id ?? index + 1}`} className="block">
                                <LearningNoteCard {...note} />
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
