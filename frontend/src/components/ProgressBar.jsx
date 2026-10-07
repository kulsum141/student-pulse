import styles from './ProgressBar.module.css'

export default function ProgressBar({ value = 0, label, color = 'lavender' }) {
  const pct = Math.max(0, Math.min(100, Number(value) || 0))

  return (
    <div className={styles.wrap}>
      {label && <div className={styles.row}><span>{label}</span><strong>{pct}%</strong></div>}
      <div className={styles.track}>
        <div className={`${styles.fill} ${styles[color]}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
