import { useEffect, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { preferencesApi, STUDENT_ID } from '../api'
import styles from './Customize.module.css'

const interests = ['AI / ML', 'Cloud', 'Cyber Security', 'Web Development', 'Data Science', 'App Development', 'Research', 'Startups']
const careerGoals = ['Cloud Engineer', 'Software Engineer', 'ML Engineer', 'Cyber Security', 'Data Scientist']
const skills = ['Python', 'JavaScript', 'AWS', 'SQL', 'Docker', 'Kubernetes', 'React', 'Data Analysis']
const opportunityTypes = ['Internship', 'Hackathon', 'Research', 'All']
const difficultyLevels = ['Beginner', 'Intermediate', 'Advanced']

const STORAGE_KEY = 'student-pulse-preferences'

const defaultPreferences = {
  selectedInterests: ['AI / ML', 'Cloud', 'Web Development'],
  selectedGoals: ['Cloud Engineer'],
  selectedSkills: ['Python', 'AWS'],
  selectedPrefs: ['Internship', 'Hackathon'],
  selectedDifficulty: ['Intermediate'],
}

export default function Customize() {
  const [selectedInterests, setSelectedInterests] = useState(defaultPreferences.selectedInterests)
  const [selectedGoals, setSelectedGoals] = useState(defaultPreferences.selectedGoals)
  const [selectedSkills, setSelectedSkills] = useState(defaultPreferences.selectedSkills)
  const [selectedPrefs, setSelectedPrefs] = useState(defaultPreferences.selectedPrefs)
  const [selectedDifficulty, setSelectedDifficulty] = useState(defaultPreferences.selectedDifficulty)
  const [loadingPreferences, setLoadingPreferences] = useState(true)
  const [saving, setSaving] = useState(false)
  const [apiError, setApiError] = useState('')
  const [saveMessage, setSaveMessage] = useState('')

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)

    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setSelectedInterests(parsed.selectedInterests || defaultPreferences.selectedInterests)
        setSelectedGoals(parsed.selectedGoals || defaultPreferences.selectedGoals)
        setSelectedSkills(parsed.selectedSkills || defaultPreferences.selectedSkills)
        setSelectedPrefs(parsed.selectedPrefs || defaultPreferences.selectedPrefs)
        setSelectedDifficulty(parsed.selectedDifficulty || defaultPreferences.selectedDifficulty)
      } catch {
        // Ignore malformed local storage data and keep defaults.
      }
    }

    preferencesApi.get(STUDENT_ID)
      .then(({ data }) => {
        if (data.interests?.length) setSelectedInterests(data.interests)
        if (data.career_goal) setSelectedGoals([careerGoals.find(item => item.toLowerCase() === data.career_goal.toLowerCase()) || data.career_goal])
        if (data.skill_level) setSelectedDifficulty([difficultyLevels.find(item => item.toLowerCase() === data.skill_level.toLowerCase()) || data.skill_level])
        if (data.preferred_opportunity_type) {
          const preference = opportunityTypes.find(item => item.toLowerCase() === data.preferred_opportunity_type.toLowerCase())
          if (preference) setSelectedPrefs([preference])
        }
      })
      .catch(error => setApiError(error.message || 'Unable to load saved preferences.'))
      .finally(() => setLoadingPreferences(false))
  }, [])

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        selectedInterests,
        selectedGoals,
        selectedSkills,
        selectedPrefs,
        selectedDifficulty,
      }),
    )
  }, [selectedInterests, selectedGoals, selectedSkills, selectedPrefs, selectedDifficulty])

  const toggleList = (value, current, setter) => {
    setter(current.includes(value) ? current.filter(item => item !== value) : [...current, value])
  }

  const savePreferences = async () => {
    setSaving(true)
    setApiError('')
    setSaveMessage('')
    try {
      await preferencesApi.save(STUDENT_ID, {
        career_goal: selectedGoals[0] || null,
        interests: selectedInterests,
        skill_level: selectedDifficulty[0]?.toLowerCase() || null,
        preferred_opportunity_type: selectedPrefs[0]?.toLowerCase() || null,
      })
      setSaveMessage('Preferences saved to your profile.')
    } catch (error) {
      setApiError(error.message || 'Preferences were saved locally but could not reach the backend.')
      setSaveMessage('Your choices are saved on this device.')
    } finally {
      setSaving(false)
    }
  }

  if (loadingPreferences) return <LoadingState text="Loading your preferences..." />

  return (
    <>
      <PageHeader title="Customization" subtitle="Shape the platform around your learning preferences" />
      {apiError && <ErrorState message={apiError} />}

      <div className={styles.grid}>
        <Card accent="lavender" className={styles.sectionCard}>
          <h3>Interests</h3>
          <div className={styles.tagWrap}>
            {interests.map(item => (
              <button
                key={item}
                type="button"
                className={`${styles.option} ${selectedInterests.includes(item) ? styles.selected : ''}`}
                onClick={() => toggleList(item, selectedInterests, setSelectedInterests)}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>

        <Card accent="pink" className={styles.sectionCard}>
          <h3>Career goals</h3>
          <div className={styles.tagWrap}>
            {careerGoals.map(item => (
              <button
                key={item}
                type="button"
                className={`${styles.option} ${selectedGoals.includes(item) ? styles.selected : ''}`}
                onClick={() => toggleList(item, selectedGoals, setSelectedGoals)}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>

        <Card accent="sky" className={styles.sectionCard}>
          <h3>Skills</h3>
          <div className={styles.tagWrap}>
            {skills.map(item => (
              <button
                key={item}
                type="button"
                className={`${styles.option} ${selectedSkills.includes(item) ? styles.selected : ''}`}
                onClick={() => toggleList(item, selectedSkills, setSelectedSkills)}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>

        <Card accent="mint" className={styles.sectionCard}>
          <h3>Preferred opportunity type</h3>
          <div className={styles.tagWrap}>
            {opportunityTypes.map(item => (
              <button
                key={item}
                type="button"
                className={`${styles.option} ${selectedPrefs.includes(item) ? styles.selected : ''}`}
                onClick={() => toggleList(item, selectedPrefs, setSelectedPrefs)}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>

        <Card accent="peach" className={styles.sectionCard}>
          <h3>Preferred difficulty</h3>
          <div className={styles.tagWrap}>
            {difficultyLevels.map(item => (
              <button
                key={item}
                type="button"
                className={`${styles.option} ${selectedDifficulty.includes(item) ? styles.selected : ''}`}
                onClick={() => toggleList(item, selectedDifficulty, setSelectedDifficulty)}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>
      </div>

      <div className={styles.footerBar}>
        <button type="button" className={styles.saveButton} onClick={savePreferences} disabled={saving}>
          {saving ? 'Saving...' : 'Save preferences'}
        </button>
        {saveMessage && <span role="status">{saveMessage}</span>}
      </div>
    </>
  )
}
