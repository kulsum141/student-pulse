import { useEffect, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './Profile.module.css'

export default function Profile() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    mockApi.getStudentProfile()
      .then(({ data }) => {
        setProfile(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load profile.')
        setLoading(false)
      })
  }, [])

  if (loading) return <LoadingState text="Loading profile..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader title="Profile" subtitle="Track your academic profile and growth goals" />

      <div className={styles.topGrid}>
        <Card accent="lavender" className={styles.profileCard}>
          <div className={styles.avatar}>K</div>
          <div>
            <h2>{profile.name}</h2>
            <p>{profile.department}</p>
            <small>{profile.email}</small>
          </div>
        </Card>

        <Card accent="mint" className={styles.quickCard}>
          <span>Career goal</span>
          <strong>{profile.career_goal}</strong>
          <small>CGPA: {profile.cgpa}</small>
        </Card>
      </div>

      <div className={styles.infoGrid}>
        <Card accent="peach" className={styles.infoCard}>
          <h3>Education</h3>
          <ul>
            <li><strong>Year:</strong> {profile.year_of_study}</li>
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
    </>
  )
}
