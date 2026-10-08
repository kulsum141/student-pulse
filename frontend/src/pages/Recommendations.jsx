import { useEffect, useState } from 'react'
import { Search, SlidersHorizontal } from 'lucide-react'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/PageHeader'
import OpportunityCard from '../components/OpportunityCard'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import SectionHeader from '../components/SectionHeader'
import { opportunitiesApi, recommendationsApi, STUDENT_ID } from '../api'
import styles from './Recommendations.module.css'

const CATEGORIES = ['All', 'Internships', 'Hackathons', 'Research', 'Jobs']

export default function Recommendations() {
  const [items, setItems] = useState([])
  const [recommended, setRecommended] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [skill, setSkill] = useState('All skills')
  const [location, setLocation] = useState('All locations')
  const [mode, setMode] = useState('Any format')
  const [deadline, setDeadline] = useState('Any deadline')
  const [experience, setExperience] = useState('Any experience')

  useEffect(() => {
    opportunitiesApi.discover(STUDENT_ID)
      .then(({ data }) => {
        setRecommended(data.featured)
        setItems(data.items)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load opportunities right now.')
        setLoading(false)
      })
  }, [])

  const skills = [...new Set(items.flatMap(item => item.skills))].sort()
  const locations = [...new Set(items.map(item => item.location))].sort()
  const experiences = [...new Set(items.map(item => item.experienceLevel))].sort()
  const filtered = items.filter(item => {
    const searchable = [item.title, item.organization, item.domain, item.category, item.location, ...item.skills]
      .join(' ')
      .toLowerCase()
    return (category === 'All' || item.category === category)
      && searchable.includes(query.trim().toLowerCase())
      && (skill === 'All skills' || item.skills.includes(skill))
      && (location === 'All locations' || item.location === location)
      && (mode === 'Any format' || item.mode === mode)
      && (deadline === 'Any deadline' || (deadline === 'Has deadline' ? Boolean(item.deadline) : !item.deadline))
      && (experience === 'Any experience' || item.experienceLevel === experience)
  })

  const updateCategory = value => setCategory(value)
  const categoryPath = item => item.category === 'Internships'
    ? '/internships'
    : item.category === 'Hackathons'
      ? '/hackathons'
      : '/research'

  if (loading) return <LoadingState text="Loading recommendations..." />
  if (error) return <ErrorState message={error} />

  return (
    <>
      <PageHeader
        title="Opportunities"
        subtitle="Discover opportunities matched to your skills, interests, and goals."
      />

      <section className={styles.recommendedSection} aria-label="Recommended for you">
        <SectionHeader title="Recommended For You" subtitle="A few strong matches from your existing recommendations" />
        {recommended.length > 0 ? (
          <div className={styles.recommendedGrid}>
            {recommended.slice(0, 3).map(item => (
              <OpportunityCard
                key={item.id}
                {...item}
                actionLabel="View Details"
                detailTo={categoryPath(item)}
                onSave={() => recommendationsApi.save(STUDENT_ID, item)}
              />
            ))}
          </div>
        ) : (
          <EmptyState title="Your recommendations are on their way" description="Check back after your interests and profile are set up." />
        )}
      </section>

      <div className={styles.categoryTabs} role="tablist" aria-label="Opportunity category">
        {CATEGORIES.map(item => (
          <button
            key={item}
            type="button"
            role="tab"
            aria-selected={category === item}
            className={`${styles.categoryTab} ${category === item ? styles.activeTab : ''}`}
            onClick={() => updateCategory(item)}
          >
            {item}
          </button>
        ))}
      </div>

      <section className={styles.filterPanel} aria-label="Filter opportunities">
        <div className={styles.searchWrap}>
          <Search size={17} aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={event => setQuery(event.target.value)}
            placeholder="Search titles, organizations, skills..."
            aria-label="Search opportunities"
          />
          <span className={styles.filterIcon}><SlidersHorizontal size={15} /></span>
        </div>
        <div className={styles.filterGrid}>
          <label><span>Category</span><select value={category} onChange={event => updateCategory(event.target.value)}>{CATEGORIES.map(item => <option key={item}>{item}</option>)}</select></label>
          <label><span>Skills</span><select value={skill} onChange={event => setSkill(event.target.value)}><option key="all-skills">All skills</option>{skills.map(item => <option key={item}>{item}</option>)}</select></label>
          <label><span>Location</span><select value={location} onChange={event => setLocation(event.target.value)}><option key="all-locations">All locations</option>{locations.map(item => <option key={item}>{item}</option>)}</select></label>
          <label><span>Remote / On-site</span><select value={mode} onChange={event => setMode(event.target.value)}><option key="any-format">Any format</option><option key="remote">Remote</option><option key="on-site">On-site</option><option key="hybrid">Hybrid</option><option key="unspecified">Not specified</option></select></label>
          <label><span>Deadline</span><select value={deadline} onChange={event => setDeadline(event.target.value)}><option key="any-deadline">Any deadline</option><option key="has-deadline">Has deadline</option><option key="no-deadline">No deadline</option></select></label>
          <label><span>Experience level</span><select value={experience} onChange={event => setExperience(event.target.value)}><option key="any-experience">Any experience</option>{experiences.map(item => <option key={item}>{item}</option>)}</select></label>
        </div>
      </section>

      <SectionHeader title="Explore opportunities" subtitle={`${filtered.length} ${filtered.length === 1 ? 'match' : 'matches'} for your search`} />
      {filtered.length > 0 ? <div className={styles.grid}>
        {filtered.map(item => (
          <OpportunityCard
            key={item.id}
            {...item}
            actionLabel="View Details"
            detailTo={categoryPath(item)}
            onSave={() => recommendationsApi.save(STUDENT_ID, item)}
          />
        ))}
      </div> : <EmptyState title="No opportunities match these filters" description="Try a broader search or reset one of the filters to see more matches." />}
    </>
  )
}
