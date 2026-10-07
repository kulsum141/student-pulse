import Card from './Card'
import styles from './SkillCard.module.css'

export default function SkillCard({ title, subtitle, value, tone = 'lavender' }) {
  return (
    <Card className={styles.card} accent={tone}>
      <div className={styles.row}>
        <div>
          <h4>{title}</h4>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {typeof value === 'number' && <span className={styles.pill}>{value}%</span>}
      </div>
    </Card>
  )
}
