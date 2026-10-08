import { useEffect, useState } from 'react'
import { ArrowRight, CheckCircle2, Circle, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import ProgressBar from '../components/ProgressBar'
import RoadmapNode from '../components/RoadmapNode'
import SectionHeader from '../components/SectionHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import { roadmapApi, STUDENT_ID } from '../api'
import styles from './Roadmap.module.css'

export default function Roadmap() {
  const [data, setData] = useState(null)
  const [steps, setSteps] = useState([])
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [progressError, setProgressError] = useState('')

  useEffect(() => {
    roadmapApi.forPage(STUDENT_ID)
      .then(({ data }) => {
        setData(data)
        setSteps(data.steps)
        setProgress(data.progress)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load roadmap.')
        setLoading(false)
      })
  }, [])

  const markComplete = async title => {
    const completedIndex = steps.findIndex(step => step.title === title && step.status === 'active')
    if (completedIndex < 0) return
    const activeStep = steps[completedIndex]
    setProgressError('')
    try {
      await roadmapApi.updateProgress(STUDENT_ID, {
        career_goal: data.careerGoal,
        step_number: activeStep.stepNumber,
        skill: activeStep.title,
        completed: true,
      })
      const updatedSteps = steps.map((step, index) => {
        if (index === completedIndex) return { ...step, status: 'done', progress: 100 }
        if (index === completedIndex + 1 && step.status === 'next') return { ...step, status: 'active', progress: Math.max(step.progress, 10) }
        return step
      })
      setSteps(updatedSteps)
      setProgress(Math.round((updatedSteps.filter(step => step.status === 'done').length / Math.max(1, updatedSteps.length)) * 100))
    } catch (requestError) {
      setProgressError(requestError.message || 'Unable to save roadmap progress.')
    }
  }

  if (loading) return <LoadingState text="Preparing your roadmap..." />
  if (error) return <ErrorState message={error} />

  const currentStage = steps.find(step => step.status === 'active')
  const currentMilestone = currentStage?.title || data.currentSkill
  const completedStages = steps.filter(step => step.status === 'done')
  const upcomingStages = steps.filter(step => step.status === 'next')

  return (
    <>
      <PageHeader title="My Roadmap" subtitle="A personal guide for your learning and career journey, one meaningful step at a time." />
      {progressError && <ErrorState message={progressError} />}

      <Card className={styles.heroCard} accent="lavender">
        <div className={styles.goalCopy}>
          <p className={styles.kicker}><Target size={14} /> CURRENT CAREER GOAL</p>
          <h2>{data.careerGoal}</h2>
          <p className={styles.goalDescription}>A practical path from what you know today to the work you want to do next.</p>
        </div>
        <div className={styles.progressBox}>
          <strong>{progress}%</strong>
          <span>overall progress</span>
        </div>
      </Card>

      <div className={styles.progressWrap}>
        <ProgressBar value={progress} label="Your roadmap journey" color="lavender" />
      </div>

      <div className={styles.currentStageWrap}>
        <Card className={styles.currentStage} accent="pink">
          <div className={styles.currentStageIcon}><Circle size={18} /></div>
          <div className={styles.currentStageCopy}>
            <span>YOU ARE HERE</span>
            <h3>{currentStage?.title || 'Your next stage is ready'}</h3>
            <p>Current milestone: <strong>{currentMilestone}</strong></p>
          </div>
          <Link to="/skill-gap" className={styles.continueButton}>Continue Learning <ArrowRight size={15} /></Link>
        </Card>
      </div>

      <div className={styles.milestoneGrid}>
        <Card className={styles.milestoneCard} accent="mint">
          <div className={styles.milestoneHeading}><CheckCircle2 size={17} /><span>Completed milestones</span></div>
          <ul>{data.completed.map(item => <li key={item}>{item}</li>)}</ul>
        </Card>
        <Card className={styles.milestoneCard} accent="sky">
          <div className={styles.milestoneHeading}><Circle size={17} /><span>Upcoming milestones</span></div>
          <ul>{data.upcoming.map(item => <li key={item}>{item}</li>)}</ul>
        </Card>
      </div>

      <SectionHeader title="Your learning stages" subtitle="A clear path from core skills to career preparation" />
      {steps.length > 0 ? <div className={styles.grid}>
        {steps.map(step => <RoadmapNode key={step.title} item={step} onMarkComplete={markComplete} />)}
      </div> : <EmptyState title="Your roadmap is up to date" description="Your current skills already match this career goal. Revisit the skill gap analysis when your goals change." />}

      <section className={styles.nextStepsSection}>
        <SectionHeader title="Recommended Next Steps" subtitle="Small, practical actions to keep your momentum going" />
        {data.nextSteps.length > 0 ? <div className={styles.nextStepsGrid}>
          {data.nextSteps.map((step, index) => (
            <Link to={step.to} className={styles.nextStep} key={step.title}>
              <span className={styles.stepNumber}>0{index + 1}</span>
              <span className={styles.nextStepCopy}><strong>{step.title}</strong><small>{step.detail}</small></span>
              <ArrowRight size={16} />
            </Link>
          ))}
        </div> : <EmptyState title="No next steps needed" description="You have completed the skills currently required for this goal." />}
      </section>
      <span className={styles.stageSummary} aria-hidden="true">{completedStages.length} stages completed · {upcomingStages.length} upcoming</span>
    </>
  )
}
