import { useEffect, useState } from 'react';
import { Check, Headphones, Video, FileText, Image as ImageIcon, HelpCircle, Lightbulb, Share2, Mic, MonitorPlay } from 'lucide-react';
import { getSettings, updateSettings } from '../api/client';

export default function Onboarding() {
    const [selectedFormats, setSelectedFormats] = useState<string[]>(['audio', 'notes']);
    const [selectedPreferences, setSelectedPreferences] = useState<string[]>(['quizzes', 'analogies']);
    const [customStyle, setCustomStyle] = useState('');
    const [cognitiveTone, setCognitiveTone] = useState('socratic');
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<string | null>(null);
    const [userId, setUserId] = useState('');

    const normalizePref = (value: string) => value.replace(/_/g, ' ');

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
                                { id: 'podcast', label: 'Podcast Style', icon: Mic },
                                { id: 'lecture', label: 'Lecture Style', icon: MonitorPlay }, // Changed from User to MonitorPlay specifically for Lecture
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

                        <div className="flex gap-3 mb-3">
                            <button
                                onClick={() => setCognitiveTone('academic')}
                                className={`px-6 py-2 rounded-full font-medium transition-colors ${cognitiveTone === 'academic'
                                    ? 'bg-trust-blue text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                Academic
                            </button>
                            <button
                                onClick={() => setCognitiveTone('socratic')}
                                className={`px-6 py-2 rounded-full font-medium transition-colors ${cognitiveTone === 'socratic'
                                    ? 'bg-trust-blue text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                Socratic
                            </button>
                            <button
                                onClick={() => setCognitiveTone('eli5')}
                                className={`px-6 py-2 rounded-full font-medium transition-colors ${cognitiveTone === 'eli5'
                                    ? 'bg-trust-blue text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                ELI5
                            </button>
                            <button
                                onClick={() => setCognitiveTone('bulleted')}
                                className={`px-6 py-2 rounded-full font-medium transition-colors ${cognitiveTone === 'bulleted'
                                    ? 'bg-trust-blue text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                Bulleted
                            </button>
                        </div>

                        <p className="text-sm text-gray-600 italic">
                            * The "Socratic" tone asks guiding questions rather than giving direct answers, encouraging critical thinking.
                        </p>
                    </div>

                    <div>
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Style Matcher</h2>

                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-gray-400 transition-colors cursor-pointer">
                            <div className="text-5xl mb-4">📄</div>
                            <p className="text-gray-900 font-medium mb-2">Click to upload or drag and drop</p>
                            <p className="text-sm text-gray-500 mb-4">Upload handwritten notes or essays (PDF, IMG, TXT)</p>
                            <button className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
                                Browse Files
                            </button>
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-1">
                    <div className="bg-white rounded-lg shadow-sm p-6 mb-6 sticky top-20">
                        <h3 className="text-sm font-semibold text-gray-500 mb-4">DNA PREVIEW</h3>
                        <p className="text-xs text-gray-500 mb-4">CURRENT CONFIGURATION</p>

                        <div className="flex justify-center mb-6">
                            <div className="relative w-32 h-32">
                                <svg className="w-32 h-32 transform -rotate-90">
                                    <circle
                                        cx="64"
                                        cy="64"
                                        r="56"
                                        stroke="currentColor"
                                        strokeWidth="8"
                                        fill="none"
                                        className="text-gray-200"
                                    />
                                    <circle
                                        cx="64"
                                        cy="64"
                                        r="56"
                                        stroke="currentColor"
                                        strokeWidth="8"
                                        fill="none"
                                        strokeDasharray={`${2 * Math.PI * 56}`}
                                        strokeDashoffset={`${2 * Math.PI * 56 * 0.25}`}
                                        className="text-trust-blue"
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <div className="text-3xl mb-1">🧬</div>
                                    <span className="text-2xl font-bold text-gray-900">75%</span>
                                </div>
                            </div>
                        </div>

                        <h4 className="text-lg font-semibold text-gray-900 text-center mb-2">
                            {selectedPreferences
                                .slice(0, 2)
                                .map((p) => normalizePref(p).charAt(0).toUpperCase() + normalizePref(p).slice(1))
                                .join(' & ') || 'Custom'} Learner
                        </h4>
                        <p className="text-sm text-gray-600 text-center mb-4">
                            Your profile is optimized for <strong>{selectedFormats.join(', ')}</strong> content with {cognitiveTone} tone.
                        </p>

                        <div className="flex flex-wrap gap-2 justify-center mb-6">
                            {selectedFormats.map(f => (
                                <span key={f} className="px-3 py-1 bg-blue-50 text-trust-blue text-xs font-medium rounded-full">
                                    #{f.toUpperCase()}
                                </span>
                            ))}
                            <span className="px-3 py-1 bg-purple-50 text-purple-700 text-xs font-medium rounded-full">
                                #{cognitiveTone.toUpperCase()}
                            </span>
                        </div>

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
                            className="w-full px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium mb-2 disabled:opacity-60"
                            disabled={isSaving}
                        >
                            {isSaving ? 'Saving…' : '💾 Save & Continue'}
                        </button>

                        {saveMessage && (
                            <p className="text-xs text-center text-gray-500 mb-2">{saveMessage}</p>
                        )}
                    </div>

                    <div className="bg-gray-900 rounded-lg p-6 text-white">
                        <h3 className="text-lg font-semibold mb-2">Need Guidance?</h3>
                        <p className="text-sm text-gray-300 mb-4">
                            Not sure which cognitive tone fits you? Take our 3-minute assessment.
                        </p>
                        <button className="text-sm font-medium text-white hover:text-gray-200 transition-colors">
                            Start Assessment →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
