import { useEffect, useState } from 'react'
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

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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

  if (loading) return <LoadingState text="Fetching your recommendations..." />
  if (error) return <ErrorState message={error} />

  const { metrics, recommendations, saved, roadmap, skillGap, assistantSuggestions } = data

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Your personalized learning and opportunity overview" />

      <div className={styles.heroCard}>
        <div>
          <p className={styles.greeting}>Good morning, Kulsum 👋</p>
          <p className={styles.subtext}>Here are opportunities and resources selected for you.</p>
        </div>
        <button className={styles.primaryButton}>View recommendations</button>
      </div>

      <div className={styles.statsGrid}>
        {metrics.map(metric => (
          <StatCard key={metric.label} label={metric.label} value={metric.value} accent={metric.accent} />
        ))}
      </div>

      <SectionHeader title="Recommended opportunities" subtitle="A mix of internships, hackathons, and research ideas" />
      <div className={styles.recommendationGrid}>
        {recommendations.opportunities.map(item => (
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
        {recommendations.hackathons.map(item => (
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
        {recommendations.papers.map(item => (
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

      <div className={styles.bottomGrid}>
        <Card className={styles.panelCard} accent="mint">
          <SectionHeader title="Career roadmap preview" subtitle={roadmap.careerGoal} />
          <div className={styles.progressWrap}>
            <ProgressBar value={roadmap.progress} label="Progress" color="mint" />
          </div>
          <div className={styles.metaList}>
            <div>
              <span className={styles.metaLabel}>Completed</span>
              <strong>{roadmap.completed.length} skills</strong>
            </div>
            <div>
              <span className={styles.metaLabel}>Current</span>
              <strong>{roadmap.currentSkill}</strong>
            </div>
            <div>
              <span className={styles.metaLabel}>Upcoming</span>
              <strong>{roadmap.upcoming[0]}</strong>
            </div>
          </div>
        </Card>

        <Card className={styles.panelCard} accent="lavender">
          <SectionHeader title="Skill gap preview" subtitle="Skills to sharpen next" />
          <div className={styles.skillList}>
            <div>
              <span>Current skills</span>
              <strong>{skillGap.currentSkills.slice(0, 3).join(', ')}</strong>
            </div>
            <div>
              <span>Missing/weak skills</span>
              <strong>{skillGap.missingSkills.slice(0, 3).join(', ')}</strong>
            </div>
            <div>
              <span>Recommended skills</span>
              <strong>{skillGap.recommendedSkills[0]}</strong>
            </div>
          </div>
        </Card>

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
          <SectionHeader title="Saved opportunities" subtitle="Recently saved for later" />
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
