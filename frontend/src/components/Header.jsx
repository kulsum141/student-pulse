import styles from './Header.module.css'

export default function Header({ title = 'Student Pulse', subtitle = 'Your growth dashboard' }) {
  return (
    <header className={styles.header}>
      <div className={styles.searchWrap}>
        <span className={styles.searchIcon} aria-hidden="true">⌕</span>
        <input
          aria-label="Search opportunities"
          type="search"
          placeholder="Search internships, hackathons, research papers..."
          className={styles.searchInput}
        />
      </div>

      <div className={styles.actions}>
        <button className={styles.iconButton} aria-label="Notifications">
          🔔
        </button>
        <button className={styles.iconButton} aria-label="Settings">
          ⚙️
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
