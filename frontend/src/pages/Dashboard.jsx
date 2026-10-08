import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, BriefcaseBusiness, Map, MessageCircle, SlidersHorizontal, Sparkles } from 'lucide-react'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/PageHeader'
import OpportunityCard from '../components/OpportunityCard'
import ProgressBar from '../components/ProgressBar'
import SectionHeader from '../components/SectionHeader'
import StatCard from '../components/StatCard'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { dashboardApi, recommendationsApi, STUDENT_ID } from '../api'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [savedResearch, setSavedResearch] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('All')

  useEffect(() => {
    dashboardApi.get(STUDENT_ID)
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

  const { metrics, recommendations, saved, roadmap, skillGap, assistantSuggestions, profile } = data
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const hasRecommendations = Object.values(recommendations).some(items => items.length > 0)
  const researchPicks = recommendations.papers.slice(0, 3)
  const deadlines = [...recommendations.opportunities, ...recommendations.hackathons]
    .filter(item => item.deadline)
    .slice(0, 3)
  const saveDashboardItem = async item => {
    setActionError('')
    try {
      await recommendationsApi.save(STUDENT_ID, item)
      setSavedResearch(current => [...new Set([...current, item.id])])
    } catch (requestError) {
      setActionError(requestError.message || 'Unable to save this opportunity.')
    }
  }

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Your personalized learning and opportunity overview" />

      <div className={styles.heroCard}>
        <div className={styles.heroCopy}>
          <span className={styles.eyebrow}><Sparkles size={14} /> YOUR PERSONAL PULSE</span>
          <p className={styles.greeting}>{greeting}, {profile.name}!</p>
          <p className={styles.subtext}>A few thoughtful next steps can take you somewhere wonderful.</p>
          <div className={styles.heroActions}>
            <Link className={styles.primaryButton} to="/opportunities">Explore opportunities <ArrowRight size={16} /></Link>
            <Link className={styles.secondaryButton} to="/roadmap">Continue roadmap</Link>
          </div>
        </div>
        <div className={styles.profileSnapshot}>
          <div className={styles.snapshotTop}>
            <div className={styles.snapshotAvatar}>{profile.name?.charAt(0) || 'S'}</div>
            <div><strong>{profile.name}</strong><span>{profile.department}</span></div>
            <Link to="/profile" aria-label="Edit student profile"><ArrowRight size={16} /></Link>
          </div>
          <div className={styles.snapshotDetails}>
            <div><span>Year</span><strong>{profile.year_of_study}</strong></div>
            <div><span>CGPA</span><strong>{profile.cgpa}</strong></div>
          </div>
          <div className={styles.careerGoal}><span>Working toward</span><strong>{profile.career_goal}</strong></div>
        </div>
      </div>

      <div className={styles.quickActions} aria-label="Quick actions">
        <span className={styles.quickActionsLabel}>QUICK ACTIONS</span>
        <Link to="/internships"><BriefcaseBusiness size={17} /> Find an internship</Link>
        <Link to="/roadmap"><Map size={17} /> Pick up your roadmap</Link>
        <Link to="/assistant"><MessageCircle size={17} /> Ask your AI assistant</Link>
        <Link to="/customize"><SlidersHorizontal size={17} /> Tune your interests</Link>
      </div>

      <div className={styles.statsGrid}>
        {metrics.map(metric => (
          <StatCard key={metric.label} label={metric.label} value={metric.value} accent={metric.accent} />
        ))}
      </div>

      <SectionHeader title="Recommended for You" subtitle="A mix of internships, hackathons, and research ideas" />
      {actionError && <ErrorState message={actionError} />}
      {hasRecommendations ? <div className={styles.recommendationGrid}>
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
            onSave={() => saveDashboardItem(item)}
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
            onSave={() => saveDashboardItem(item)}
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
            onSave={() => saveDashboardItem(item)}
          />
        ))}
      </div> : <EmptyState title="Your recommendations are on their way" description="Add a few interests to your profile and we’ll find a good place to start." />}

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
      {opportunityList.length > 0 ? <div className={styles.exploreGrid}>
        {opportunityList.map(item => (
          <OpportunityCard
            key={item.id}
            type={item.type}
            title={item.title}
            organization={item.organization}
            domain={item.domain}
            location={item.location || 'Remote'}
            deadline={item.deadline || 'Flexible'}
            match={item.match}
            skills={item.skills || ['Python', 'Research']}
            description={item.description}
            actionLabel={item.category === 'Research' ? 'Read' : 'View'}
            onSave={() => saveDashboardItem(item)}
          />
        ))}
      </div> : <EmptyState title="No matches in this category yet" description="Try another filter or update your interests to discover more." />}

      <div className={styles.splitGrid}>
        <Card className={styles.panelCard} accent="mint">
          <SectionHeader title="Your Learning Roadmap" subtitle="Track your weekly growth" />
          <div className={styles.progressWrap}>
            {(roadmap.steps || []).slice(0, 4).map((step, index) => (
              <ProgressBar key={step.title} value={step.progress} label={step.title} color={['mint', 'sky', 'pink', 'lavender'][index]} />
            ))}
          </div>
          <Link className={styles.secondaryButton} to="/roadmap">View Full Roadmap</Link>
        </Card>

        <Card className={styles.panelCard} accent="peach">
          <SectionHeader title="Your Skill Gap" subtitle={`${skillGap.readiness}% ready for ${skillGap.targetCareer}`} />
          <div className={styles.skillList}>
            <div className={styles.skillPill}><span>Matched skills</span><strong>{skillGap.matchedSkills.slice(0, 3).join(', ') || 'No current matches'}</strong></div>
            <div className={styles.skillPill}><span>Skills to strengthen</span><strong>{skillGap.missingSkills.slice(0, 3).join(', ') || 'No skill gaps found'}</strong></div>
          </div>
          <Link className={styles.primaryButton} to="/skill-gap">Improve My Skills</Link>
        </Card>
      </div>

      <div className={styles.lowerGrid}>
        <Card className={styles.panelCard} accent="sky">
          <SectionHeader title="Research Picks" subtitle="Fresh reads for your focus area" />
          {researchPicks.length > 0 ? <div className={styles.researchGrid}>
            {researchPicks.map(paper => (
              <div key={paper.id} className={styles.researchCard}>
                <div className={styles.researchMeta}>
                  <span>{paper.domain}</span>
                  <span>{paper.match}% match</span>
                </div>
                <h3>{paper.title}</h3>
                <p>{paper.organization}</p>
                <div className={styles.researchFooter}>
                  <small>{paper.difficulty || paper.domain}</small>
                  <div className={styles.researchActions}>
                    <button type="button" className={styles.secondaryButton} disabled={savedResearch.includes(paper.id)} onClick={() => saveDashboardItem(paper)}>
                      {savedResearch.includes(paper.id) ? 'Saved' : 'Save'}
                    </button>
                    <Link className={styles.primaryButton} to="/research">Read</Link>
                  </div>
                </div>
              </div>
            ))}
          </div> : <EmptyState title="No research picks yet" description="Research recommendations will appear here when available." />}
        </Card>

        <Card className={styles.panelCard} accent="pink">
          <SectionHeader title="Upcoming internships & deadlines" subtitle="Application windows worth keeping in sight" />
          {deadlines.length > 0 ? <div className={styles.deadlineList}>
            {deadlines.map(item => (
              <div key={item.title} className={styles.deadlineItem}>
                <div>
                  <strong>{item.title}</strong>
                  <small>Deadline: {item.deadline}</small>
                </div>
                <span>Due</span>
              </div>
            ))}
          </div> : <EmptyState title="No deadlines available" description="Listings will show here when the backend includes deadline information." />}
        </Card>
      </div>

      <Card className={styles.personalizeCard} accent="lavender">
        <SectionHeader title="Customize Your Pulse" subtitle="Choose your interests and preferred opportunities" />
        <div className={styles.preferenceRow}>
          {profile.interests.map(item => (
            <span key={item} className={styles.preferencePill}>{item}</span>
          ))}
        </div>
        <div className={styles.preferenceRow}>
          {profile.preferred_opportunity_types.map(item => (
            <span key={item} className={styles.preferencePill}>{item}</span>
          ))}
        </div>
      </Card>

      <div className={styles.bottomGrid}>
        <Card className={styles.panelCard} accent="pink">
          <SectionHeader title="AI Assistant" subtitle="Need help planning your next step?" />
          <p className={styles.assistantText}>Ask Student Pulse AI</p>
          <Link className={styles.secondaryButton} to="/assistant">Start chatting</Link>
          <div className={styles.suggestionList}>
            {assistantSuggestions.slice(0, 2).map(item => (
              <span key={item} className={styles.suggestionChip}>{item}</span>
            ))}
          </div>
        </Card>

        <Card className={styles.panelCard} accent="peach">
          <SectionHeader title="Saved items" subtitle="Recently saved for later" />
          {saved.length > 0 ? <div className={styles.savedList}>
            {saved.slice(0, 3).map(item => (
              <div key={item.id} className={styles.savedItem}>
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.organization}</small>
                </div>
                <span>{item.type}</span>
              </div>
            ))}
          </div> : <EmptyState title="No saved opportunities" description="Save a recommendation to keep it here for later." />}
        </Card>
      </div>
    </>
  )
}
