import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Calendar, Clock, Gauge, Headphones, BookOpen, CheckCircle, X } from 'lucide-react'
import { cn } from '../utils/cn'
import { getNotifications } from '../api/client'

interface DashboardProps {
  userId: string
}

interface LearningPlan {
  id: string
  title: string
  duration: string
  timeline: string
  intensity: string
  formatBreakdown: {
    audio: number
    deepDives: number
  }
  timelineItems: Array<{
    week: string
    topic: string
  }>
}

export default function Dashboard({ userId }: DashboardProps) {
  const navigate = useNavigate()
  const [showProposal, setShowProposal] = useState(false)
  const [plan, setPlan] = useState<LearningPlan | null>(null)

  useEffect(() => {
    // Check for new proposals/notifications
    checkForProposals()
  }, [userId])

  const checkForProposals = async () => {
    try {
      const notifications = await getNotifications(userId, true)
      // If there's a proposal notification, show the modal
      // For demo purposes, we'll show a sample proposal
      if (notifications.notifications && notifications.notifications.length > 0) {
        setShowProposal(true)
        setPlan({
          id: 'plan_1',
          title: "Rust Basics",
          duration: "5 Hours",
          timeline: "Oct 10 - Oct 24",
          intensity: "Moderate Pace",
          formatBreakdown: {
            audio: 2,
            deepDives: 3,
          },
          timelineItems: [
            { week: "WEEK 1", topic: "Core Syntax" },
            { week: "WEEK 1.5", topic: "Type System" },
            { week: "WEEK 2", topic: "Error Handling" },
            { week: "WEEK 2", topic: "Project" },
          ],
        })
      }
    } catch (error) {
      console.error('Failed to check notifications:', error)
    }
  }

  const handleApprovePlan = () => {
    // Navigate to calendar sync or show success message
    alert('Plan approved! Syncing to calendar...')
    setShowProposal(false)
    // In a real implementation, this would trigger calendar sync
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Good Morning, Learner</h1>
        <p className="text-gray-600">Welcome back to your learning journey</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Active Plans</p>
              <p className="text-2xl font-bold text-gray-900">2</p>
            </div>
            <BookOpen className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Completed Topics</p>
              <p className="text-2xl font-bold text-gray-900">12</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">This Week</p>
              <p className="text-2xl font-bold text-gray-900">5h</p>
            </div>
            <Clock className="w-8 h-8 text-purple-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Knowledge Items</p>
              <p className="text-2xl font-bold text-gray-900">24</p>
            </div>
            <BookOpen className="w-8 h-8 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <button
          onClick={() => navigate('/knowledge-bank')}
          className="bg-white rounded-lg border border-gray-200 p-6 text-left hover:shadow-lg transition-shadow"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload New Content</h3>
          <p className="text-gray-600">Add files to your knowledge bank</p>
        </button>
        <button
          onClick={() => setShowProposal(true)}
          className="bg-white rounded-lg border border-gray-200 p-6 text-left hover:shadow-lg transition-shadow"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-2">View Learning Plans</h3>
          <p className="text-gray-600">See your active and proposed plans</p>
        </button>
      </div>

      {/* AI Proposal Modal */}
      {showProposal && plan && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-blue-600" />
                  <h2 className="text-xl font-bold text-gray-900">AI PROPOSAL</h2>
                </div>
                <button
                  onClick={() => setShowProposal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mt-4">
                I've designed a 2-week plan for {plan.title}
              </h3>
              <p className="text-gray-600 mt-2">
                Based on the 3 articles and 1 video you saved yesterday.
              </p>
            </div>

            <div className="p-6">
              {/* Plan Summary Cards */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-5 h-5 text-gray-600" />
                    <p className="text-sm text-gray-600">Total Duration</p>
                  </div>
                  <p className="text-xl font-bold text-gray-900">{plan.duration}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-5 h-5 text-gray-600" />
                    <p className="text-sm text-gray-600">Timeline</p>
                  </div>
                  <p className="text-xl font-bold text-gray-900">{plan.timeline}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Gauge className="w-5 h-5 text-gray-600" />
                    <p className="text-sm text-gray-600">Intensity</p>
                  </div>
                  <p className="text-xl font-bold text-gray-900">{plan.intensity}</p>
                </div>
              </div>

              {/* Format Breakdown */}
              <div className="mb-6">
                <h4 className="font-semibold text-gray-900 mb-3">Format Breakdown</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                    <Headphones className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="font-medium text-gray-900">
                        {plan.formatBreakdown.audio} Audio Sessions
                      </p>
                      <p className="text-sm text-gray-600">Optimized for your commute</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                    <BookOpen className="w-5 h-5 text-purple-600" />
                    <div>
                      <p className="font-medium text-gray-900">
                        {plan.formatBreakdown.deepDives} Deep Dives
                      </p>
                      <p className="text-sm text-gray-600">Interactive text & code review</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="mb-6">
                <h4 className="font-semibold text-gray-900 mb-3">Proposed Timeline</h4>
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-blue-200"></div>
                  <div className="space-y-4 pl-8">
                    {plan.timelineItems.map((item, index) => (
                      <div key={index} className="relative">
                        <div className="absolute -left-10 w-4 h-4 bg-blue-600 rounded-full border-4 border-white"></div>
                        <div>
                          <p className="font-medium text-gray-900">{item.week}</p>
                          <p className="text-sm text-gray-600">{item.topic}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                  Customize Plan
                </button>
                <button className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                  Regenerate
                </button>
                <button
                  onClick={handleApprovePlan}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                >
                  <Calendar className="w-5 h-5" />
                  Approve & Sync
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
