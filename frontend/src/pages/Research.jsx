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

export default function Research() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    opportunitiesApi.research({ student_id: STUDENT_ID, top_k: 25 })
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
      {filtered.length > 0 ? <div className={styles.grid}>
        {filtered.map(item => (
          <OpportunityCard
            key={item.id}
            type="paper"
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.publishedYear ? `Published ${item.publishedYear}` : ''}
            deadline={null}
            match={item.match}
            skills={item.skills}
            description={item.description}
            actionLabel="Read"
            onSave={() => recommendationsApi.save(STUDENT_ID, item)}
          />
        ))}
      </div> : <EmptyState title="No research papers found" description="Try another search to discover more reading." />}
    </>
  )
}
