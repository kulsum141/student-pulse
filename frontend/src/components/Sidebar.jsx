import { NavLink } from 'react-router-dom'
import styles from './Sidebar.module.css'

const NAV = [
  { to: '/dashboard',   icon: '🏠', label: 'Dashboard'    },
  { to: '/roadmap',     icon: '🗺️',  label: 'My Roadmap'   },
  { to: '/skill-gap',   icon: '📊', label: 'Skill Gap'    },
  { to: '/internships', icon: '💼', label: 'Internships'  },
  { to: '/hackathons',  icon: '🏆', label: 'Hackathons'   },
  { to: '/research',    icon: '📄', label: 'Research'     },
  { to: '/assistant',   icon: '🤖', label: 'AI Assistant' },
]

const BOTTOM = [
  { to: '/profile',   icon: '👤', label: 'Profile'    },
  { to: '/customize', icon: '🎨', label: 'Customize'  },
]

export default function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.logo}>✨</span>
        <span className={styles.brandName}>StudentPulse</span>
      </div>

      <nav className={styles.nav}>
        {NAV.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            <span className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.divider} />

      <nav className={styles.nav}>
        {BOTTOM.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            <span className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.footer}>
        <div className={styles.status}>
          <span className={styles.dot} />
          ML Engine Active
        </div>
      </div>
    </aside>
  )
}
