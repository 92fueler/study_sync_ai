import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Bookmark, Play, Pause, SkipBack, SkipForward, CheckCircle, Calendar, PauseCircle } from 'lucide-react'
import { cn } from '../utils/cn'
import { getArtifact } from '../api/client'
import Mermaid from '../components/Mermaid'

interface StudySessionProps {
  userId: string
}

interface SessionContent {
  id: string
  title: string
  subtitle: string
  sections: Array<{
    id: string
    title: string
    content: string
    mermaidCode?: string
    latex?: string
    bullets?: string[]
  }>
}

export default function StudySession({ userId }: StudySessionProps) {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [content, setContent] = useState<SessionContent | null>(null)
  const [context, setContext] = useState<'commute' | 'read' | 'quiz'>('commute')
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(765) // 12:45 in seconds
  const [progress, setProgress] = useState(35)
  const [isPaused, setIsPaused] = useState(false)

  useEffect(() => {
    loadSessionContent()
  }, [sessionId])

  const loadSessionContent = async () => {
    try {
      if (sessionId) {
        const artifact = await getArtifact(sessionId)
        // Transform API response to match our SessionContent interface
        // This is a mock - adjust based on actual API response
        setContent({
          id: sessionId,
          title: 'Introduction to Superposition',
          subtitle: 'Fundamental principles of quantum superposition and state collapse',
          sections: [
            {
              id: '1',
              title: 'Core Concepts',
              content: 'Quantum superposition is a fundamental principle of quantum mechanics. Unlike classical objects that exist in a single, well-defined state, quantum particles can exist in multiple states simultaneously until observed.',
              mermaidCode: `graph LR
    A[Quantum Particle] -->|Observation Event| B[State Collapse]
    B --> C[Definite State]
    style A fill:#3b82f6
    style B fill:#9333ea
    style C fill:#10b981`,
            },
            {
              id: '2',
              title: 'Mathematical Representation',
              content: 'The state of a quantum system is represented by a wave function, which is a linear combination of all possible states.',
              latex: '$$ |\\psi\\rangle = \\alpha |0\\rangle + \\beta |1\\rangle $$',
            },
            {
              id: '3',
              title: 'Implications',
              content: '',
              bullets: [
                'Measurement Problem: Why does observation force a choice?',
                'Quantum Computing: Using superposition for parallel processing',
              ],
            },
          ],
        })
      }
    } catch (error) {
      console.error('Failed to load session content:', error)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleSkipBack = () => {
    setCurrentTime(Math.max(0, currentTime - 10))
  }

  const handleSkipForward = () => {
    setCurrentTime(Math.min(duration, currentTime + 10))
  }

  if (!content) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading session...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-gray-200 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Bookmark className="w-6 h-6 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Study Manager</span>
            </div>
            <div className="text-sm text-gray-600">
              Dashboard &gt; Physics 101 &gt; Quantum Mechanics
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 rounded-full">
              <div className="w-2 h-2 bg-green-600 rounded-full"></div>
              <span className="text-sm font-medium text-green-700">G-Cal Sync Active</span>
            </div>
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
            >
              <PauseCircle className="w-4 h-4 text-gray-700" />
              <span className="text-sm font-medium text-gray-700">Pause Plan</span>
            </button>
            <div className="w-8 h-8 rounded-full bg-gray-200"></div>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Column - Master Note */}
        <div className="flex-1 overflow-y-auto p-8 bg-white">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-2 mb-4">
              <Bookmark className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-semibold text-blue-600 uppercase">Master Note</span>
            </div>

            <h1 className="text-4xl font-bold text-gray-900 mb-2">{content.title}</h1>
            <p className="text-lg text-gray-600 mb-8">{content.subtitle}</p>

            <div className="space-y-8">
              {content.sections.map((section) => (
                <div key={section.id} className="space-y-4">
                  <h2 className="text-2xl font-semibold text-gray-900">
                    {section.id}. {section.title}
                  </h2>

                  {section.content && (
                    <p className="text-gray-700 leading-relaxed">{section.content}</p>
                  )}

                  {section.mermaidCode && (
                    <div className="my-6">
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <Mermaid chart={section.mermaidCode} />
                      </div>
                      <p className="text-sm text-gray-500 mt-2 italic">
                        Figure {section.id}: Simplified flow of state determination
                      </p>
                    </div>
                  )}

                  {section.latex && (
                    <div className="my-6">
                      <div className="bg-gray-900 rounded-lg p-6 text-white font-mono">
                        <div className="text-lg">{section.latex}</div>
                        <p className="text-sm text-gray-400 mt-2">
                          Where alpha and beta are complex numbers
                        </p>
                      </div>
                    </div>
                  )}

                  {section.bullets && (
                    <ul className="list-disc list-inside space-y-2 text-gray-700">
                      {section.bullets.map((bullet, index) => (
                        <li key={index}>{bullet}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Active Context */}
        <div className="w-96 bg-gray-50 border-l border-gray-200 p-6 overflow-y-auto">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-sm font-semibold text-gray-900 uppercase">Active Context</span>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
              Stage 3
            </span>
          </div>

          {/* Context Selection */}
          <div className="flex gap-2 mb-6">
            {(['commute', 'read', 'quiz'] as const).map((ctx) => (
              <button
                key={ctx}
                onClick={() => setContext(ctx)}
                className={cn(
                  'flex-1 px-4 py-2 rounded-full text-sm font-medium transition-colors capitalize',
                  context === ctx
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                )}
              >
                {ctx}
              </button>
            ))}
          </div>

          {/* Media Player Card */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg p-6 mb-6 text-white">
            <div className="mb-4">
              <span className="text-xs font-semibold text-gray-400 uppercase">AI Narrator</span>
              <h3 className="text-lg font-bold mt-1">Superposition Deep Dive</h3>
              <p className="text-sm text-gray-400 mt-1">Part 1 of 4 • Physics 101</p>
            </div>

            {/* Waveform Visualization Placeholder */}
            <div className="h-16 bg-gray-800 rounded-lg mb-4 flex items-center justify-center">
              <div className="flex items-end gap-1 h-8">
                {[...Array(20)].map((_, i) => (
                  <div
                    key={i}
                    className="w-1 bg-blue-500 rounded-full"
                    style={{
                      height: `${Math.random() * 100}%`,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Playback Controls */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm text-gray-400">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
              </div>

              {/* Control Buttons */}
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={handleSkipBack}
                  className="p-2 hover:bg-gray-700 rounded-full transition-colors"
                >
                  <SkipBack className="w-5 h-5" />
                </button>
                <button
                  onClick={handlePlayPause}
                  className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center hover:bg-blue-700 transition-colors"
                >
                  {isPlaying ? (
                    <Pause className="w-6 h-6" />
                  ) : (
                    <Play className="w-6 h-6 ml-1" />
                  )}
                </button>
                <button
                  onClick={handleSkipForward}
                  className="p-2 hover:bg-gray-700 rounded-full transition-colors"
                >
                  <SkipForward className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Transcript */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-3 uppercase">Transcript</h4>
            <div className="space-y-2 text-sm text-gray-700 bg-white rounded-lg p-4 max-h-48 overflow-y-auto">
              <p>
                <span className="text-blue-600 font-medium">[03:45]</span> Let's begin by defining
                what we mean by a "state" in classical mechanics...
              </p>
              <p className="bg-blue-50 p-2 rounded">
                <span className="text-blue-600 font-medium">[04:20]</span> Unlike classical objects,
                a quantum particle can exist in multiple states simultaneously. This is the essence
                of superposition.
              </p>
            </div>
          </div>

          {/* Session Progress */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-900">Session Progress</span>
              <span className="text-sm text-gray-600">{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">15 min remaining</p>
          </div>

          {/* Action Button */}
          <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
            <CheckCircle className="w-5 h-5" />
            Mark Topic Complete
          </button>
        </div>
      </div>
    </div>
  )
}
