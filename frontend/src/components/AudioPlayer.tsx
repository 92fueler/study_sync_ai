import { useEffect, useState, useRef } from 'react';
import { Play, Pause, Volume2, Loader2 } from 'lucide-react';
import { getAudioMetadata, getAudioUrl } from '../api/client';

interface AudioPlayerProps {
    title: string;
    artifactId?: string;
}

export default function AudioPlayer({ title, artifactId }: AudioPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [loadError, setLoadError] = useState<boolean>(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    // Poll for audio metadata
    useEffect(() => {
        if (!artifactId) {
            setLoading(false);
            return;
        }

        let pollInterval: number;
        let attempts = 0;
        const maxAttempts = 60; // Poll for up to 10 minutes (60 * 10s)

        const checkAudioStatus = async () => {
            try {
                const metadata = await getAudioMetadata(artifactId);

                if (metadata.status === 'ready' && metadata.audio_url) {
                    // Extract filename from audio_url (e.g. /api/v1/audio/xxx.wav -> xxx.wav)
                    const filename = metadata.audio_url.split('/').pop();
                    if (filename) {
                        setAudioUrl(getAudioUrl(filename));
                        setLoadError(false);
                    }
                    setDuration(metadata.duration_seconds || 0);
                    setLoading(false);
                    clearInterval(pollInterval);
                } else if (attempts >= maxAttempts) {
                    setError('Audio generation timed out');
                    setLoading(false);
                    clearInterval(pollInterval);
                }
                attempts++;
            } catch (err) {
                // Audio not ready yet, keep polling
                if (attempts >= maxAttempts) {
                    setError('Audio not available');
                    setLoading(false);
                    clearInterval(pollInterval);
                }
                attempts++;
            }
        };

        // Initial check
        void checkAudioStatus();

        // Poll every 10 seconds
        pollInterval = setInterval(checkAudioStatus, 10000);

        return () => {
            if (pollInterval) clearInterval(pollInterval);
        };
    }, [artifactId]);

    // Handle audio element events
    useEffect(() => {
        if (!audioRef.current) return;

        const audio = audioRef.current;

        const handleTimeUpdate = () => {
            setCurrentTime(audio.currentTime);
        };

        const handleLoadedMetadata = () => {
            setDuration(audio.duration);
        };

        const handleEnded = () => {
            setIsPlaying(false);
        };

        audio.addEventListener('timeupdate', handleTimeUpdate);
        audio.addEventListener('loadedmetadata', handleLoadedMetadata);
        audio.addEventListener('ended', handleEnded);

        return () => {
            audio.removeEventListener('timeupdate', handleTimeUpdate);
            audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
            audio.removeEventListener('ended', handleEnded);
        };
    }, [audioUrl]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const togglePlay = () => {
        if (!audioRef.current) return;

        if (isPlaying) {
            audioRef.current.pause();
        } else {
            void audioRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!audioRef.current || !duration) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = x / rect.width;
        const newTime = percentage * duration;

        audioRef.current.currentTime = newTime;
        setCurrentTime(newTime);
    };

    // Don't show player if no artifactId provided
    if (!artifactId) {
        return null;
    }

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
                        {loading ? (
                            <Loader2 className="w-4 h-4 text-white animate-spin" />
                        ) : (
                            <Volume2 className="w-4 h-4 text-white" />
                        )}
                    </div>
                    <h3 className="text-base font-bold leading-tight mb-1">{title}</h3>
                    {loading && <p className="text-indigo-300 text-xs mt-2">Generating audio...</p>}
                    {error && <p className="text-red-300 text-xs mt-2">{error}</p>}
                    {loadError && !loading && <p className="text-amber-300 text-xs mt-2">Audio file not available. Try a new upload with Audio enabled in My DNA.</p>}
                </div>
            </div>

            {/* Controls Area - Right Side */}
            <div className="flex-1 p-6 bg-gray-900 flex flex-col justify-center">
                {loading ? (
                    <div className="text-center text-gray-400 text-sm">
                        <Loader2 className="w-6 h-6 mx-auto mb-2 animate-spin" />
                        <p>Audio is being generated...</p>
                        <p className="text-xs mt-1">This may take up to 10 minutes</p>
                    </div>
                ) : error ? (
                    <div className="text-center text-gray-400 text-sm">
                        <p>{error}</p>
                    </div>
                ) : loadError ? (
                    <div className="text-center text-gray-400 text-sm">
                        <p>Audio could not be loaded.</p>
                        <p className="text-xs mt-1">Upload a new file with Audio enabled to get playable audio.</p>
                    </div>
                ) : (
                    <>
                        {/* Progress Bar */}
                        <div className="flex items-center justify-between text-xs text-gray-400 mb-2 font-mono">
                            <span>{formatTime(currentTime)}</span>
                            <span>{formatTime(duration)}</span>
                        </div>
                        <div
                            className="w-full h-1.5 bg-gray-700 rounded-full mb-6 cursor-pointer group"
                            onClick={handleSeek}
                        >
                            <div
                                className="h-full bg-indigo-500 rounded-full relative group-hover:bg-indigo-400 transition-colors"
                                style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
                            >
                                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 shadow-md transition-opacity" />
                            </div>
                        </div>

                        {/* Play/Pause Button */}
                        <div className="flex items-center justify-center">
                            <button
                                onClick={togglePlay}
                                disabled={!audioUrl || loadError}
                                className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isPlaying ? (
                                    <Pause className="w-5 h-5 fill-current" />
                                ) : (
                                    <Play className="w-5 h-5 fill-current ml-0.5" />
                                )}
                            </button>
                        </div>

                        {/* Hidden audio element - onError when file missing (404) or CORS */}
                        {audioUrl && (
                            <audio
                                ref={audioRef}
                                src={audioUrl}
                                preload="metadata"
                                onError={() => setLoadError(true)}
                                onLoadedMetadata={() => setLoadError(false)}
                            />
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
