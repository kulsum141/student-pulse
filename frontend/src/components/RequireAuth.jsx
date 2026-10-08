import { Navigate, Outlet, useLocation } from 'react-router-dom'
import LoadingState from './LoadingState'
import { useAuth } from '../hooks/useAuth'

export default function RequireAuth() {
  const { student, loading } = useAuth()
  const location = useLocation()

  if (loading) return <LoadingState text="Restoring your session..." />
  if (!student) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}