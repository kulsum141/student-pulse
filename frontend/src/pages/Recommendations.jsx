import { useEffect, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import OpportunityCard from '../components/OpportunityCard'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './Recommendations.module.css'

export default function Recommendations() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    mockApi.getDashboardData()
      .then(({ data }) => {
        const merged = [
          ...data.recommendations.opportunities.map(item => ({ ...item, category: 'Internship' })),
          ...data.recommendations.hackathons.map(item => ({ ...item, category: 'Hackathon' })),
          ...data.recommendations.papers.map(item => ({ ...item, category: 'Research' })),
        ]

        setItems(merged)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load recommendations.')
        setLoading(false)
      })
  }, [])

  if (loading) return <LoadingState text="Loading recommendations..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader
        title="Recommendations"
        subtitle="AI-curated opportunities matched to your profile and interests"
      />

      <div className={styles.filters}>
        <span className={styles.filterChip}>All</span>
        <span className={styles.filterChip}>Internships</span>
        <span className={styles.filterChip}>Hackathons</span>
        <span className={styles.filterChip}>Research</span>
      </div>

      <div className={styles.grid}>
        {items.map(item => (
          <OpportunityCard
            key={item.id}
            type={item.category === 'Hackathon' ? 'hackathon' : item.category === 'Research' ? 'paper' : 'internship'}
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.location || 'Remote'}
            deadline={item.deadline || 'Flexible'}
            match={item.match}
            skills={item.skills || ['Research', 'Python']}
            description={item.description}
            actionLabel={item.category === 'Research' ? 'Read' : 'View'}
            secondaryLabel="Save"
          />
        ))}
      </div>

      <Card accent="lavender" className={styles.summaryCard}>
        <h3>AI recommendation summary</h3>
        <p>
          Your strongest matches are focused on cloud engineering, full-stack product development,
          and applied AI research. Continue building your AWS and Python fundamentals to improve future fit.
        </p>
      </Card>
    </>
  )
}
