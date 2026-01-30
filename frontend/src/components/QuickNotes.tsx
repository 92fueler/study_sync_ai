import { useState } from 'react';
import { PenTool, Save, ChevronDown } from 'lucide-react';

interface QuickNotesProps {
    activeSection: string;
    onSectionChange: (section: string) => void;
}

const SECTIONS = [
    { id: 'global', label: 'General / Global' },
    { id: 'core-concepts', label: '1. Core Concepts' },
    { id: 'math-rep', label: '2. Math Representation' },
    { id: 'implications', label: '3. Implications' },
    { id: 'audio-segment', label: 'Audio Segment' },
];

export default function QuickNotes({ activeSection, onSectionChange }: QuickNotesProps) {
    const [note, setNote] = useState('');
    const [isSaved, setIsSaved] = useState(false);

    const handleSave = () => {
        setIsSaved(true);
        // Simulate API save with context
        console.log('Saving note:', { context: activeSection, content: note });
        setTimeout(() => setIsSaved(false), 2000);
        setNote('');
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6 sticky top-24">
            <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <PenTool className="w-4 h-4 text-trust-blue" />
                    Quick Note
                </h3>
            </div>

            {/* Context Selector */}
            <div className="mb-3 relative">
                <label className="text-xs text-gray-500 font-medium mb-1 block">Attaching to context:</label>
                <div className="relative">
                    <select
                        value={activeSection}
                        onChange={(e) => onSectionChange(e.target.value)}
                        className="w-full appearance-none bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg pl-3 pr-8 py-2 focus:ring-2 focus:ring-trust-blue focus:border-trust-blue transition-all"
                    >
                        {SECTIONS.map((section) => (
                            <option key={section.id} value={section.id}>
                                {section.label}
                            </option>
                        ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                </div>
            </div>

            <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder={`Add a note about ${SECTIONS.find(s => s.id === activeSection)?.label.replace(/^\d+\.\s/, '')}...`}
                className="w-full h-32 p-3 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-trust-blue focus:border-trust-blue resize-none mb-3 bg-gray-50 focus:bg-white transition-colors"
            />

            <div className="flex justify-end">
                <button
                    onClick={handleSave}
                    disabled={!note.trim()}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-all ${note.trim()
                        ? 'bg-trust-blue text-white hover:bg-blue-700 shadow-sm'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                >
                    {isSaved ? (
                        <>Saved!</>
                    ) : (
                        <>
                            <Save className="w-3.5 h-3.5" />
                            Save Note
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}
