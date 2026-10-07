import { useEffect, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import ProgressBar from '../components/ProgressBar'
import RoadmapNode from '../components/RoadmapNode'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './Roadmap.module.css'

export default function Roadmap() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    mockApi.getRoadmap()
      .then(({ data }) => {
        setData(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load roadmap.')
        setLoading(false)
      })
  }, [])

  if (loading) return <LoadingState text="Preparing your roadmap..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader title="Career Roadmap" subtitle={`Goal: ${data.careerGoal}`} />

      <Card className={styles.heroCard} accent="mint">
        <div>
          <p className={styles.kicker}>Roadmap progress</p>
          <h2>{data.careerGoal}</h2>
        </div>
        <div className={styles.progressBox}>
          <strong>{data.progress}%</strong>
          <span>completed</span>
        </div>
      </Card>

      <div className={styles.progressWrap}>
        <ProgressBar value={data.progress} label="Overall readiness" color="mint" />
      </div>

      <div className={styles.grid}>
        {data.steps.map(step => (
          <RoadmapNode key={step.title} item={step} />
        ))}
      </div>
    </>
  )
}
