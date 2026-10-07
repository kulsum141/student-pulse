import { useEffect, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import ProgressBar from '../components/ProgressBar'
import SkillCard from '../components/SkillCard'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './SkillGap.module.css'

export default function SkillGap() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    mockApi.getSkillGap()
      .then(({ data }) => {
        setData(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load skill gap information.')
        setLoading(false)
      })
  }, [])

  if (loading) return <LoadingState text="Analyzing your skill gap..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader title="Skill Gap" subtitle={`Target career: ${data.targetCareer}`} />

      <div className={styles.topGrid}>
        <Card accent="lavender" className={styles.summaryCard}>
          <div className={styles.summaryHead}>
            <span>Readiness</span>
            <strong>{data.readiness}%</strong>
          </div>
          <ProgressBar value={data.readiness} label="Current readiness" color="lavender" />
        </Card>

        <Card accent="pink" className={styles.summaryCard}>
          <div className={styles.summaryHead}>
            <span>Focus area</span>
            <strong>{data.missingSkills[0]}</strong>
          </div>
          <p className={styles.summaryText}>Most important skill gap to close next.</p>
        </Card>
      </div>

      <div className={styles.columns}>
        <div className={styles.column}>
          <h3>Current skills</h3>
          <div className={styles.skillGrid}>
            {data.currentSkills.map(skill => (
              <SkillCard key={skill} title={skill} subtitle="Strong match" value={88} tone="mint" />
            ))}
          </div>
        </div>

        <div className={styles.column}>
          <h3>Missing / weak skills</h3>
          <div className={styles.skillGrid}>
            {data.missingSkills.map(skill => (
              <SkillCard key={skill} title={skill} subtitle="Needs attention" value={45} tone="peach" />
            ))}
          </div>
        </div>
      </div>

      <Card accent="sky" className={styles.learningCard}>
        <h3>Recommended learning areas</h3>
        <div className={styles.learningList}>
          {data.recommendedSkills.map(item => (
            <div key={item} className={styles.learningItem}>{item}</div>
          ))}
        </div>
      </Card>
    </>
  )
}
