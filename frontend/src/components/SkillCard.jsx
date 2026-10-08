import { useEffect, useState } from 'react'
import Card from './Card'
import ProgressBar from './ProgressBar'
import styles from './SkillCard.module.css'

export default function SkillCard({ title, subtitle, value, target, gap, action, tone = 'lavender', onSaveLevel, saving = false }) {
  const [currentLevel, setCurrentLevel] = useState(value ?? '')
  const [targetLevel, setTargetLevel] = useState(target ?? '')

  useEffect(() => {
    setCurrentLevel(value ?? '')
    setTargetLevel(target ?? '')
  }, [value, target])

  const saveLevels = event => {
    event.preventDefault()
    onSaveLevel({ skill: title, current_level: Number(currentLevel), target_level: Number(targetLevel) })
  }

  return (
    <Card className={styles.card} accent={tone}>
      <div className={styles.row}>
        <div>
          <h4>{title}</h4>
          <p>{subtitle || 'Current proficiency'}</p>
        </div>
        {typeof value === 'number' && <span className={styles.pill}>{value}%</span>}
      </div>
      {typeof value === 'number' && typeof target === 'number' && (
        <>
          <ProgressBar value={value} label="Current proficiency" color={tone} />
          <div className={styles.levelRow}>
            <span>Target <strong>{target}%</strong></span>
            <span className={styles.gap}>Gap <strong>{gap}%</strong></span>
          </div>
        </>
      )}
      {action && <p className={styles.action}>{action}</p>}
      {onSaveLevel && (
        <form className={styles.levelForm} onSubmit={saveLevels}>
          <label>Current %<input type="number" min="0" max="100" required value={currentLevel} onChange={event => setCurrentLevel(event.target.value)} /></label>
          <label>Target %<input type="number" min="0" max="100" required value={targetLevel} onChange={event => setTargetLevel(event.target.value)} /></label>
          <button type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save levels'}</button>
        </form>
      )}
    </Card>
  )
}
