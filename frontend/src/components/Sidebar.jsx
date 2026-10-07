import { NavLink } from 'react-router-dom'
import styles from './Sidebar.module.css'

const NAV = [
  { to: '/dashboard', icon: '🏠', label: 'Dashboard' },
  { to: '/internships', icon: '💼', label: 'Internships' },
  { to: '/hackathons', icon: '🏆', label: 'Hackathons' },
  { to: '/research', icon: '�', label: 'Research Papers' },
  { to: '/roadmap', icon: '🗺️', label: 'Roadmap' },
  { to: '/skill-gap', icon: '📊', label: 'Skill Gap' },
  { to: '/recommendations', icon: '✨', label: 'Recommendations' },
  { to: '/assistant', icon: '🤖', label: 'AI Assistant' },
  { to: '/saved', icon: '🔖', label: 'Saved' },
  { to: '/profile', icon: '👤', label: 'Profile' },
  { to: '/settings', icon: '⚙️', label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.logo}>✨</span>
        <div className={styles.brandBlock}>
          <span className={styles.brandName}>Student Pulse</span>
          <small className={styles.brandTag}>Career dashboard</small>
        </div>
      </div>

      <div className={styles.profileSummary}>
        <div className={styles.avatar}>K</div>
        <div>
          <strong>Kulsum</strong>
          <small>3rd year • CS</small>
        </div>
      </div>

      <nav className={styles.nav}>
        {NAV.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
          >
            <span className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.footerCard}>
        <p className={styles.cardLabel}>Your next step</p>
        <h4>Complete 2 skills this week</h4>
        <button className={styles.cardButton}>View Roadmap</button>
      </div>
    </aside>
  )
}
