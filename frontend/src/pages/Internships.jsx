import { useEffect, useState } from 'react'
import Card from '../components/Card'
import OpportunityCard from '../components/OpportunityCard'
import PageHeader from '../components/PageHeader'
import SectionHeader from '../components/SectionHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './OpportunityPage.module.css'

export default function Internships() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    mockApi.getInternships()
      .then(({ data }) => {
        setItems(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load internships.')
        setLoading(false)
      })
  }, [])

  const filtered = items.filter(item => {
    const text = `${item.title} ${item.organization} ${item.domain}`.toLowerCase()
    return text.includes(query.toLowerCase())
  })

  if (loading) return <LoadingState text="Loading internships..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader title="Internships" subtitle="Explore roles aligned with your interests and skill profile" />

      <Card className={styles.toolbar} accent="lavender">
        <div className={styles.searchWrap}>
          <span>🔎</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search internships, skills, companies" />
        </div>
        <div className={styles.filterRow}>
          <select defaultValue="all"><option value="all">All domains</option></select>
          <select defaultValue="all"><option value="all">Location</option></select>
          <select defaultValue="all"><option value="all">Remote / On-site</option></select>
        </div>
      </Card>

      <SectionHeader title="Matches for you" subtitle={`${filtered.length} internship opportunities`} />
      <div className={styles.grid}>
        {filtered.map(item => (
          <OpportunityCard
            key={item.id}
            type="internship"
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.location}
            deadline={item.deadline}
            match={item.match}
            skills={item.skills}
            description={`Role type: ${item.type} • Duration: ${item.duration}`}
            actionLabel="Apply"
          />
        ))}
      </div>
    </>
  )
}
