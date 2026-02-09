import { useEffect, useState } from 'react';
import { ChevronRight, ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import AudioPlayer from '../components/AudioPlayer';
import VideoPlayer from '../components/VideoPlayer';
import QuickNotes from '../components/QuickNotes';
import ProgressRoadmap from '../components/ProgressRoadmap';
import { getNote } from '../api/client';

export default function NoteDetail() {
    const { id } = useParams<{ id: string }>();
    const [userId, setUserId] = useState('');
    const [note, setNote] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeSection, setActiveSection] = useState('summary');

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
                setNote(response || null);
            } catch (error) {
                console.error('Failed to load note', error);
                setNote(null);
            } finally {
                setLoading(false);
            }
        };
        void loadNote();
    }, [id, userId]);

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
                    {note.has_audio && (
                        <AudioPlayer
                            title={note.title || 'Learning Audio'}
                            subtitle={note.description}
                            artifactId={note.artifact_id || note.id}
                        />
                    )}
                    {note.has_video && (
                        <VideoPlayer
                            title={`${note.title || 'Learning'} - Video`}
                            artifactId={note.artifact_id || note.id}
                        />
                    )}
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
