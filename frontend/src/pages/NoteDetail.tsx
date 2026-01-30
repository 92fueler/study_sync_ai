import { useState } from 'react';
import { ChevronRight, ArrowLeft, Maximize2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import AudioPlayer from '../components/AudioPlayer';
import QuickNotes from '../components/QuickNotes';
import ProgressRoadmap from '../components/ProgressRoadmap';

export default function NoteDetail() {
    const [activeSection, setActiveSection] = useState('global');
    return (
        <div className="max-w-7xl mx-auto px-6 py-8">
            {/* Breadcrumb & Header */}
            <div className="mb-8">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                    <Link to="/" className="hover:text-trust-blue transition-colors flex items-center gap-1">
                        <ArrowLeft className="w-3 h-3" /> Dashboard
                    </Link>
                    <ChevronRight className="w-3 h-3" />
                    <span>Physics 101</span>
                    <ChevronRight className="w-3 h-3" />
                    <span className="text-gray-900 font-medium">Quantum Mechanics</span>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <span className="px-2 py-0.5 bg-blue-100 text-trust-blue text-xs font-bold uppercase tracking-wider rounded">Master Note</span>
                            <span className="text-sm text-gray-500">October 24, 2023</span>
                        </div>
                        <h1 className="text-4xl font-serif font-bold text-gray-900 mb-2">
                            Introduction to Superposition
                        </h1>
                        <p className="text-lg text-gray-600">
                            Fundamental principles of quantum superposition and state collapse.
                        </p>
                    </div>

                    <div className="flex gap-3">
                        <button className="px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">
                            Pause Plan
                        </button>
                        <button className="px-4 py-2 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm font-bold flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                            G-Cal Sync: Active
                        </button>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                {/* LEFT COLUMN: Main Content (8 cols) */}
                <div className="lg:col-span-8">


                    {/* Content Feed */}
                    <div className="space-y-12">

                        {/* Section 1 */}
                        <section
                            onClick={() => setActiveSection('core-concepts')}
                            className={`transition-colors p-4 -m-4 rounded-xl ${activeSection === 'core-concepts' ? 'bg-blue-50/50' : ''}`}
                        >
                            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-3 cursor-pointer group">
                                <span className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-colors ${activeSection === 'core-concepts' ? 'bg-trust-blue text-white' : 'bg-gray-100 text-gray-600'}`}>1</span>
                                Core Concepts
                            </h2>
                            <div className="prose prose-lg text-gray-600 max-w-none">
                                <p className="mb-6 leading-relaxed">
                                    Quantum superposition is a fundamental principle of quantum mechanics. It states that, much like waves in classical physics, any two (or more) quantum states can be added together ("superposed") and the result will be another valid quantum state; and conversely, that every quantum state can be represented as a sum of two or more other distinct states.
                                </p>
                            </div>

                            {/* Rich Media Block: Diagram */}
                            <div className="bg-white border border-gray-200 rounded-xl p-8 mb-6 relative overflow-hidden group">
                                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button className="p-2 text-gray-400 hover:text-gray-600">
                                        <Maximize2 className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="flex justify-center items-center py-4">
                                    {/* Mock Mermaid Diagram */}
                                    <div className="flex items-center gap-4 text-sm font-medium">
                                        <div className="px-4 py-3 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg shadow-sm">
                                            Quantum Particle
                                        </div>
                                        <div className="text-gray-400">─────▶</div>
                                        <div className="px-4 py-3 bg-purple-50 border border-purple-200 text-purple-700 rounded-lg shadow-sm">
                                            Observation Event
                                        </div>
                                        <div className="text-gray-400">─────▶</div>
                                        <div className="px-4 py-3 bg-green-50 border border-green-200 text-green-700 rounded-lg shadow-sm">
                                            State Collapse
                                        </div>
                                    </div>
                                </div>
                                <p className="text-center text-xs text-gray-400 italic mt-6">
                                    Figure 1.1: Simplified flow of state determination
                                </p>
                            </div>
                        </section>

                        {/* Section 2 */}
                        <section
                            onClick={() => setActiveSection('math-rep')}
                            className={`transition-colors p-4 -m-4 rounded-xl ${activeSection === 'math-rep' ? 'bg-blue-50/50' : ''}`}
                        >
                            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-3 cursor-pointer group">
                                <span className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-colors ${activeSection === 'math-rep' ? 'bg-trust-blue text-white' : 'bg-gray-100 text-gray-600'}`}>2</span>
                                Mathematical Representation
                            </h2>
                            <p className="text-gray-600 mb-6 leading-relaxed">
                                Mathematically, it refers to a property of solutions to the Schrödinger equation; since the Schrödinger equation is linear, any linear combination of solutions is also a solution.
                            </p>

                            {/* Code Block */}
                            <div className="bg-gray-900 rounded-lg p-6 font-mono text-sm text-gray-300 relative mb-6">
                                <div className="absolute top-3 left-3 flex gap-1.5">
                                    <div className="w-3 h-3 rounded-full bg-red-400" />
                                    <div className="w-3 h-3 rounded-full bg-yellow-400" />
                                    <div className="w-3 h-3 rounded-full bg-green-400" />
                                </div>
                                <div className="pt-4 overflow-x-auto">
                                    <p className="mb-2"><span className="text-purple-400">$$</span> |\psi\rangle = \alpha|0\rangle + \beta|1\rangle <span className="text-purple-400">$$</span></p>
                                    <p className="text-gray-500"># Where alpha and beta are complex numbers</p>
                                </div>
                            </div>

                            {/* Audio Segment at end of section */}
                            <AudioPlayer
                                title="Mathematical Deep Dive"
                                subtitle="Explanation of Schrödinger's equation"
                                duration={245}
                            />
                        </section>

                        {/* Section 3 */}
                        <section
                            onClick={() => setActiveSection('implications')}
                            className={`transition-colors p-4 -m-4 rounded-xl ${activeSection === 'implications' ? 'bg-blue-50/50' : ''}`}
                        >
                            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-3 cursor-pointer group">
                                <span className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-colors ${activeSection === 'implications' ? 'bg-trust-blue text-white' : 'bg-gray-100 text-gray-600'}`}>3</span>
                                Implications
                            </h2>
                            <ul className="space-y-4">
                                <li className="flex items-start gap-3">
                                    <div className="w-1.5 h-1.5 bg-trust-blue rounded-full mt-2.5" />
                                    <p className="text-gray-600">
                                        <strong className="text-gray-900">Measurement Problem:</strong> Why does observation force a choice? This remains one of the greatest unsolved problems in physics.
                                    </p>
                                </li>
                                <li className="flex items-start gap-3">
                                    <div className="w-1.5 h-1.5 bg-trust-blue rounded-full mt-2.5" />
                                    <p className="text-gray-600">
                                        <strong className="text-gray-900">Quantum Computing:</strong> Using superposition for parallel processing allows qubits to exist in multiple states at once.
                                    </p>
                                </li>
                            </ul>
                        </section>

                    </div>
                </div>

                {/* RIGHT COLUMN: Sticky Sidebar (4 cols) */}
                <div className="lg:col-span-4">
                    <div className="sticky top-24 space-y-6">

                        {/* 1. Quick Notes Module */}
                        <QuickNotes
                            activeSection={activeSection}
                            onSectionChange={setActiveSection}
                        />

                        {/* 2. Progress Roadmap Module */}
                        <ProgressRoadmap />

                    </div>
                </div>
            </div>
        </div>
    );
}
