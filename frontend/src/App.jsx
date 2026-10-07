import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Roadmap from './pages/Roadmap'
import SkillGap from './pages/SkillGap'
import Internships from './pages/Internships'
import Hackathons from './pages/Hackathons'
import Research from './pages/Research'
import Assistant from './pages/Assistant'
import Profile from './pages/Profile'
import Customize from './pages/Customize'
import './index.css'

// Default student for demo — S001 Aarav Sharma
export const STUDENT_ID = 'S001'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"   element={<Dashboard />} />
          <Route path="roadmap"     element={<Roadmap />} />
          <Route path="skill-gap"   element={<SkillGap />} />
          <Route path="internships" element={<Internships />} />
          <Route path="hackathons"  element={<Hackathons />} />
          <Route path="research"    element={<Research />} />
          <Route path="assistant"   element={<Assistant />} />
          <Route path="profile"     element={<Profile />} />
          <Route path="customize"   element={<Customize />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
