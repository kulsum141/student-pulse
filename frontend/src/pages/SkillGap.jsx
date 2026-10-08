import { useEffect, useState } from 'react'
import { ArrowRight, BookOpenCheck, BriefcaseBusiness, Code2, FolderKanban, Trophy } from 'lucide-react'
import { Link } from 'react-router-dom'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import ProgressBar from '../components/ProgressBar'
import SkillCard from '../components/SkillCard'
import SectionHeader from '../components/SectionHeader'
import EmptyState from '../components/EmptyState'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { skillGapApi, STUDENT_ID } from '../api'
import styles from './SkillGap.module.css'

const ACTION_ICONS = [BookOpenCheck, Code2, FolderKanban, Trophy, BriefcaseBusiness]
const LEARNING_ACTIONS = [
  { title: 'Complete a course', detail: 'Build a guided foundation in cloud concepts.', to: '/roadmap', tone: 'lavender' },
  { title: 'Practice problems', detail: 'Strengthen DSA with consistent short sessions.', to: '/roadmap', tone: 'pink' },
  { title: 'Build a project', detail: 'Apply cloud and web skills in a portfolio project.', to: '/roadmap', tone: 'sky' },
  { title: 'Join a hackathon', detail: 'Collaborate and practice solving open-ended problems.', to: '/hackathons', tone: 'mint' },
  { title: 'Apply for an internship', detail: 'Put your growing skills to work with a team.', to: '/internships', tone: 'peach' },
]

export default function SkillGap() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [savingSkill, setSavingSkill] = useState('')

  useEffect(() => {
    skillGapApi.forCareerGoal(STUDENT_ID)
      .then(({ data }) => {
        setData(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load skill gap information.')
        setLoading(false)
      })
  }, [])

  if (loading) return <LoadingState text="Analyzing your skill gap..." />
  if (error) return <ErrorState message={error} />

  const skills = data.skillLevels || []
  const strongSkills = skills.filter(skill => skill.status === 'strong')
  const focusSkills = skills.filter(skill => skill.status === 'focus').sort((first, second) => first.priority - second.priority)
  const saveSkillLevel = async level => {
    setSavingSkill(level.skill)
    setSaveError('')
    try {
      const { data: savedLevels } = await skillGapApi.saveLevels(STUDENT_ID, [level])
      const savedLevel = savedLevels.find(item => item.name === level.skill)
      setData(current => ({
        ...current,
        skillLevels: current.skillLevels.map(skill => skill.name === level.skill ? { ...skill, ...savedLevel } : skill),
      }))
    } catch (requestError) {
      setSaveError(requestError.message || 'Unable to save this skill level.')
    } finally {
      setSavingSkill('')
    }
  }
  const skillCard = (skill, tone) => (
    <SkillCard
      key={skill.name}
      title={skill.name}
      subtitle={skill.status === 'strong' ? 'Matched to your career goal' : 'Needed for your career goal'}
      value={skill.current}
      target={skill.target}
      gap={skill.gap}
      action={skill.action}
      tone={tone}
      onSaveLevel={saveSkillLevel}
      saving={savingSkill === skill.name}
    />
  )

  return (
    <>
      <PageHeader title="Skill Gap Analysis" subtitle="Understand what skills you have, what you need, and what to learn next." />
      {saveError && <ErrorState message={saveError} />}

      <div className={styles.topGrid}>
        <Card accent="lavender" className={styles.summaryCard}>
          <div className={styles.summaryHead}>
            <span>Overall skill progress</span>
            <strong>{data.readiness}%</strong>
          </div>
          <ProgressBar value={data.readiness} label={`Readiness for ${data.targetCareer}`} color="lavender" />
        </Card>

        <Card accent="pink" className={styles.summaryCard}>
          <div className={styles.summaryHead}>
            <span>Top focus area</span>
            <strong>{focusSkills[0]?.name || data.missingSkills[0] || 'Keep building'}</strong>
          </div>
          <p className={styles.summaryText}>Your next skill-building priority for becoming a {data.targetCareer}.</p>
        </Card>
      </div>

      <section className={styles.section}>
        <SectionHeader title="Strong Skills" subtitle="Skills you can build on as you move toward your goal" />
        {strongSkills.length > 0 ? <div className={styles.skillGrid}>{strongSkills.map(skill => skillCard(skill, 'mint'))}</div> : <EmptyState title="Your strengths are still taking shape" description="Keep adding projects and experience to your profile." />}
      </section>

      <section className={styles.section}>
        <SectionHeader title="Skills to Improve" subtitle="Required skills that are not yet in your profile" />
        {focusSkills.length > 0 ? <div className={styles.skillGrid}>{focusSkills.map(skill => skillCard(skill, 'peach'))}</div> : <EmptyState title="No skill gaps to show" description="You are meeting the current targets in your skill profile." />}
      </section>

      <section className={styles.section}>
        <SectionHeader title="Skills To Focus On" subtitle={`Ranked priorities for your ${data.targetCareer} path`} />
        <div className={styles.focusList}>
          {focusSkills.map((skill, index) => (
            <div className={styles.focusItem} key={skill.name}>
              <span className={styles.rank}>0{index + 1}</span>
              <div className={styles.focusCopy}><strong>{skill.name}</strong><small>{skill.action}</small></div>
              <span className={styles.focusGap}>{index < data.recommendedSkills.length ? `Priority ${index + 1}` : 'Needed'}</span>
            </div>
          ))}
        </div>
      </section>

      <Card accent="sky" className={styles.learningCard}>
        <SectionHeader title="Recommended Skills" subtitle="Learning resources that support your next milestones" />
        {data.recommendedSkills.length > 0 ? <div className={styles.learningList}>{data.recommendedSkills.map(item => <span key={item} className={styles.learningItem}>{item}</span>)}</div> : <EmptyState title="No recommendations yet" description="Your next skills will appear here as your profile grows." />}
      </Card>

      <section className={styles.section}>
        <SectionHeader title="How To Improve" subtitle="Choose one practical action to keep moving forward" />
        <div className={styles.actionGrid}>
          {LEARNING_ACTIONS.map((action, index) => {
            const ActionIcon = ACTION_ICONS[index % ACTION_ICONS.length]
            return (
              <Link to={action.to} key={action.title} className={`${styles.actionCard} ${styles[action.tone]}`}>
                <span className={styles.actionIcon}><ActionIcon size={18} /></span>
                <span className={styles.actionCopy}><strong>{action.title}</strong><small>{action.detail}</small></span>
                <ArrowRight size={15} className={styles.actionArrow} />
              </Link>
            )
          })}
        </div>
      </section>
    </>
  )
}
