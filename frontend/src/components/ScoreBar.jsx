import styles from './ScoreBar.module.css'

export default function ScoreBar({ value = 0, label, color = 'lavender', showPct = true }) {
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100)
  return (
    <div className={styles.wrap}>
      {label && <div className={styles.label}>{label}</div>}
      <div className={styles.track}>
        <div className={`${styles.fill} ${styles[color]}`} style={{ width: `${pct}%` }} />
      </div>
      {showPct && <div className={styles.pct}>{pct}%</div>}
    </div>
  )
}
