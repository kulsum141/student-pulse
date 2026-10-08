import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import LoadingState from '../components/LoadingState'
import styles from './Auth.module.css'

const initialForm = {
  name: '', email: '', password: '', college: '', branch: '',
  academicYear: '1', semester: '1', gpa: '', careerGoal: '',
  skills: '', interests: '', opportunityTypes: 'Internship',
}

export default function Register() {
  const { student, loading, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (loading) return <LoadingState text="Checking your session..." />
  if (student) return <Navigate to="/dashboard" replace />

  const change = event => setForm(current => ({ ...current, [event.target.name]: event.target.value }))
  const list = value => value.split(',').map(item => item.trim()).filter(Boolean)

  const submit = async event => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await register({
        name: form.name,
        email: form.email,
        password: form.password,
        college: form.college,
        branch: form.branch,
        academic_year: Number(form.academicYear),
        semester: Number(form.semester),
        gpa: form.gpa === '' ? null : Number(form.gpa),
        career_goal: form.careerGoal || null,
        skills: list(form.skills),
        interests: list(form.interests),
        preferred_opportunity_types: list(form.opportunityTypes),
      })
      navigate('/dashboard', { replace: true })
    } catch (requestError) {
      setError(requestError.message || 'Unable to create your account. Please check the form.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.panel} aria-labelledby="register-title">
        <div className={styles.brand}><span className={styles.brandMark}><Sparkles size={17} /></span>Student Pulse</div>
        <h1 id="register-title" className={styles.title}>Create your student account</h1>
        <p className={styles.subtitle}>Your profile will carry across your dashboard, roadmap, and recommendations.</p>
        <form className={styles.form} onSubmit={submit}>
          <div className={styles.fieldGrid}>
            <div className={styles.field}><label htmlFor="register-name">Name</label><input id="register-name" name="name" autoComplete="name" required minLength={2} maxLength={100} value={form.name} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-email">Email</label><input id="register-email" name="email" type="email" autoComplete="email" required maxLength={254} value={form.email} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-college">College</label><input id="register-college" name="college" required minLength={2} maxLength={160} value={form.college} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-branch">Branch</label><input id="register-branch" name="branch" required minLength={2} maxLength={120} value={form.branch} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-year">Academic year</label><input id="register-year" name="academicYear" type="number" min="1" max="8" required value={form.academicYear} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-semester">Semester</label><input id="register-semester" name="semester" type="number" min="1" max="16" required value={form.semester} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-gpa">GPA (0-10)</label><input id="register-gpa" name="gpa" type="number" min="0" max="10" step="0.01" value={form.gpa} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-goal">Career goal</label><input id="register-goal" name="careerGoal" maxLength={120} value={form.careerGoal} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-skills">Skills, comma-separated</label><input id="register-skills" name="skills" maxLength={1000} value={form.skills} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-interests">Interests, comma-separated</label><input id="register-interests" name="interests" maxLength={1000} value={form.interests} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-opportunities">Preferred opportunities</label><input id="register-opportunities" name="opportunityTypes" maxLength={300} value={form.opportunityTypes} onChange={change} /></div>
            <div className={styles.field}><label htmlFor="register-password">Password (10+ characters)</label><input id="register-password" name="password" type="password" autoComplete="new-password" required minLength={10} maxLength={128} value={form.password} onChange={change} /></div>
          </div>
          {error && <p className={styles.error} role="alert">{error}</p>}
          <button className={styles.submit} type="submit" disabled={submitting}>
            {submitting ? 'Creating account...' : 'Create account'} {!submitting && <ArrowRight size={15} />}
          </button>
        </form>
        <p className={styles.footer}>Already registered? <Link to="/login">Sign in</Link></p>
      </section>
    </main>
  )
}