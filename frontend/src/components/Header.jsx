import styles from './Header.module.css'

export default function Header({ title = 'Student Pulse', subtitle = 'Your growth dashboard' }) {
  return (
    <header className={styles.header}>
      <div>
        <p className={styles.kicker}>Student platform</p>
        <h1 className={styles.title}>{title}</h1>
      </div>

      <div className={styles.actions}>
        <button className={styles.iconButton} aria-label="Notifications">
          🔔
        </button>
        <div className={styles.userChip}>
          <span className={styles.avatar}>K</span>
          <div>
            <strong>Kulsum</strong>
            <small>{subtitle}</small>
          </div>
        </div>
      </div>
    </header>
  )
}
