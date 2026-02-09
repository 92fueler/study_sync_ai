import { useEffect, useState, useMemo } from 'react';
import { ChevronRight, ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import AudioPlayer from '../components/AudioPlayer';
import VideoPlayer from '../components/VideoPlayer';
import Mermaid from '../components/Mermaid';
import { generateVideo, getNote, getArtifact, getVideoMetadata } from '../api/client';

/** Split content into text and mermaid code blocks for rendering. */
function parseSectionContent(content: string): { type: 'text' | 'mermaid'; content: string }[] {
    const parts: { type: 'text' | 'mermaid'; content: string }[] = [];
    const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/gi;
    let lastIndex = 0;
    let match;
    while ((match = mermaidRegex.exec(content)) !== null) {
        const before = content.slice(lastIndex, match.index).trim();
        if (before) parts.push({ type: 'text', content: before });
        parts.push({ type: 'mermaid', content: match[1].trim() });
        lastIndex = match.index + match[0].length;
    }
    const after = content.slice(lastIndex).trim();
    if (after) parts.push({ type: 'text', content: after });
    if (parts.length === 0 && content.trim()) parts.push({ type: 'text', content: content.trim() });
    return parts;
}

/** Split markdown into sections by # headings. Returns [{ title, content }]. */
function parseMarkdownSections(text: string): { title: string; content: string }[] {
    if (!text?.trim()) return [{ title: 'Summary', content: 'No content available.' }];
    const sections: { title: string; content: string }[] = [];
    const headingRegex = /^(#{1,6})\s+(.+)$/gm;
    let lastTitle: string | undefined;
    let lastStart = 0;
    let match;
    while ((match = headingRegex.exec(text)) !== null) {
        const fullMatch = match[0];
        const title = match[2].trim();
        const start = match.index;
        if (lastTitle !== undefined) {
            const content = text.slice(lastStart, start).trim();
            if (content) sections.push({ title: lastTitle, content });
        }
        lastTitle = title;
        lastStart = start + fullMatch.length;
    }
    if (lastTitle !== undefined) {
        const content = text.slice(lastStart).trim();
        sections.push({ title: lastTitle, content });
    }
    if (sections.length === 0) return [{ title: 'Summary', content: text.trim() }];
    return sections;
}

type VideoGenerationStatus = 'not_requested' | 'requesting' | 'queued' | 'generating' | 'ready' | 'failed';

export default function NoteDetail() {
    const { id } = useParams<{ id: string }>();
    const [userId, setUserId] = useState('');
    const [note, setNote] = useState<any | null>(null);
    const [fullContent, setFullContent] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeSection, setActiveSection] = useState<string | null>(null);
    const [videoStatus, setVideoStatus] = useState<VideoGenerationStatus>('not_requested');
    const [videoStatusDetail, setVideoStatusDetail] = useState<string | null>(null);
    const [isRetryingVideo, setIsRetryingVideo] = useState(false);

    const formatVideoError = (message?: string | null) => {
        if (!message) return 'Generation failed';
        const lower = message.toLowerCase();
        if (lower.includes('429') || lower.includes('resource_exhausted') || lower.includes('quota')) {
            return 'Quota exceeded (429). Upgrade quota or retry later.';
        }
        return message;
    };

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
        if (!id || !userId) return;
        const loadNote = async () => {
            try {
                setLoading(true);
                setFullContent(null);
                const response = await getNote(id, userId);

                const text = `${response?.title || ''} ${response?.description || ''}`.toLowerCase();
                const requestedVideo = text.includes('video');
                if (response?.has_video) {
                    setVideoStatus('ready');
                    setVideoStatusDetail('Ready to play');
                } else if (requestedVideo && response?.artifact_id) {
                    setVideoStatus('queued');
                    setVideoStatusDetail('Request detected');
                } else if (requestedVideo) {
                    setVideoStatus('queued');
                    setVideoStatusDetail('Waiting for artifact');
                } else {
                    setVideoStatus('not_requested');
                    setVideoStatusDetail(null);
                }

                setNote(response || null);
                if (response?.artifact_id) {
                    try {
                        const artifact = await getArtifact(response.artifact_id);
                        if (artifact?.content) setFullContent(artifact.content);
                    } catch {
                        if (response?.description) setFullContent(response.description);
                    }
                } else if (response?.description) {
                    setFullContent(response.description);
                }
            } catch (error) {
                console.error('Failed to load note', error);
                setNote(null);
                setVideoStatus('failed');
                setVideoStatusDetail('Could not load note');
            } finally {
                setLoading(false);
            }
        };
        void loadNote();
    }, [id, userId]);

    useEffect(() => {
        if (!note || !userId || !note.artifact_id || note.has_video) return;
        const text = `${note.title || ''} ${note.description || ''}`.toLowerCase();
        const requestedVideo = text.includes('video');
        if (!requestedVideo) return;

        const trigger = async () => {
            try {
                setVideoStatus('requesting');
                setVideoStatusDetail('Sending request');
                await generateVideo(note.artifact_id, { user_id: userId, total_duration: 120 });
                setVideoStatus('queued');
                setVideoStatusDetail('Request accepted');
            } catch (error) {
                console.error('[NoteDetail] failed to trigger video generation', error);
                setVideoStatus('failed');
                setVideoStatusDetail('Request failed');
            }
        };

        void trigger();
    }, [note, userId]);

    const mediaArtifactId = note?.artifact_id || undefined;
    const noteRequestedVideo = Boolean(note && `${note.title || ''} ${note.description || ''}`.toLowerCase().includes('video'));

    useEffect(() => {
        if (!mediaArtifactId || !noteRequestedVideo) return;
        if (videoStatus === 'ready' || videoStatus === 'failed') return;

        let cancelled = false;
        let pollInterval: number | null = null;

        const poll = async () => {
            try {
                const metadata = await getVideoMetadata(mediaArtifactId);
                if (cancelled) return;
                const status = (metadata?.status || '').toLowerCase();
                if (status === 'ready') {
                    setVideoStatus('ready');
                    setVideoStatusDetail('Ready to play');
                    setNote((prev: any) => (prev ? { ...prev, has_video: true } : prev));
                    if (pollInterval) window.clearInterval(pollInterval);
                    return;
                }
                if (status === 'failed') {
                    setVideoStatus('failed');
                    setVideoStatusDetail(formatVideoError(metadata?.error_message));
                    if (pollInterval) window.clearInterval(pollInterval);
                    return;
                }
                if (status === 'generating') {
                    setVideoStatus('generating');
                    const progress = typeof metadata?.progress === 'number' ? `${metadata.progress}%` : null;
                    const seg = metadata?.current_segment && metadata?.total_segments
                        ? `Segment ${metadata.current_segment}/${metadata.total_segments}`
                        : null;
                    setVideoStatusDetail([progress, seg].filter(Boolean).join(' • ') || 'Generating');
                    return;
                }
                setVideoStatus('queued');
                setVideoStatusDetail('Queued');
            } catch (error: any) {
                const statusCode = error?.response?.status;
                if (statusCode === 404) {
                    setVideoStatus((prev) => (prev === 'requesting' ? prev : 'queued'));
                    setVideoStatusDetail('Waiting for worker');
                    return;
                }
                console.error('[NoteDetail] failed polling video metadata', error);
                const detail = error?.response?.data?.detail;
                if (typeof detail === 'string') {
                    setVideoStatusDetail(formatVideoError(detail));
                }
            }
        };

        void poll();
        pollInterval = window.setInterval(() => {
            void poll();
        }, 5000);

        return () => {
            cancelled = true;
            if (pollInterval) {
                window.clearInterval(pollInterval);
            }
        };
    }, [mediaArtifactId, noteRequestedVideo, videoStatus]);

    const videoStatusLabel = (() => {
        switch (videoStatus) {
            case 'requesting':
                return 'Video: Requesting';
            case 'queued':
                return 'Video: Queued';
            case 'generating':
                return 'Video: Generating';
            case 'ready':
                return 'Video: Ready';
            case 'failed':
                return 'Video: Failed';
            default:
                return 'Video: Not Requested';
        }
    })();

    const videoStatusClass = (() => {
        switch (videoStatus) {
            case 'requesting':
            case 'queued':
                return 'bg-yellow-100 text-yellow-800';
            case 'generating':
                return 'bg-blue-100 text-blue-800';
            case 'ready':
                return 'bg-green-100 text-green-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-700';
        }
    })();

    const handleRetryVideo = async () => {
        if (!note?.artifact_id || !userId || isRetryingVideo) return;
        try {
            setIsRetryingVideo(true);
            setVideoStatus('requesting');
            setVideoStatusDetail('Retrying request');
            await generateVideo(
                note.artifact_id,
                { user_id: userId, total_duration: 120 },
                { retry: true }
            );
            setVideoStatus('queued');
            setVideoStatusDetail('Retry accepted');
            setNote((prev: any) => (prev ? { ...prev, has_video: false } : prev));
        } catch (error: any) {
            console.error('[NoteDetail] retry video failed', error);
            setVideoStatus('failed');
            const detail = error?.response?.data?.detail;
            setVideoStatusDetail(formatVideoError(typeof detail === 'string' ? detail : 'Retry failed'));
        } finally {
            setIsRetryingVideo(false);
        }
    };

    const sections = useMemo(() => parseMarkdownSections(fullContent ?? note?.description ?? ''), [fullContent, note?.description]);

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto px-6 py-8">
                <div className="text-gray-500">Loading note...</div>
            </div>
        );
    }

    if (!note) {
        return (
            <div className="max-w-7xl mx-auto px-6 py-8">
                <div className="text-gray-500">Note not found.</div>
            </div>
        );
    }

    const tags = Array.isArray(note.tags) ? note.tags : [];
    const createdAt = note.created_at ? new Date(note.created_at).toLocaleDateString() : '';

    return (
        <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="mb-8">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                    <Link to="/" className="hover:text-trust-blue transition-colors flex items-center gap-1">
                        <ArrowLeft className="w-3 h-3" /> Knowledge Bank
                    </Link>
                    <ChevronRight className="w-3 h-3" />
                    <span>{note.title || 'Note'}</span>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <span className="px-2 py-0.5 bg-blue-100 text-trust-blue text-xs font-bold uppercase tracking-wider rounded">Note</span>
                            {createdAt && <span className="text-sm text-gray-500">{createdAt}</span>}
                        </div>
                        <h1 className="text-4xl font-serif font-bold text-gray-900 mb-2">
                            {note.title || 'Untitled Note'}
                        </h1>
                        <p className="text-lg text-gray-600">
                            {note.description || 'No description provided.'}
                        </p>
                        <div className="mt-3 flex items-center gap-2">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${videoStatusClass}`}>
                                {videoStatusLabel}
                            </span>
                            {videoStatusDetail && (
                                <span className="text-xs text-gray-500">{videoStatusDetail}</span>
                            )}
                            {videoStatus === 'failed' && mediaArtifactId && (
                                <button
                                    className="px-3 py-1 rounded text-xs font-semibold bg-red-100 text-red-700 hover:bg-red-200 transition-colors disabled:opacity-60"
                                    onClick={handleRetryVideo}
                                    disabled={isRetryingVideo}
                                >
                                    {isRetryingVideo ? 'Retrying...' : 'Retry Video'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                <div className="lg:col-span-8">
                    <div className="space-y-12">
                        {sections.map((sec, index) => {
                            const sectionId = `section-${index}`;
                            const isActive = activeSection === sectionId || (activeSection === null && index === 0);
                            return (
                                <section
                                    key={sectionId}
                                    id={sectionId}
                                    onClick={() => setActiveSection(sectionId)}
                                    className={`transition-colors p-4 -m-4 rounded-xl ${isActive ? 'bg-blue-50/50' : ''}`}
                                >
                                    <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-3 cursor-pointer group">
                                        <span className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-colors ${isActive ? 'bg-trust-blue text-white' : 'bg-gray-100 text-gray-600'}`}>
                                            {index + 1}
                                        </span>
                                        {sec.title}
                                    </h2>
                                    <div className="prose prose-lg text-gray-600 max-w-none">
                                        {sec.content.trim() ? (
                                            parseSectionContent(sec.content).map((part, i) =>
                                                part.type === 'mermaid' ? (
                                                    <div key={`${sectionId}-mermaid-${i}`} className="my-6 flex justify-center overflow-x-auto">
                                                        <Mermaid chart={part.content} />
                                                    </div>
                                                ) : (
                                                    <div key={`${sectionId}-text-${i}`} className="note-markdown">
                                                        <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-lg text-gray-600 max-w-none prose-headings:text-gray-900 prose-strong:text-gray-900 prose-p:leading-relaxed prose-ul:my-4 prose-ol:my-4">
                                                            {part.content}
                                                        </ReactMarkdown>
                                                    </div>
                                                )
                                            )
                                        ) : (
                                            <p className="mb-6 leading-relaxed text-gray-500 italic">No content in this section.</p>
                                        )}
                                    </div>
                                </section>
                            );
                        })}
                        {tags.length > 0 && (
                            <div className="flex flex-wrap gap-2 text-sm text-gray-500 pt-4">
                                {tags.map((tag: any, index: number) => (
                                    <span key={`${tag.label}-${index}`} className="px-3 py-1 bg-gray-100 rounded-full">
                                        {tag.label}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="lg:col-span-4 space-y-6">
                    {/* Audio: right sidebar, first block (above Quick Note) */}
                    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3 flex items-center gap-2">
                            Audio
                        </h3>
                        {note.has_audio ? (
                            <AudioPlayer
                                title={note.title || 'Learning Audio'}
                                artifactId={note.artifact_id || note.id}
                            />
                        ) : (
                            <div className="text-sm text-gray-500 space-y-1">
                                <p>No audio available for this note.</p>
                                <p className="text-xs text-gray-400 mt-2">
                                    To get audio: enable <strong>Audio</strong> in My DNA, then upload new files. Notes from that upload will get an audio version (may take a few minutes).
                                </p>
                            </div>
                        )}
                    </div>
                    {(note.has_video || noteRequestedVideo) && (
                        <VideoPlayer
                            title={`${note.title || 'Learning'} - Video`}
                            artifactId={mediaArtifactId}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
