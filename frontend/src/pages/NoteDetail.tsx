import { useEffect, useState } from 'react';
import { ChevronRight, ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import AudioPlayer from '../components/AudioPlayer';
import VideoPlayer from '../components/VideoPlayer';
import QuickNotes from '../components/QuickNotes';
import ProgressRoadmap from '../components/ProgressRoadmap';
import { generateVideo, getNote, getVideoMetadata } from '../api/client';

type VideoGenerationStatus = 'not_requested' | 'requesting' | 'queued' | 'generating' | 'ready' | 'failed';

export default function NoteDetail() {
    const { id } = useParams<{ id: string }>();
    const [userId, setUserId] = useState('');
    const [note, setNote] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeSection, setActiveSection] = useState('summary');
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
                const response = await getNote(id, userId);
                console.log('[NoteDetail] loaded note', {
                    id: response?.id,
                    artifact_id: response?.artifact_id,
                    has_video: response?.has_video,
                    has_audio: response?.has_audio,
                    source_id: response?.source_id,
                });
                const text = `${response?.title || ''} ${response?.description || ''}`.toLowerCase();
                const requestedVideo = text.includes('video') || Boolean(response?.has_video);
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
                    setVideoStatusDetail('No video requested');
                }
                setNote(response || null);
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
                console.log('[NoteDetail] triggering video generation', {
                    note_id: note.id,
                    artifact_id: note.artifact_id,
                    user_id: userId,
                });
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
    const noteText = `${note?.title || ''} ${note?.description || ''}`.toLowerCase();
    const noteRequestedVideo = Boolean(note && (noteText.includes('video') || note.has_video));
    const noteRequestedAudio = Boolean(
        note && (noteText.includes('audio') || note.has_audio || String(note.note_type || '').toLowerCase() === 'audio')
    );

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
                // Metadata 404 during early pipeline is expected.
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
                return 'Video: No Video Requested';
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

    const audioStatusLabel = note?.has_audio
        ? 'Audio: Ready'
        : noteRequestedAudio
            ? 'Audio: Requested'
            : 'Audio: No Audio Requested';

    const audioStatusClass = note?.has_audio
        ? 'bg-green-100 text-green-800'
        : noteRequestedAudio
            ? 'bg-yellow-100 text-yellow-800'
            : 'bg-gray-100 text-gray-700';

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
    const roadmap = Array.isArray(note.roadmap)
        ? note.roadmap
        : Array.isArray(note.details?.roadmap)
            ? note.details.roadmap
            : Array.isArray(note.sections)
                ? note.sections
                : [];
    const milestones = roadmap.map((step: any, index: number) => ({
        id: step.id || String(index + 1),
        title: step.title || step.topic || `Step ${index + 1}`,
        isCompleted: Boolean(step.isCompleted || step.status === 'done' || step.completed),
        isActive: Boolean(step.isActive || step.status === 'active'),
    }));

    return (
        <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="mb-8">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                    <Link to="/" className="hover:text-trust-blue transition-colors flex items-center gap-1">
                        <ArrowLeft className="w-3 h-3" /> Dashboard
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
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${audioStatusClass}`}>
                                {audioStatusLabel}
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
                        <section
                            onClick={() => setActiveSection('summary')}
                            className={`transition-colors p-4 -m-4 rounded-xl ${activeSection === 'summary' ? 'bg-blue-50/50' : ''}`}
                        >
                            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-3 cursor-pointer group">
                                <span className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-colors ${activeSection === 'summary' ? 'bg-trust-blue text-white' : 'bg-gray-100 text-gray-600'}`}>1</span>
                                Summary
                            </h2>
                            <div className="prose prose-lg text-gray-600 max-w-none">
                                <p className="mb-6 leading-relaxed">
                                    {note.description || 'No summary available.'}
                                </p>
                            </div>

                            {tags.length > 0 && (
                                <div className="flex flex-wrap gap-2 text-sm text-gray-500">
                                    {tags.map((tag: any, index: number) => (
                                        <span key={`${tag.label}-${index}`} className="px-3 py-1 bg-gray-100 rounded-full">
                                            {tag.label}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </section>
                    </div>
                </div>

                <div className="lg:col-span-4 space-y-6">
                    <AudioPlayer
                        title={note.title || 'Learning Audio'}
                        subtitle={note.description}
                        artifactId={mediaArtifactId}
                        requested={noteRequestedAudio}
                    />
                    <VideoPlayer
                        title={`${note.title || 'Learning'} - Video`}
                        artifactId={mediaArtifactId}
                        requested={noteRequestedVideo}
                    />
                    <QuickNotes
                        activeSection={activeSection}
                        onSectionChange={setActiveSection}
                        userId={userId}
                        sourceId={note.id}
                        sourceTitle={note.title}
                    />
                    <ProgressRoadmap milestones={milestones} />
                </div>
            </div>
        </div>
    );
}
