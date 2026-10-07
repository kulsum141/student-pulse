import { useEffect, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
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

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)

    if (!saved) return

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

  return (
    <>
      <PageHeader title="Customization" subtitle="Shape the platform around your learning preferences" />

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
        <button type="button" className={styles.saveButton}>Saved locally</button>
      </div>
    </>
  )
}
