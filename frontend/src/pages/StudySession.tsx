import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Bookmark, Play, Pause, SkipBack, SkipForward, CheckCircle, PauseCircle } from 'lucide-react'
import { cn } from '../utils/cn'
import { getLearningPlan } from '../api/client'

interface StudySessionProps {
  userId?: string
}

interface SessionSection {
  id: string
  title: string
  content: string
  bullets?: string[]
}

interface SessionContent {
  id: string
  title: string
  subtitle: string
  sections: SessionSection[]
}

export default function StudySession({ }: StudySessionProps) {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [content, setContent] = useState<SessionContent | null>(null)
  const [context, setContext] = useState<'commute' | 'read' | 'quiz'>('commute')
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [progress, setProgress] = useState(0)
  const [userId, setUserId] = useState('')

  useEffect(() => {
    const storedUserId = localStorage.getItem('user_id')
    if (storedUserId) {
      setUserId(storedUserId)
      return
    }
    const tempUserId = `user_${Date.now()}`
    localStorage.setItem('user_id', tempUserId)
    setUserId(tempUserId)
  }, [])

  useEffect(() => {
    if (!sessionId || !userId) return
    const loadSessionContent = async () => {
      try {
        const response = await getLearningPlan(sessionId, userId)
        const plan = response.plan || response
        const items = response.items || plan.items || []
        const sections = items.map((item: any, index: number) => ({
          id: item.id || String(index + 1),
          title: item.title || `Module ${index + 1}`,
          content: item.description || 'No description provided.',
          bullets: item.content_ids ? item.content_ids.map((cid: string) => `Content ${cid}`) : undefined,
        }))

        const totalMinutes = items.reduce((sum: number, item: any) => {
          const estimated = Number(item.estimated_minutes) || 45
          return sum + estimated
        }, 0)
        setDuration(totalMinutes * 60)
        if (plan.progress_percent != null) {
          setProgress(plan.progress_percent)
        } else {
          const completed = items.filter((item: any) => item.status === 'done').length
          setProgress(items.length ? Math.round((completed / items.length) * 100) : 0)
        }

        setContent({
          id: plan.id,
          title: plan.title || 'Learning Session',
          subtitle: plan.description || 'No description provided.',
          sections,
        })
      } catch (error) {
        console.error('Failed to load session content:', error)
        setContent(null)
      }
    }

    void loadSessionContent()
  }, [sessionId, userId])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')} `
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
      <div className="bg-white border-b border-gray-200 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Bookmark className="w-6 h-6 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Study Manager</span>
            </div>
            <div className="text-sm text-gray-600">
              Session {content.id}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">{content.title}</h1>
          <p className="text-lg text-gray-600 mb-8">{content.subtitle}</p>

          <div className="flex items-center gap-4">
            <button
              className={cn(
                'px-4 py-2 rounded-lg border text-sm font-medium',
                context === 'commute'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-600 border-gray-200'
              )}
              onClick={() => setContext('commute')}
            >
              Commute
            </button>
            <button
              className={cn(
                'px-4 py-2 rounded-lg border text-sm font-medium',
                context === 'read'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-600 border-gray-200'
              )}
              onClick={() => setContext('read')}
            >
              Read
            </button>
            <button
              className={cn(
                'px-4 py-2 rounded-lg border text-sm font-medium',
                context === 'quiz'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-600 border-gray-200'
              )}
              onClick={() => setContext('quiz')}
            >
              Quiz
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="text-sm text-gray-500">Audio Session</div>
              <div className="text-xl font-semibold text-gray-900">{content.title}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Progress</div>
              <div className="text-lg font-semibold text-blue-600">{progress}%</div>
            </div>
          </div>

          <div className="bg-gray-100 rounded-full h-2 mb-4">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${progress}%` }} />
          </div>

          <div className="flex items-center justify-between text-sm text-gray-600 mb-6">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>

          <div className="flex items-center justify-center gap-6 mb-8">
            <button onClick={handleSkipBack} className="p-3 rounded-full bg-gray-100 hover:bg-gray-200">
              <SkipBack className="w-5 h-5" />
            </button>
            <button
              onClick={handlePlayPause}
              className="p-4 rounded-full bg-blue-600 text-white hover:bg-blue-700"
            >
              {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
            </button>
            <button onClick={handleSkipForward} className="p-3 rounded-full bg-gray-100 hover:bg-gray-200">
              <SkipForward className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-8">
            {content.sections.length === 0 ? (
              <div className="text-sm text-gray-500">No modules for this plan yet.</div>
            ) : (
              content.sections.map((section) => (
                <div key={section.id} className="space-y-4">
                  <h2 className="text-2xl font-semibold text-gray-900">
                    {section.title}
                  </h2>
                  {section.content && (
                    <p className="text-gray-700 leading-relaxed">{section.content}</p>
                  )}
                  {section.bullets && (
                    <ul className="list-disc list-inside space-y-2 text-gray-700">
                      {section.bullets.map((bullet, index) => (
                        <li key={index}>{bullet}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-2 text-gray-900 font-semibold mb-2">
              <CheckCircle className="w-5 h-5 text-green-500" /> Completed
            </div>
            <p className="text-sm text-gray-600">Track your finished modules here.</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-2 text-gray-900 font-semibold mb-2">
              <Play className="w-5 h-5 text-blue-500" /> Next Up
            </div>
            <p className="text-sm text-gray-600">Queue the next study segment.</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-2 text-gray-900 font-semibold mb-2">
              <PauseCircle className="w-5 h-5 text-orange-500" /> Paused
            </div>
            <p className="text-sm text-gray-600">Resume when you're ready.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
