import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Onboarding from './pages/Onboarding';
import LearningPlan from './pages/LearningPlan';
import KnowledgeBank from './pages/KnowledgeBank';
import NoteDetail from './pages/NoteDetail';
import StudySession from './pages/StudySession';
import PlanDetail from './pages/PlanDetail';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dna" element={<Onboarding />} />
          <Route path="/plan" element={<LearningPlan />} />
          <Route path="/plans/:id" element={<PlanDetail />} />
          <Route path="/bank" element={<KnowledgeBank />} />
          <Route path="/notes/:id" element={<NoteDetail />} />
          <Route path="/session/:sessionId" element={<StudySession />} /> {/* Ensuring this exists too if it was missed, based on StudySession usage */}
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
