import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import Dashboard from './pages/Dashboard'
import Roadmap from './pages/Roadmap'
import SkillGap from './pages/SkillGap'
import Internships from './pages/Internships'
import Hackathons from './pages/Hackathons'
import Research from './pages/Research'
import Recommendations from './pages/Recommendations'
import Assistant from './pages/Assistant'
import Saved from './pages/Saved'
import Profile from './pages/Profile'
import Customize from './pages/Customize'
import Login from './pages/Login'
import Register from './pages/Register'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<RequireAuth />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="opportunities" element={<Recommendations />} />
              <Route path="internships" element={<Internships />} />
              <Route path="hackathons" element={<Hackathons />} />
              <Route path="research" element={<Research />} />
              <Route path="recommendations" element={<Recommendations />} />
              <Route path="roadmap" element={<Roadmap />} />
              <Route path="skill-gap" element={<SkillGap />} />
              <Route path="assistant" element={<Assistant />} />
              <Route path="saved" element={<Saved />} />
              <Route path="profile" element={<Profile />} />
              <Route path="customize" element={<Customize />} />
              <Route path="settings" element={<Customize />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
