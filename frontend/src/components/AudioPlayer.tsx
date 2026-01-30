import { useState } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, RotateCcw, RotateCw } from 'lucide-react';

interface AudioPlayerProps {
    title: string;
    subtitle?: string;
    duration?: number; // in seconds
    src?: string; // Optional real source
}

export default function AudioPlayer({ title, subtitle, duration = 1245 }: AudioPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime] = useState(260); // Mock current time (4:20)

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const togglePlay = () => setIsPlaying(!isPlaying);

    return (
        <div className="bg-gray-900 rounded-xl overflow-hidden shadow-lg text-white mb-8 flex flex-col md:flex-row h-auto md:h-40">
            {/* Album Art / Visualizer Area - Left Side */}
            <div className="relative w-full md:w-64 bg-gradient-to-br from-indigo-900 to-black flex flex-col items-center justify-center p-6 flex-shrink-0">
                {/* Abstract Waves Background */}
                <div className="absolute inset-0 opacity-30">
                    <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                        <path d="M0 50 Q 25 30 50 50 T 100 50 V 100 H 0 Z" fill="#4F46E5" />
                        <path d="M0 60 Q 25 40 50 60 T 100 60 V 100 H 0 Z" fill="#818CF8" opacity="0.5" />
                    </svg>
                </div>

                <div className="relative z-10 text-center">
                    <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm mb-2">
                        <Volume2 className="w-4 h-4 text-white" />
                    </div>
                    <h3 className="text-base font-bold leading-tight mb-1">{title}</h3>
                    {subtitle && <p className="text-indigo-200 text-xs">{subtitle}</p>}
                </div>
            </div>

            {/* Controls Area - Right Side */}
            <div className="flex-1 p-6 bg-gray-900 flex flex-col justify-center">
                {/* Progress Bar */}
                <div className="flex items-center justify-between text-xs text-gray-400 mb-2 font-mono">
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                </div>
                <div className="w-full h-1.5 bg-gray-700 rounded-full mb-6 cursor-pointer group">
                    <div
                        className="h-full bg-indigo-500 rounded-full relative group-hover:bg-indigo-400 transition-colors"
                        style={{ width: `${(currentTime / duration) * 100}%` }}
                    >
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 shadow-md transition-opacity" />
                    </div>
                </div>

                {/* Buttons */}
                <div className="flex items-center justify-center gap-6">
                    <button className="text-gray-400 hover:text-white transition-colors">
                        <SkipBack className="w-4 h-4" />
                    </button>
                    <button className="text-gray-400 hover:text-white transition-colors">
                        <RotateCcw className="w-4 h-4" />
                    </button>

                    <button
                        onClick={togglePlay}
                        className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
                    >
                        {isPlaying ? (
                            <Pause className="w-5 h-5 fill-current" />
                        ) : (
                            <Play className="w-5 h-5 fill-current ml-0.5" />
                        )}
                    </button>

                    <button className="text-gray-400 hover:text-white transition-colors">
                        <RotateCw className="w-4 h-4" />
                    </button>
                    <button className="text-gray-400 hover:text-white transition-colors">
                        <SkipForward className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
