import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import Onboarding from './pages/Onboarding';
import LearningPlan from './pages/LearningPlan';
import KnowledgeBank from './pages/KnowledgeBank';
import NoteDetail from './pages/NoteDetail';
import StudySession from './pages/StudySession';
import PlanDetail from './pages/PlanDetail';
import SignUp from './pages/SignUp';
import ContentDetail from './pages/ContentDetail';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = localStorage.getItem('isAuthenticated');
  const hasOnboarded = localStorage.getItem('hasOnboarded');
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/signup" state={{ from: location }} replace />;
  }

  if (!hasOnboarded) {
    return <Navigate to="/onboarding" state={{ from: location }} replace />;
  }

  return children;
}

function RequireAuthOnly({ children }: { children: React.ReactNode }) {
  const isAuthenticated = localStorage.getItem('isAuthenticated');
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/signup" state={{ from: location }} replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth Pages (No Layout) */}
        <Route path="/signup" element={<SignUp />} />

        {/* Protected App Pages (With Layout) */}
        <Route path="/*" element={
          <Layout>
            <Routes>
              <Route path="/" element={
                <RequireAuth>
                  <KnowledgeBank />
                </RequireAuth>
              } />
              <Route path="/onboarding" element={
                <RequireAuthOnly>
                  <Onboarding />
                </RequireAuthOnly>
              } />
              <Route path="/dna" element={<Onboarding />} />
              <Route path="/plan" element={<LearningPlan />} />
              <Route path="/plans/:id" element={<PlanDetail />} />
              <Route path="/bank" element={<Navigate to="/" replace />} />
              <Route path="/notes/:id" element={<NoteDetail />} />
              <Route path="/materials/:id" element={<Navigate to="/" replace />} />
              <Route path="/content/:id" element={<ContentDetail />} />
              <Route path="/session/:sessionId" element={<StudySession />} />
            </Routes>
          </Layout>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
