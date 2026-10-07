import Card from './Card'
import styles from './StatCard.module.css'

export default function StatCard({ label, value, accent = 'lavender' }) {
  return (
    <Card className={styles.card} accent={accent}>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{value}</div>
    </Card>
  )
}
