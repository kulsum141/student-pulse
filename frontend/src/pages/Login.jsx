import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import LoadingState from '../components/LoadingState'
import styles from './Auth.module.css'

export default function Login() {
  const { student, loading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (loading) return <LoadingState text="Restoring your session..." />
  if (student) return <Navigate to="/dashboard" replace />

  const submit = async event => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await login({ email, password })
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (requestError) {
      setError(requestError.message || 'Unable to sign in. Check your details and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.panel} aria-labelledby="login-title">
        <div className={styles.brand}><span className={styles.brandMark}><Sparkles size={17} /></span>Student Pulse</div>
        <h1 id="login-title" className={styles.title}>Welcome back</h1>
        <p className={styles.subtitle}>Sign in to continue your learning and career journey.</p>
        <form className={styles.form} onSubmit={submit}>
          <div className={styles.field}>
            <label htmlFor="login-email">Email</label>
            <input id="login-email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={event => setEmail(event.target.value)} />
          </div>
          <div className={styles.field}>
            <label htmlFor="login-password">Password</label>
            <input id="login-password" type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={event => setPassword(event.target.value)} />
          </div>
          {error && <p className={styles.error} role="alert">{error}</p>}
          <button className={styles.submit} type="submit" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'} {!submitting && <ArrowRight size={15} />}
          </button>
        </form>
        <p className={styles.footer}>New to Student Pulse? <Link to="/register">Create an account</Link></p>
      </section>
    </main>
  )
}