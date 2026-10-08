import { useEffect, useState } from 'react'
import Card from '../components/Card'
import OpportunityCard from '../components/OpportunityCard'
import PageHeader from '../components/PageHeader'
import SectionHeader from '../components/SectionHeader'
import EmptyState from '../components/EmptyState'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { opportunitiesApi, recommendationsApi, STUDENT_ID } from '../api'
import styles from './OpportunityPage.module.css'

export default function Hackathons() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    opportunitiesApi.hackathons({ student_id: STUDENT_ID, top_k: 25 })
      .then(({ data }) => {
        setItems(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load hackathons.')
        setLoading(false)
      })
  }, [])

  const filtered = items.filter(item => {
    const text = `${item.title} ${item.organization} ${item.domain}`.toLowerCase()
    return text.includes(query.toLowerCase())
  })

  if (loading) return <LoadingState text="Loading hackathons..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader title="Hackathons" subtitle="Compete, learn, and build with top teams and communities" />

      <Card className={styles.toolbar} accent="pink">
        <div className={styles.searchWrap}>
          <span>🔎</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search hackathons, domains, organizers" />
        </div>
        <div className={styles.filterRow}>
          <select defaultValue="all"><option value="all">Technology</option></select>
          <select defaultValue="all"><option value="all">Mode</option></select>
          <select defaultValue="all"><option value="all">Difficulty</option></select>
        </div>
      </Card>

      <SectionHeader title="Upcoming events" subtitle={`${filtered.length} hackathon opportunities`} />
      {filtered.length > 0 ? <div className={styles.grid}>
        {filtered.map(item => (
          <OpportunityCard
            key={item.id}
            type="hackathon"
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.location}
            deadline={item.deadline}
            match={item.match}
            skills={item.skills}
            description={item.description || `${item.difficulty || 'Difficulty not provided'} · Team size ${item.teamSize || 'not provided'}`}
            actionLabel="Register"
            onSave={() => recommendationsApi.save(STUDENT_ID, item)}
          />
        ))}
      </div> : <EmptyState title="No hackathons found" description="Try a different search to see upcoming events." />}
    </>
  )
}
