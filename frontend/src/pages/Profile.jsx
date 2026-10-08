import { useEffect, useState } from 'react'
import { Pencil, Save, X } from 'lucide-react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { profileApi, STUDENT_ID } from '../api'
import styles from './Profile.module.css'

export default function Profile() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [draft, setDraft] = useState(null)

  useEffect(() => {
    profileApi.get(STUDENT_ID)
      .then(({ data }) => {
        setProfile(data)
        setDraft({
          name: data.name || '',
          email: data.email || '',
          college: data.college || '',
          branch: data.branch || data.department || '',
          academic_year: data.academic_year || data.year_of_study || 1,
          semester: data.semester || 1,
          gpa: data.gpa ?? data.cgpa ?? '',
          career_goal: data.career_goal || '',
          skills: (data.skills || []).join(', '),
          interests: (data.interests || []).join(', '),
          preferred_opportunity_types: (data.preferred_opportunity_types || []).join(', '),
          preferred_location: data.preferred_location || '',
          open_to_remote: data.open_to_remote ?? true,
        })
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load profile.')
        setLoading(false)
      })
  }, [])

  if (loading) return <LoadingState text="Loading profile..." />
  if (error) return <ErrorState message={error} />

  const updateField = event => setDraft(current => ({ ...current, [event.target.name]: event.target.value }))
  const updateProfile = async event => {
    event.preventDefault()
    setSaving(true)
    setError('')
    setMessage('')
    const splitList = value => value.split(',').map(item => item.trim()).filter(Boolean)
    try {
      const { data } = await profileApi.update({
        ...draft,
        academic_year: Number(draft.academic_year),
        semester: Number(draft.semester),
        gpa: draft.gpa === '' ? null : Number(draft.gpa),
        skills: splitList(draft.skills),
        interests: splitList(draft.interests),
        preferred_opportunity_types: splitList(draft.preferred_opportunity_types),
      })
      setProfile(data)
      setDraft(current => ({ ...current, ...data, skills: data.skills.join(', '), interests: data.interests.join(', '), preferred_opportunity_types: data.preferred_opportunity_types.join(', ') }))
      setEditing(false)
      setMessage('Profile updated.')
    } catch (requestError) {
      setError(requestError.message || 'Unable to update your profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeader title="Profile" subtitle="Track your academic profile and growth goals" />

      <div className={styles.topGrid}>
        <Card accent="lavender" className={styles.profileCard}>
          <div className={styles.avatar}>{profile.name?.charAt(0) || 'S'}</div>
          <div>
            <h2>{profile.name}</h2>
            <p>{profile.branch || profile.department}</p>
            <small>{profile.email}</small>
          </div>
        </Card>

        <Card accent="mint" className={styles.quickCard}>
          <span>Career goal</span>
          <strong>{profile.career_goal}</strong>
            <small>GPA: {profile.gpa ?? profile.cgpa ?? 'Not provided'}</small>
        </Card>
      </div>

      <div className={styles.infoGrid}>
        <Card accent="peach" className={styles.infoCard}>
          <h3>Education</h3>
          <ul>
            <li><strong>Year:</strong> {profile.year_of_study}</li>
            <li><strong>Semester:</strong> {profile.semester || 'Not provided'}</li>
            <li><strong>College:</strong> {profile.college || 'Not provided'}</li>
            <li><strong>Preferred location:</strong> {profile.preferred_location}</li>
            <li><strong>Open to remote:</strong> {profile.open_to_remote ? 'Yes' : 'No'}</li>
          </ul>
        </Card>

        <Card accent="sky" className={styles.infoCard}>
          <h3>Skills</h3>
          <div className={styles.tagList}>
            {profile.skills.map(skill => <span key={skill}>{skill}</span>)}
          </div>
        </Card>

        <Card accent="pink" className={styles.infoCard}>
          <h3>Interests</h3>
          <div className={styles.tagList}>
            {profile.interests.map(item => <span key={item}>{item}</span>)}
          </div>
        </Card>
      </div>

      <div className={styles.editActions}>
        <button type="button" className={styles.editButton} onClick={() => setEditing(value => !value)}>
          {editing ? <X size={15} /> : <Pencil size={15} />}{editing ? 'Cancel editing' : 'Edit profile'}
        </button>
        {message && <span role="status">{message}</span>}
      </div>
      {error && <ErrorState message={error} />}
      {editing && draft && (
        <Card accent="lavender" className={styles.editCard}>
          <h3>Edit student profile</h3>
          <form className={styles.editForm} onSubmit={updateProfile}>
            <label>Name<input name="name" required minLength="2" maxLength="100" value={draft.name} onChange={updateField} /></label>
            <label>Email<input name="email" type="email" required value={draft.email} onChange={updateField} /></label>
            <label>College<input name="college" required minLength="2" value={draft.college} onChange={updateField} /></label>
            <label>Branch<input name="branch" required minLength="2" value={draft.branch} onChange={updateField} /></label>
            <label>Academic year<input name="academic_year" type="number" min="1" max="8" required value={draft.academic_year} onChange={updateField} /></label>
            <label>Semester<input name="semester" type="number" min="1" max="16" required value={draft.semester} onChange={updateField} /></label>
            <label>GPA<input name="gpa" type="number" min="0" max="10" step="0.01" value={draft.gpa} onChange={updateField} /></label>
            <label>Career goal<input name="career_goal" maxLength="120" value={draft.career_goal} onChange={updateField} /></label>
            <label>Skills, comma-separated<input name="skills" value={draft.skills} onChange={updateField} /></label>
            <label>Interests, comma-separated<input name="interests" value={draft.interests} onChange={updateField} /></label>
            <label>Preferred opportunity types<input name="preferred_opportunity_types" value={draft.preferred_opportunity_types} onChange={updateField} /></label>
            <label>Preferred location<input name="preferred_location" value={draft.preferred_location} onChange={updateField} /></label>
            <label className={styles.remoteToggle}><input name="open_to_remote" type="checkbox" checked={Boolean(draft.open_to_remote)} onChange={event => setDraft(current => ({ ...current, open_to_remote: event.target.checked }))} />Open to remote</label>
            <button className={styles.editButton} type="submit" disabled={saving}>{saving ? 'Saving...' : <><Save size={15} />Save profile</>}</button>
          </form>
        </Card>
      )}
    </>
  )
}
