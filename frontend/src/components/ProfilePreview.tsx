import { useEffect, useState } from 'react';
import { getSettings } from '../api/client';

interface ProfilePreviewProps {
    userId: string;
}

export default function ProfilePreview({ userId }: ProfilePreviewProps) {
    const [selectedFormats, setSelectedFormats] = useState<string[]>([]);
    const [selectedPreferences, setSelectedPreferences] = useState<string[]>([]);
    const [cognitiveTone, setCognitiveTone] = useState('socratic');

    const getCognitiveToneLabel = (tone: string): string => {
        const toneMap: { [key: string]: string } = {
            'textbook': '🎓 Textbook',
            'coaching': '📣 Coaching',
            'beginner_friendly': '🌱 Beginner Friendly',
            'key_points': '⚡️ Key Points Only',
            // Legacy mappings for backward compatibility
            'academic': '🎓 Textbook',
            'socratic': '📣 Coaching',
            'eli5': '🌱 Beginner Friendly',
            'bulleted': '⚡️ Key Points Only'
        };
        return toneMap[tone] || tone;
    };

    const getFormatLabel = (format: string): string => {
        const formatMap: { [key: string]: string } = {
            'audio': 'Audio',
            'video': 'Video',
            'notes': 'Notes',
            'images': 'Images'
        };
        return formatMap[format] || format;
    };

    const getPreferenceLabel = (pref: string): string => {
        const prefMap: { [key: string]: string } = {
            'quizzes': 'Quizzes',
            'analogies': 'Analogies',
            'knowledge_graph': 'Knowledge Graph',
            'lecture': 'Lecture Style'
        };
        return prefMap[pref] || pref.replace(/_/g, ' ');
    };

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
            if (typeof prefs.cognitive_tone === 'string') {
                setCognitiveTone(prefs.cognitive_tone);
            }
        } catch (error) {
            console.error('Failed to load DNA settings', error);
        }
    };

    useEffect(() => {
        if (!userId) return;
        void loadSettings(userId);
    }, [userId]);

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

    return (
        <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center gap-2 mb-6">
                <div className="text-3xl">🧬</div>
                <h3 className="text-lg font-semibold text-gray-500">DNA PREVIEW</h3>
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

            <div className="flex flex-wrap gap-2 justify-center">
                {selectedFormats.map(f => (
                    <span key={f} className="px-3 py-1 bg-blue-50 text-trust-blue text-xs font-medium rounded-full">
                        #{f.toUpperCase()}
                    </span>
                ))}
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
                <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                    {getCognitiveToneLabel(cognitiveTone)}
                </span>
            </div>
        </div>
    );
}
