import { useState } from 'react'
import { Check, FileText, Headphones, Image as ImageIcon, Video, Upload, ArrowRight } from 'lucide-react'
import { cn } from '../utils/cn'
import { createProfile } from '../api/client'

interface OnboardingProps {
  userId: string
  onComplete: () => void
}

type FormatPreference = 'text' | 'podcast' | 'diagram' | 'video'
type TeachingTone = 'eli5' | 'socratic' | 'academic'
type SessionLength = '<10' | '10-15' | '30' | '60' | '120'
type WeeklyCommitment = 'infrequent' | 'frequent' | 'consistent'
type ContextualOpt = 'yes-audio' | 'yes-visual' | 'no'

export default function Onboarding({ userId, onComplete }: OnboardingProps) {
  const [step, setStep] = useState(1)
  const [formatPrefs, setFormatPrefs] = useState<FormatPreference[]>([])
  const [teachingTone, setTeachingTone] = useState<TeachingTone | null>(null)
  const [qualitativeSample, setQualitativeSample] = useState<File | null>(null)
  const [sessionLength, setSessionLength] = useState<SessionLength | null>(null)
  const [weeklyCommitment, setWeeklyCommitment] = useState<WeeklyCommitment | null>(null)
  const [contextualOpt, setContextualOpt] = useState<ContextualOpt | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const toggleFormatPref = (format: FormatPreference) => {
    setFormatPrefs((prev) =>
      prev.includes(format) ? prev.filter((f) => f !== format) : [...prev, format]
    )
  }

  const handleSubmit = async () => {
    if (!teachingTone || !sessionLength || !weeklyCommitment || !contextualOpt) {
      return
    }

    if (!userId || userId.trim() === '') {
      alert('Error: User ID is missing')
      return
    }

    setIsSubmitting(true)
    try {
      await createProfile({
        user_id: userId,
        style_dna: {
          format_pref: formatPrefs.length > 0 ? formatPrefs.join(',') : 'text',
          tone: teachingTone,
          uses_emoji: false,
          prefers_diagrams: formatPrefs.includes('diagram'),
        },
        calendar_context: {
          commute_times: contextualOpt !== 'no' ? ['morning', 'evening'] : null,
          work_hours: '9-17',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
      })
      onComplete()
    } catch (error: any) {
      console.error('Failed to create profile:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to save profile. Please try again.'
      alert(`Error: ${errorMessage}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  const canProceedStep1 = formatPrefs.length > 0 && teachingTone !== null
  const canProceedStep2 = sessionLength !== null && weeklyCommitment !== null && contextualOpt !== null

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Sidebar - Progress */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col p-6">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold">S</span>
            </div>
            <span className="text-xl font-bold text-gray-900">StudySync AI</span>
          </div>
        </div>

        <div className="flex-1 space-y-6">
          {/* Step 1 */}
          <div className="flex items-start gap-3">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                step >= 1 ? 'bg-blue-600' : 'bg-gray-200'
              )}
            >
              {step > 1 ? (
                <Check className="w-5 h-5 text-white" />
              ) : (
                <span className={cn('text-sm font-medium', step === 1 ? 'text-white' : 'text-gray-500')}>
                  1
                </span>
              )}
            </div>
            <div>
              <p className={cn('font-medium', step === 1 ? 'text-blue-600' : 'text-gray-500')}>
                Learning Style
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="flex items-start gap-3">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                step >= 2 ? 'bg-blue-600' : 'bg-gray-200'
              )}
            >
              <span className={cn('text-sm font-medium', step === 2 ? 'text-white' : 'text-gray-500')}>
                2
              </span>
            </div>
            <div>
              <p className={cn('font-medium', step === 2 ? 'text-blue-600' : 'text-gray-500')}>
                Scheduling
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="flex items-start gap-3">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                step >= 3 ? 'bg-blue-600' : 'bg-gray-200'
              )}
            >
              <span className={cn('text-sm font-medium', step === 3 ? 'text-white' : 'text-gray-500')}>
                3
              </span>
            </div>
            <div>
              <p className={cn('font-medium', step === 3 ? 'text-blue-600' : 'text-gray-500')}>
                Integrations
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-white text-xs">💡</span>
            </div>
            <p className="text-sm text-gray-700">
              Defining your DNA helps us tailor content to your brain. We adapt to how you learn best.
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-12 max-w-4xl mx-auto">
        {step === 1 && (
          <div className="space-y-8">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Let's map your Learning DNA
              </h1>
              <p className="text-lg text-gray-600">Define your Cognitive Profile to get started.</p>
            </div>

            {/* Format Preference */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <h2 className="text-xl font-semibold text-gray-900">Format Preference</h2>
                <span className="text-sm text-gray-500">MULTI-SELECT</span>
              </div>
              <p className="text-gray-600 mb-4">Select the formats you absorb best.</p>
              <div className="grid grid-cols-4 gap-4">
                {[
                  { id: 'text' as FormatPreference, label: 'Text', icon: FileText },
                  { id: 'podcast' as FormatPreference, label: 'Podcast', icon: Headphones },
                  { id: 'diagram' as FormatPreference, label: 'Diagram', icon: ImageIcon },
                  { id: 'video' as FormatPreference, label: 'Video', icon: Video },
                ].map((format) => {
                  const isSelected = formatPrefs.includes(format.id)
                  return (
                    <button
                      key={format.id}
                      onClick={() => toggleFormatPref(format.id)}
                      className={cn(
                        'p-6 border-2 rounded-lg transition-all text-center',
                        isSelected
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <div className="relative">
                        {isSelected && (
                          <Check className="w-5 h-5 text-blue-600 absolute -top-2 -right-2" />
                        )}
                        <format.icon className="w-8 h-8 mx-auto mb-2 text-gray-700" />
                        <p className="font-medium text-gray-900">{format.label}</p>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Teaching Tone */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Teaching Tone</h2>
              <div className="grid grid-cols-3 gap-4">
                {[
                  {
                    id: 'eli5' as TeachingTone,
                    label: 'ELI5',
                    description: 'Simple, analogy-based explanations suitable for beginners.',
                  },
                  {
                    id: 'socratic' as TeachingTone,
                    label: 'Socratic',
                    description: 'Question-based learning that guides you to the answer.',
                  },
                  {
                    id: 'academic' as TeachingTone,
                    label: 'Academic',
                    description: 'Dense, formal, and structured for in-depth mastery.',
                  },
                ].map((tone) => {
                  const isSelected = teachingTone === tone.id
                  return (
                    <button
                      key={tone.id}
                      onClick={() => setTeachingTone(tone.id)}
                      className={cn(
                        'p-6 border-2 rounded-lg text-left transition-all',
                        isSelected
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={cn(
                            'w-5 h-5 rounded-full border-2 flex-shrink-0 mt-0.5',
                            isSelected ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                          )}
                        >
                          {isSelected && <div className="w-full h-full rounded-full bg-white scale-50" />}
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 mb-1">{tone.label}</h3>
                          <p className="text-sm text-gray-600">{tone.description}</p>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Qualitative Sample */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Qualitative Sample</h2>
              <p className="text-gray-600 mb-4">
                Upload a PDF or text file of a topic you learned successfully.
              </p>
              <div
                className={cn(
                  'border-2 border-dashed rounded-lg p-12 text-center transition-colors',
                  qualitativeSample
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                )}
              >
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".pdf,.txt,.md"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) setQualitativeSample(file)
                  }}
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-blue-600 font-medium mb-2">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-sm text-gray-500">PDF, TXT, or MD (max. 10MB)</p>
                  {qualitativeSample && (
                    <p className="text-sm text-blue-600 mt-2">{qualitativeSample.name}</p>
                  )}
                </label>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setStep(2)}
                disabled={!canProceedStep1}
                className={cn(
                  'px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors',
                  canProceedStep1
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                )}
              >
                Continue
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-8">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Scheduling Preferences</h1>
              <p className="text-lg text-gray-600">Configure how learning fits into your schedule.</p>
            </div>

            {/* Default Session Length */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Default Session Length</h2>
              <div className="grid grid-cols-5 gap-4">
                {['<10', '10-15', '30', '60', '120'].map((length) => (
                  <button
                    key={length}
                    onClick={() => setSessionLength(length as SessionLength)}
                    className={cn(
                      'p-4 border-2 rounded-lg text-center transition-all',
                      sessionLength === length
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    )}
                  >
                    <p className="font-medium text-gray-900">
                      {length === '120' ? '2 hours' : length === '60' ? '1 hour' : length === '30' ? '30 min' : length === '10-15' ? '10-15 min' : '<10 min'}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Weekly Commitment */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Weekly Commitment</h2>
              <div className="space-y-3">
                {[
                  {
                    id: 'infrequent' as WeeklyCommitment,
                    label: 'Infrequent Deep Dives',
                    description: 'Longer sessions, less frequently',
                  },
                  {
                    id: 'frequent' as WeeklyCommitment,
                    label: 'Frequent Short Bursts',
                    description: 'Many short sessions throughout the week',
                  },
                  {
                    id: 'consistent' as WeeklyCommitment,
                    label: 'Consistent Pace',
                    description: 'Regular, moderate-length sessions',
                  },
                ].map((commitment) => {
                  const isSelected = weeklyCommitment === commitment.id
                  return (
                    <button
                      key={commitment.id}
                      onClick={() => setWeeklyCommitment(commitment.id)}
                      className={cn(
                        'w-full p-4 border-2 rounded-lg text-left transition-all',
                        isSelected
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={cn(
                            'w-5 h-5 rounded-full border-2 flex-shrink-0 mt-0.5',
                            isSelected ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                          )}
                        >
                          {isSelected && <div className="w-full h-full rounded-full bg-white scale-50" />}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{commitment.label}</h3>
                          <p className="text-sm text-gray-600">{commitment.description}</p>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Contextual Optimization */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Contextual Optimization</h2>
              <p className="text-gray-600 mb-4">
                Can we book a session during a "busy" event (e.g., commute)?
              </p>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { id: 'yes-audio' as ContextualOpt, label: 'Yes - Audio', description: 'Audio content during commute' },
                  { id: 'yes-visual' as ContextualOpt, label: 'Yes - Visual', description: 'Visual content when possible' },
                  { id: 'no' as ContextualOpt, label: 'No', description: 'Only during dedicated time slots' },
                ].map((opt) => {
                  const isSelected = contextualOpt === opt.id
                  return (
                    <button
                      key={opt.id}
                      onClick={() => setContextualOpt(opt.id)}
                      className={cn(
                        'p-4 border-2 rounded-lg text-center transition-all',
                        isSelected
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <h3 className="font-semibold text-gray-900 mb-1">{opt.label}</h3>
                      <p className="text-sm text-gray-600">{opt.description}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="px-6 py-3 rounded-lg font-medium text-gray-700 hover:bg-gray-100 transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={!canProceedStep2 || isSubmitting}
                className={cn(
                  'px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors',
                  canProceedStep2 && !isSubmitting
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                )}
              >
                {isSubmitting ? 'Saving...' : 'Complete Setup'}
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
