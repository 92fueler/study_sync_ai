import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { getVideoMetadata, getVideoUrl } from '../api/client'

interface VideoPlayerProps {
    title: string
    artifactId?: string
    requested?: boolean
}

export default function VideoPlayer({ title, artifactId, requested = true }: VideoPlayerProps) {
    const [videoUrl, setVideoUrl] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [progress, setProgress] = useState(0);
    const [statusText, setStatusText] = useState('Initializing video...');
    const formatVideoError = (message?: string | null) => {
        if (!message) return 'Video generation failed';
        const lower = message.toLowerCase();
        if (lower.includes('429') || lower.includes('resource_exhausted') || lower.includes('quota')) {
            return 'Video quota exceeded (429). Retry later or upgrade quota.';
        }
        return message;
    };

    useEffect(() => {
        setVideoUrl(null)
        setProgress(0)
        setStatusText('Initializing video...')
        setLoading(true)
        setError(null)

        if (!requested) {
            setLoading(false)
            setError(null)
            setStatusText('No video requested')
            return
        }

        if (!artifactId) {
            setLoading(false)
            setError('Video request pending artifact')
            return
        }

        let currentPollInterval: ReturnType<typeof setInterval> | null = null
        let attempts = 0
        const maxAttempts = 120 // Poll for up to 20 minutes

        const checkVideoStatus = async () => {
            try {
                const metadata = await getVideoMetadata(artifactId)

                if (metadata.status === 'ready' && metadata.video_url) {
                    const filename = metadata.video_url.split('/').pop()
                    if (!filename) {
                        setError('Video metadata is missing a file path')
                        setLoading(false)
                        if (currentPollInterval) clearInterval(currentPollInterval)
                        return
                    }
                    setVideoUrl(getVideoUrl(filename))
                    setLoading(false)
                    if (currentPollInterval) clearInterval(currentPollInterval)
                } else if (metadata.status === 'failed') {
                    setError(formatVideoError(metadata.error_message))
                    setLoading(false)
                    if (currentPollInterval) clearInterval(currentPollInterval)
                } else if (metadata.status === 'generating') {
                    // Update progress
                    if (metadata.progress !== undefined) {
                        setProgress(metadata.progress)
                        const current = metadata.current_segment || 0
                        const total = metadata.total_segments || 0
                        const remaining = total - current
                        // Estimate 45 seconds per segment for Veo 3
                        const estSeconds = remaining * 45
                        const timeText = estSeconds > 60
                            ? `${Math.ceil(estSeconds / 60)} mins`
                            : `${estSeconds} secs`

                        setStatusText(`Generating segment ${current} of ${total} (${timeText} left)`)
                    }
                }
            } catch (err: any) {
                console.log('Video not found yet, polling...')
                const detail = err?.response?.data?.detail
                if (typeof detail === 'string' && detail.toLowerCase().includes('429')) {
                    setError(formatVideoError(detail))
                    setLoading(false)
                    if (currentPollInterval) clearInterval(currentPollInterval)
                }
            }
            attempts++
            if (attempts >= maxAttempts) {
                if (currentPollInterval) clearInterval(currentPollInterval)
                setError('Video generation timed out')
                setLoading(false)
            }
        }

        // Check immediately
        void checkVideoStatus()

        // Poll every 5 seconds
        currentPollInterval = setInterval(checkVideoStatus, 5000)

        return () => {
            if (currentPollInterval) clearInterval(currentPollInterval)
        }
    }, [artifactId, requested])

    if (!requested) {
        return (
            <div className="bg-white rounded-xl shadow-sm p-6 flex flex-col items-center justify-center min-h-[200px]">
                <p className="text-gray-900 font-medium mb-1">No video requested</p>
                <p className="text-gray-500 text-sm">Request a video from this note to start generation.</p>
            </div>
        )
    }

    if (!artifactId) {
        return (
            <div className="bg-white rounded-xl shadow-sm p-6 flex flex-col items-center justify-center min-h-[200px]">
                <p className="text-gray-900 font-medium mb-1">Video request pending artifact</p>
                <p className="text-gray-500 text-sm">Try again once note processing finishes.</p>
            </div>
        )
    }

    if (loading) {
        return (
            <div className="bg-gray-900 rounded-xl shadow-sm p-8 flex flex-col items-center justify-center text-white min-h-[300px]">
                <Loader2 className="w-10 h-10 animate-spin text-blue-500 mb-4" />
                <h3 className="text-lg font-medium mb-2">Generating personalized video...</h3>
                <p className="text-gray-400 text-sm mb-6">{statusText}</p>

                {/* Progress Bar */}
                <div className="w-full max-w-md bg-gray-700 rounded-full h-2">
                    <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${Math.max(5, progress)}%` }}
                    />
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="bg-white rounded-xl shadow-sm p-6 flex flex-col items-center justify-center min-h-[200px]">
                <p className="text-red-500 font-medium mb-1">Unable to load video</p>
                <p className="text-gray-500 text-sm">{error}</p>
            </div>
        )
    }

    return (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b">
                <h3 className="font-semibold text-gray-900">{title}</h3>
            </div>
            <div className="relative bg-black">
                <video
                    src={videoUrl || undefined}
                    controls
                    className="w-full"
                    style={{ maxHeight: '600px' }}
                >
                    Your browser does not support the video tag.
                </video>
            </div>
        </div>
    )
}
