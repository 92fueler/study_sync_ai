import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Onboarding from './pages/Onboarding'
import KnowledgeBank from './pages/KnowledgeBank'
import StudySession from './pages/StudySession'
import Dashboard from './pages/Dashboard'
import Layout from './components/Layout'

function App() {
  const [userId, setUserId] = useState<string | null>(null)
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false)

  useEffect(() => {
    // Check if user has completed onboarding
    const storedUserId = localStorage.getItem('user_id')
    const onboardingComplete = localStorage.getItem('onboarding_complete') === 'true'
    
    if (storedUserId) {
      setUserId(storedUserId)
    } else {
      // Generate a temporary user ID for demo purposes
      const tempUserId = `user_${Date.now()}`
      localStorage.setItem('user_id', tempUserId)
      setUserId(tempUserId)
    }
    
    setHasCompletedOnboarding(onboardingComplete)
  }, [])

  const handleOnboardingComplete = () => {
    setHasCompletedOnboarding(true)
    localStorage.setItem('onboarding_complete', 'true')
  }

  if (!userId) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/onboarding"
          element={
            hasCompletedOnboarding ? (
              <Navigate to="/knowledge-bank" replace />
            ) : (
              <Onboarding userId={userId} onComplete={handleOnboardingComplete} />
            )
          }
        />
        <Route
          path="/"
          element={
            <Layout userId={userId}>
              <Dashboard userId={userId} />
            </Layout>
          }
        />
        <Route
          path="/knowledge-bank"
          element={
            <Layout userId={userId}>
              <KnowledgeBank userId={userId} />
            </Layout>
          }
        />
        <Route
          path="/study-session/:sessionId"
          element={<StudySession userId={userId} />}
        />
        <Route
          path="*"
          element={
            hasCompletedOnboarding ? (
              <Navigate to="/knowledge-bank" replace />
            ) : (
              <Navigate to="/onboarding" replace />
            )
          }
        />
      </Routes>
    </Router>
  )
}

export default App
