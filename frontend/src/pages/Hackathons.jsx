import { useEffect, useState } from 'react'
import Card from '../components/Card'
import OpportunityCard from '../components/OpportunityCard'
import PageHeader from '../components/PageHeader'
import SectionHeader from '../components/SectionHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './OpportunityPage.module.css'

export default function Hackathons() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    mockApi.getHackathons()
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
      <div className={styles.grid}>
        {filtered.map(item => (
          <OpportunityCard
            key={item.id}
            type="hackathon"
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.mode}
            deadline={item.deadline}
            match={item.match}
            skills={[item.domain, item.difficulty]}
            description={`Team size: ${item.teamSize} • Difficulty: ${item.difficulty}`}
            actionLabel="Register"
          />
        ))}
      </div>
    </>
  )
}
