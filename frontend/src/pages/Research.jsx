import { useEffect, useState } from 'react'
import Card from '../components/Card'
import OpportunityCard from '../components/OpportunityCard'
import PageHeader from '../components/PageHeader'
import SectionHeader from '../components/SectionHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './OpportunityPage.module.css'

export default function Research() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    mockApi.getResearch()
      .then(({ data }) => {
        setItems(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load research papers.')
        setLoading(false)
      })
  }, [])

  const filtered = items.filter(item => {
    const text = `${item.title} ${item.organization} ${item.domain}`.toLowerCase()
    return text.includes(query.toLowerCase())
  })

  if (loading) return <LoadingState text="Loading research papers..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader title="Research Papers" subtitle="Discover ideas and reading material relevant to your current goals" />

      <Card className={styles.toolbar} accent="sky">
        <div className={styles.searchWrap}>
          <span>🔎</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search topics, domains, authors" />
        </div>
        <div className={styles.filterRow}>
          <select defaultValue="all"><option value="all">All domains</option></select>
          <select defaultValue="all"><option value="all">Difficulty</option></select>
          <select defaultValue="all"><option value="all">Latest</option></select>
        </div>
      </Card>

      <SectionHeader title="Suggested reading" subtitle={`${filtered.length} papers reviewed for you`} />
      <div className={styles.grid}>
        {filtered.map(item => (
          <OpportunityCard
            key={item.id}
            type="paper"
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.date}
            deadline={item.difficulty}
            match={item.match}
            skills={[item.domain, 'Research']}
            description={`Published: ${item.date}`}
            actionLabel="Read"
          />
        ))}
      </div>
    </>
  )
}
