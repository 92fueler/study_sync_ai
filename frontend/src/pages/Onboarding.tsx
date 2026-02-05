import { useEffect, useState } from 'react';
import { Check, Headphones, Video, FileText, Image as ImageIcon, HelpCircle, Lightbulb, Share2, MonitorPlay } from 'lucide-react';
import ProfilePreview from '../components/ProfilePreview';
import { getSettings, updateSettings } from '../api/client';

export default function Onboarding() {
    const [selectedFormats, setSelectedFormats] = useState<string[]>(['audio', 'notes']);
    const [selectedPreferences, setSelectedPreferences] = useState<string[]>(['quizzes', 'analogies']);
    const [customStyle, setCustomStyle] = useState('');
    const [cognitiveTone, setCognitiveTone] = useState('textbook');
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<string | null>(null);
    const [userId, setUserId] = useState('');

    const loadSettings = async (resolvedUserId: string) => {
        try {
            const response = await getSettings(resolvedUserId);
            const prefs = response?.study_preferences;
            if (!prefs) return;

            if (Array.isArray(prefs.formats)) {
                setSelectedFormats(prefs.formats);
            }
            if (Array.isArray(prefs.preferences)) {
                setSelectedPreferences(prefs.preferences);
            }
            if (typeof prefs.custom_style === 'string') {
                setCustomStyle(prefs.custom_style);
            }
            if (typeof prefs.cognitive_tone === 'string') {
                setCognitiveTone(prefs.cognitive_tone);
            }
            if (typeof response?.updated_at === 'string') {
                setSaveMessage(`Last saved: ${new Date(response.updated_at).toLocaleString()}`);
            }
        } catch (error) {
            console.error('Failed to load DNA settings', error);
        }
    };

    const resolveUserId = () => {
        const storedUserId = localStorage.getItem('user_id');
        const resolved = storedUserId || `user_${Date.now()}`;
        if (!storedUserId) {
            localStorage.setItem('user_id', resolved);
        }
        return resolved;
    };

    useEffect(() => {
        const resolved = resolveUserId();
        setUserId(resolved);
        void loadSettings(resolved);
    }, []);

    useEffect(() => {
        if (!userId) return;
        const handler = () => {
            void loadSettings(userId);
        };
        window.addEventListener('notifications:ready', handler);
        return () => {
            window.removeEventListener('notifications:ready', handler);
        };
    }, [userId]);

    const toggleFormat = (format: string) => {
        setSelectedFormats(prev =>
            prev.includes(format)
                ? prev.filter(f => f !== format)
                : [...prev, format]
        );
    };

    const togglePreference = (pref: string) => {
        setSelectedPreferences(prev =>
            prev.includes(pref)
                ? prev.filter(p => p !== pref)
                : [...prev, pref]
        );
    };

    return (
        <div className="max-w-7xl mx-auto px-6 py-12">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                    <div className="mb-2">
                        <span className="inline-block px-3 py-1 bg-blue-50 text-trust-blue text-xs font-semibold rounded mb-4">
                            PERSONALIZATION
                        </span>
                    </div>

                    <h1 className="text-4xl font-serif font-bold text-gray-900 mb-3">
                        Learning DNA
                    </h1>
                    <p className="text-gray-600 mb-8">
                        Configure your personalized AI learning experience. Decouple format from style to create your perfect study mix.
                    </p>

                    {/* Preferred Content Formats */}
                    <div className="mb-10">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-semibold text-gray-900">Preferred Content Formats</h2>
                            <span className="text-sm text-gray-500">Select supported media types</span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {[
                                { id: 'audio', label: 'Audio', icon: Headphones, desc: 'Listening' },
                                { id: 'video', label: 'Video', icon: Video, desc: 'Watching' },
                                { id: 'notes', label: 'Notes', icon: FileText, desc: 'Reading' },
                                { id: 'image', label: 'Image', icon: ImageIcon, desc: 'Visuals' },
                            ].map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => toggleFormat(item.id)}
                                    className={`relative p-4 rounded-xl border-2 transition-all text-center flex flex-col items-center gap-2 ${selectedFormats.includes(item.id)
                                        ? 'border-trust-blue bg-blue-50'
                                        : 'border-gray-200 bg-white hover:border-gray-300'
                                        }`}
                                >
                                    {selectedFormats.includes(item.id) && (
                                        <div className="absolute top-2 right-2 w-5 h-5 bg-trust-blue rounded-full flex items-center justify-center">
                                            <Check className="w-3 h-3 text-white" />
                                        </div>
                                    )}
                                    <div className={`p-3 rounded-full ${selectedFormats.includes(item.id) ? 'bg-blue-100 text-trust-blue' : 'bg-gray-100 text-gray-500'}`}>
                                        <item.icon className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 text-sm">{item.label}</h3>
                                        <p className="text-xs text-gray-500">{item.desc}</p>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Learning Style Preferences */}
                    <div className="mb-10">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-semibold text-gray-900">Learning Style Preferences</h2>
                            <span className="text-sm text-gray-500">How do you learn best?</span>
                        </div>

                        <div className="flex flex-wrap gap-3 mb-6">
                            {[
                                { id: 'quizzes', label: 'Quizzes', icon: HelpCircle },
                                { id: 'analogies', label: 'Analogies', icon: Lightbulb },
                                { id: 'knowledge_graph', label: 'Knowledge Graph', icon: Share2 },
                                { id: 'lecture', label: 'Lecture Style', icon: MonitorPlay },
                            ].map((pref) => (
                                <button
                                    key={pref.id}
                                    onClick={() => togglePreference(pref.id)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all text-sm font-medium ${selectedPreferences.includes(pref.id)
                                        ? 'bg-trust-blue text-white border-trust-blue shadow-sm'
                                        : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                        }`}
                                >
                                    <pref.icon className="w-4 h-4" />
                                    {pref.label}
                                </button>
                            ))}
                        </div>

                        {/* Custom Style Input */}
                        <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Describe your preferred style (1 sentence)
                            </label>
                            <input
                                type="text"
                                value={customStyle}
                                onChange={(e) => setCustomStyle(e.target.value)}
                                placeholder="e.g., 'I prefer detailed historical context with modern-day comparisons.'"
                                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-trust-blue focus:border-trust-blue outline-none transition-shadow"
                            />
                        </div>
                    </div>

                    <div className="mb-8">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Cognitive Tone</h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                            <button
                                onClick={() => setCognitiveTone('textbook')}
                                className={`px-4 py-3 rounded-lg font-medium transition-all text-left ${cognitiveTone === 'textbook'
                                    ? 'bg-trust-blue text-white shadow-md'
                                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                                    }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xl">🎓</span>
                                    <span className="font-semibold">Textbook</span>
                                </div>
                                <p className={`text-xs ${cognitiveTone === 'textbook' ? 'text-blue-100' : 'text-gray-500'}`}>
                                    Authoritative, dense, precise
                                </p>
                            </button>
                            <button
                                onClick={() => setCognitiveTone('coaching')}
                                className={`px-4 py-3 rounded-lg font-medium transition-all text-left ${cognitiveTone === 'coaching'
                                    ? 'bg-trust-blue text-white shadow-md'
                                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                                    }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xl">📣</span>
                                    <span className="font-semibold">Coaching</span>
                                </div>
                                <p className={`text-xs ${cognitiveTone === 'coaching' ? 'text-blue-100' : 'text-gray-500'}`}>
                                    Motivational, probing, guides you
                                </p>
                            </button>
                            <button
                                onClick={() => setCognitiveTone('beginner_friendly')}
                                className={`px-4 py-3 rounded-lg font-medium transition-all text-left ${cognitiveTone === 'beginner_friendly'
                                    ? 'bg-trust-blue text-white shadow-md'
                                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                                    }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xl">🌱</span>
                                    <span className="font-semibold">Beginner Friendly</span>
                                </div>
                                <p className={`text-xs ${cognitiveTone === 'beginner_friendly' ? 'text-blue-100' : 'text-gray-500'}`}>
                                    Welcoming, simple, reassuring
                                </p>
                            </button>
                            <button
                                onClick={() => setCognitiveTone('key_points')}
                                className={`px-4 py-3 rounded-lg font-medium transition-all text-left ${cognitiveTone === 'key_points'
                                    ? 'bg-trust-blue text-white shadow-md'
                                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                                    }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xl">⚡️</span>
                                    <span className="font-semibold">Key Points Only</span>
                                </div>
                                <p className={`text-xs ${cognitiveTone === 'key_points' ? 'text-blue-100' : 'text-gray-500'}`}>
                                    Blunt, efficient, strictly business
                                </p>
                            </button>
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-1">
                    <div className="mb-6 sticky top-20">
                        <ProfilePreview userId={userId} />

                        <button
                            onClick={async () => {
                                const resolvedUserId = userId || resolveUserId();
                                if (!userId) {
                                    setUserId(resolvedUserId);
                                }
                                setIsSaving(true);
                                setSaveMessage(null);
                                try {
                                    const saved = await updateSettings(resolvedUserId, {
                                        study_preferences: {
                                            formats: selectedFormats,
                                            preferences: selectedPreferences,
                                            custom_style: customStyle,
                                            cognitive_tone: cognitiveTone,
                                        },
                                    });
                                    localStorage.setItem('hasOnboarded', 'true');
                                    setSaveMessage('Saved!');
                                    if (saved?.updated_at) {
                                        setSaveMessage(`Saved! ${new Date(saved.updated_at).toLocaleString()}`);
                                    }
                                    if (saved?.study_preferences) {
                                        const prefs = saved.study_preferences as Record<string, unknown>;
                                        if (Array.isArray(prefs.formats)) {
                                            setSelectedFormats(prefs.formats as string[]);
                                        }
                                        if (Array.isArray(prefs.preferences)) {
                                            setSelectedPreferences(prefs.preferences as string[]);
                                        }
                                        if (typeof prefs.custom_style === 'string') {
                                            setCustomStyle(prefs.custom_style);
                                        }
                                        if (typeof prefs.cognitive_tone === 'string') {
                                            setCognitiveTone(prefs.cognitive_tone);
                                        }
                                    }
                                    await loadSettings(resolvedUserId);
                                } catch (error) {
                                    console.error('Failed to save DNA', error);
                                    setSaveMessage('Save failed. Please try again.');
                                } finally {
                                    setIsSaving(false);
                                }
                            }}
                            className="w-full px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium mb-2 disabled:opacity-60 mt-4"
                            disabled={isSaving}
                        >
                            {isSaving ? 'Saving…' : '💾 Save & Continue'}
                        </button>

                        {saveMessage && (
                            <p className="text-xs text-center text-gray-500 mb-2">{saveMessage}</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
