import { useState } from 'react';
import { Check } from 'lucide-react';

export default function Onboarding() {
    const [selectedFormats, setSelectedFormats] = useState(['podcast', 'diagrams']);
    const [cognitiveTone, setCognitiveTone] = useState('socratic');

    const toggleFormat = (format: string) => {
        setSelectedFormats(prev =>
            prev.includes(format)
                ? prev.filter(f => f !== format)
                : [...prev, format]
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
                        Configure your personalized AI learning experience to match your unique cognitive style. We'll adapt content formats and tones specifically for you.
                    </p>

                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-semibold text-gray-900">Format Preferences</h2>
                            <span className="text-sm text-gray-500">Select all that apply</span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <button
                                onClick={() => toggleFormat('podcast')}
                                className={`relative p-6 rounded-lg border-2 transition-all text-left ${selectedFormats.includes('podcast')
                                        ? 'border-trust-blue bg-blue-50'
                                        : 'border-gray-200 bg-white hover:border-gray-300'
                                    }`}
                            >
                                {selectedFormats.includes('podcast') && (
                                    <div className="absolute top-3 right-3 w-6 h-6 bg-trust-blue rounded-full flex items-center justify-center">
                                        <Check className="w-4 h-4 text-white" />
                                    </div>
                                )}
                                <div className="text-3xl mb-3">🎧</div>
                                <h3 className="font-semibold text-gray-900 mb-1">Podcast Scripts</h3>
                                <p className="text-sm text-gray-600">Audio-first summaries tailored for listening on the go.</p>
                            </button>

                            <button
                                onClick={() => toggleFormat('quizzes')}
                                className={`relative p-6 rounded-lg border-2 transition-all text-left ${selectedFormats.includes('quizzes')
                                        ? 'border-trust-blue bg-blue-50'
                                        : 'border-gray-200 bg-white hover:border-gray-300'
                                    }`}
                            >
                                {selectedFormats.includes('quizzes') && (
                                    <div className="absolute top-3 right-3 w-6 h-6 bg-trust-blue rounded-full flex items-center justify-center">
                                        <Check className="w-4 h-4 text-white" />
                                    </div>
                                )}
                                <div className="text-3xl mb-3">📋</div>
                                <h3 className="font-semibold text-gray-900 mb-1">Socratic Quizzes</h3>
                                <p className="text-sm text-gray-600">Interactive Q&A sessions to test comprehension actively.</p>
                            </button>

                            <button
                                onClick={() => toggleFormat('diagrams')}
                                className={`relative p-6 rounded-lg border-2 transition-all text-left ${selectedFormats.includes('diagrams')
                                        ? 'border-trust-blue bg-blue-50'
                                        : 'border-gray-200 bg-white hover:border-gray-300'
                                    }`}
                            >
                                {selectedFormats.includes('diagrams') && (
                                    <div className="absolute top-3 right-3 w-6 h-6 bg-trust-blue rounded-full flex items-center justify-center">
                                        <Check className="w-4 h-4 text-white" />
                                    </div>
                                )}
                                <div className="text-3xl mb-3">📊</div>
                                <h3 className="font-semibold text-gray-900 mb-1">Visual Diagrams</h3>
                                <p className="text-sm text-gray-600">Flowcharts and mind maps for structural learners.</p>
                            </button>
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
                            Visual & Socratic
                        </h4>
                        <p className="text-sm text-gray-600 text-center mb-4">
                            Your profile is optimized for <strong>rapid visual intake</strong> with critical thinking checks.
                        </p>

                        <div className="flex flex-wrap gap-2 justify-center mb-6">
                            <span className="px-3 py-1 bg-blue-50 text-trust-blue text-xs font-medium rounded-full">
                                #VisualLearner
                            </span>
                            <span className="px-3 py-1 bg-blue-50 text-trust-blue text-xs font-medium rounded-full">
                                #TimeCompressed
                            </span>
                            <span className="px-3 py-1 bg-blue-50 text-trust-blue text-xs font-medium rounded-full">
                                #SocraticMethod
                            </span>
                        </div>

                        <button className="w-full px-6 py-3 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors font-medium mb-2">
                            💾 Update Learning DNA
                        </button>

                        <p className="text-xs text-gray-500 text-center">Last updated: 2 hours ago</p>
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
