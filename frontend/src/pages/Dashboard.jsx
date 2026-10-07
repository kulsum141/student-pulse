import { useEffect, useMemo, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import OpportunityCard from '../components/OpportunityCard'
import ProgressBar from '../components/ProgressBar'
import SectionHeader from '../components/SectionHeader'
import StatCard from '../components/StatCard'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './Dashboard.module.css'

const researchPicks = [
  { id: 'PAP-33', title: 'Efficient Feature Selection for Predictive Learning', organization: 'ACM Research', domain: 'Machine Learning', difficulty: 'Advanced', match: 90 },
  { id: 'PAP-41', title: 'Edge AI for Smart Campus Systems', organization: 'IEEE Papers', domain: 'Embedded AI', difficulty: 'Intermediate', match: 85 },
  { id: 'PAP-22', title: 'Reliable Distributed Storage for Education Platforms', organization: 'Springer', domain: 'Distributed Systems', difficulty: 'Advanced', match: 83 },
]

const deadlines = [
  { title: 'Google Cloud Internship', days: 3 },
  { title: 'AI Hackathon', days: 6 },
  { title: 'Research Fellows Program', days: 9 },
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')

  useEffect(() => {
    mockApi.getDashboardData()
      .then(({ data }) => {
        setData(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load dashboard data.')
        setLoading(false)
      })
  }, [])

  const opportunityList = useMemo(() => {
    if (!data) return []

    const all = [
      ...data.recommendations.opportunities.map(item => ({ ...item, category: 'Internships' })),
      ...data.recommendations.hackathons.map(item => ({ ...item, category: 'Hackathons' })),
      ...data.recommendations.papers.map(item => ({ ...item, category: 'Research' })),
    ]

    return selectedCategory === 'All' ? all : all.filter(item => item.category === selectedCategory)
  }, [data, selectedCategory])

  if (loading) return <LoadingState text="Fetching your recommendations..." />
  if (error) return <ErrorState message={error} />

  const { metrics, recommendations, saved, roadmap, skillGap, assistantSuggestions } = data

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Your personalized learning and opportunity overview" />

      <div className={styles.heroCard}>
        <div>
          <p className={styles.greeting}>Good morning, Student! 👋</p>
          <p className={styles.subtext}>Here is what is waiting for you today.</p>
        </div>
        <div className={styles.heroActions}>
          <button className={styles.primaryButton}>Explore Recommendations</button>
          <button className={styles.secondaryButton}>Continue Roadmap</button>
        </div>
      </div>

      <div className={styles.statsGrid}>
        {metrics.map(metric => (
          <StatCard key={metric.label} label={metric.label} value={metric.value} accent={metric.accent} />
        ))}
      </div>

      <SectionHeader title="Recommended for You" subtitle="A mix of internships, hackathons, and research ideas" />
      <div className={styles.recommendationGrid}>
        {recommendations.opportunities.slice(0, 2).map(item => (
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
            description={item.description}
            actionLabel="Apply"
          />
        ))}
        {recommendations.hackathons.slice(0, 1).map(item => (
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
            description={item.description}
            actionLabel="View"
          />
        ))}
        {recommendations.papers.slice(0, 1).map(item => (
          <OpportunityCard
            key={item.id}
            type="paper"
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.location}
            deadline={item.deadline}
            match={item.match}
            skills={item.skills}
            description={item.description}
            actionLabel="Read"
          />
        ))}
      </div>

      <SectionHeader title="Explore Opportunities" subtitle="Filter by opportunity type, domain, and timeline" />
      <div className={styles.filterRow}>
        {['All', 'Internships', 'Hackathons', 'Research'].map(option => (
          <button
            key={option}
            type="button"
            className={`${styles.filterChip} ${selectedCategory === option ? styles.activeFilter : ''}`}
            onClick={() => setSelectedCategory(option)}
          >
            {option}
          </button>
        ))}
      </div>
      <div className={styles.exploreGrid}>
        {opportunityList.map(item => (
          <OpportunityCard
            key={item.id}
            type={item.category === 'Hackathons' ? 'hackathon' : item.category === 'Research' ? 'paper' : 'internship'}
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.location || 'Remote'}
            deadline={item.deadline || 'Flexible'}
            match={item.match}
            skills={item.skills || ['Python', 'Research']}
            description={item.description}
            actionLabel={item.category === 'Research' ? 'Read' : 'View'}
          />
        ))}
      </div>

      <div className={styles.splitGrid}>
        <Card className={styles.panelCard} accent="mint">
          <SectionHeader title="Your Learning Roadmap" subtitle="Track your weekly growth" />
          <div className={styles.progressWrap}>
            <ProgressBar value={roadmap.progress} label="Python" color="mint" />
            <ProgressBar value={60} label="Cloud Computing" color="sky" />
            <ProgressBar value={40} label="DSA" color="pink" />
            <ProgressBar value={70} label="Web Development" color="lavender" />
          </div>
          <button className={styles.secondaryButton}>View Full Roadmap</button>
        </Card>

        <Card className={styles.panelCard} accent="peach">
          <SectionHeader title="Your Skill Gap" subtitle="Skills to strengthen" />
          <div className={styles.skillList}>
            <div className={styles.skillPill}><span>Strong Skills</span><strong>Python, HTML/CSS</strong></div>
            <div className={styles.skillPill}><span>Skills to Improve</span><strong>AWS, DSA, SQL</strong></div>
          </div>
          <button className={styles.primaryButton}>Improve My Skills</button>
        </Card>
      </div>

      <div className={styles.lowerGrid}>
        <Card className={styles.panelCard} accent="sky">
          <SectionHeader title="Research Picks" subtitle="Fresh reads for your focus area" />
          <div className={styles.researchGrid}>
            {researchPicks.map(paper => (
              <div key={paper.id} className={styles.researchCard}>
                <div className={styles.researchMeta}>
                  <span>{paper.domain}</span>
                  <span>{paper.match}% match</span>
                </div>
                <h3>{paper.title}</h3>
                <p>{paper.organization}</p>
                <div className={styles.researchFooter}>
                  <small>{paper.difficulty}</small>
                  <div className={styles.researchActions}>
                    <button className={styles.secondaryButton}>Save</button>
                    <button className={styles.primaryButton}>Read</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className={styles.panelCard} accent="pink">
          <SectionHeader title="Don't Miss These" subtitle="Upcoming deadlines" />
          <div className={styles.deadlineList}>
            {deadlines.map(item => (
              <div key={item.title} className={styles.deadlineItem}>
                <div>
                  <strong>{item.title}</strong>
                  <small>Deadline: {item.days} days</small>
                </div>
                <span>{item.days}d</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className={styles.personalizeCard} accent="lavender">
        <SectionHeader title="Customize Your Pulse" subtitle="Choose your interests and preferred opportunities" />
        <div className={styles.preferenceRow}>
          {['AI / ML', 'Cloud', 'Cyber Security', 'Web Development', 'Data Science', 'App Development', 'Research', 'Startups'].map(item => (
            <span key={item} className={styles.preferencePill}>{item}</span>
          ))}
        </div>
        <div className={styles.preferenceRow}>
          {['Internship', 'Hackathon', 'Research', 'All'].map(item => (
            <span key={item} className={styles.preferencePill}>{item}</span>
          ))}
        </div>
      </Card>

      <div className={styles.bottomGrid}>
        <Card className={styles.panelCard} accent="pink">
          <SectionHeader title="AI Assistant" subtitle="Need help planning your next step?" />
          <p className={styles.assistantText}>Ask Student Pulse AI</p>
          <button className={styles.secondaryButton}>Start chatting</button>
          <div className={styles.suggestionList}>
            {assistantSuggestions.slice(0, 2).map(item => (
              <span key={item} className={styles.suggestionChip}>{item}</span>
            ))}
          </div>
        </Card>

        <Card className={styles.panelCard} accent="peach">
          <SectionHeader title="Saved items" subtitle="Recently saved for later" />
          <div className={styles.savedList}>
            {saved.slice(0, 3).map(item => (
              <div key={item.id} className={styles.savedItem}>
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.organization}</small>
                </div>
                <span>{item.match}%</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </>
  )
}
