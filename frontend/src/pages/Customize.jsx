import { useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import styles from './Customize.module.css'

const interests = ['Web Development', 'Cloud Computing', 'Cyber Security', 'AI/ML', 'Data Science', 'App Development']
const careerGoals = ['Cloud Engineer', 'Software Engineer', 'ML Engineer', 'Cyber Security', 'Data Scientist']
const skills = ['Python', 'JavaScript', 'AWS', 'SQL', 'Docker', 'Kubernetes', 'React', 'Data Analysis']
const opportunityTypes = ['Internships', 'Hackathons', 'Research Papers', 'Competitions', 'Projects']

export default function Customize() {
  const [selectedInterests, setSelectedInterests] = useState(['Web Development', 'Cloud Computing'])
  const [selectedGoals, setSelectedGoals] = useState(['Cloud Engineer'])
  const [selectedSkills, setSelectedSkills] = useState(['Python', 'AWS'])
  const [selectedPrefs, setSelectedPrefs] = useState(['Internships', 'Hackathons'])

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
                className={`${styles.option} ${selectedSkills.includes(item) ? styles.selected : ''}`}
                onClick={() => toggleList(item, selectedSkills, setSelectedSkills)}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>

        <Card accent="mint" className={styles.sectionCard}>
          <h3>Opportunity preferences</h3>
          <div className={styles.tagWrap}>
            {opportunityTypes.map(item => (
              <button
                key={item}
                className={`${styles.option} ${selectedPrefs.includes(item) ? styles.selected : ''}`}
                onClick={() => toggleList(item, selectedPrefs, setSelectedPrefs)}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>
      </div>

      <div className={styles.footerBar}>
        <button className={styles.saveButton}>Save Preferences</button>
      </div>
    </>
  )
}
