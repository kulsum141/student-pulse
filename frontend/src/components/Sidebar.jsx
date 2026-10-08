import { NavLink } from 'react-router-dom'
import {
  BookOpenText,
  BriefcaseBusiness,
  ChartNoAxesColumnIncreasing,
  ChevronRight,
  LayoutDashboard,
  Map,
  SlidersHorizontal,
  Sparkles,
  Trophy,
  UserRound,
  X,
} from 'lucide-react'
import styles from './Sidebar.module.css'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/opportunities', icon: Sparkles, label: 'Opportunities' },
  { to: '/internships', icon: BriefcaseBusiness, label: 'Internships' },
  { to: '/hackathons', icon: Trophy, label: 'Hackathons' },
  { to: '/research', icon: BookOpenText, label: 'Research Papers' },
  { to: '/roadmap', icon: Map, label: 'Roadmap' },
  { to: '/skill-gap', icon: ChartNoAxesColumnIncreasing, label: 'Skill Gap' },
  { to: '/assistant', icon: Sparkles, label: 'AI Assistant' },
  { to: '/profile', icon: UserRound, label: 'My Profile' },
  { to: '/customize', icon: SlidersHorizontal, label: 'Customize' },
]

export default function Sidebar({ studentProfile, isOpen, onNavigate, onClose }) {
  const studentName = studentProfile?.name || 'Kulsum'
  const studentDepartment = studentProfile?.department || 'Computer Science'
  const studentYear = studentProfile?.year_of_study || 3

  return (
    <>
      <button
        type="button"
        className={`${styles.scrim} ${isOpen ? styles.scrimVisible : ''}`}
        aria-label="Close navigation"
        onClick={onClose}
        tabIndex={isOpen ? 0 : -1}
      />
      <aside className={`${styles.sidebar} ${isOpen ? styles.sidebarOpen : ''}`}>
      <div className={styles.brand}>
        <span className={styles.logo}><Sparkles size={19} strokeWidth={2.4} /></span>
        <div className={styles.brandBlock}>
          <span className={styles.brandName}>Student Pulse</span>
          <small className={styles.brandTag}>Your next chapter starts here</small>
        </div>
        <button type="button" className={styles.closeButton} aria-label="Close navigation" onClick={onClose}>
          <X size={19} />
        </button>
      </div>

      <div className={styles.profileSummary}>
        <div className={styles.avatar}>{studentName.charAt(0)}</div>
        <div>
          <strong>{studentName}</strong>
          <small>{studentDepartment} · Year {studentYear}</small>
        </div>
      </div>

      <p className={styles.navCaption}>YOUR SPACE</p>
      <nav className={styles.nav}>
        {NAV.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            end={item.to === '/dashboard'}
            className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
          >
            <item.icon className={styles.icon} size={18} strokeWidth={1.9} />
            <span className={styles.label}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.footerCard}>
        <p className={styles.cardLabel}>Your next step</p>
        <h4>Small steps make big futures.</h4>
        <NavLink to="/roadmap" className={styles.cardButton} onClick={onNavigate}>
          View your roadmap <ChevronRight size={15} />
        </NavLink>
      </div>
      </aside>
    </>
  )
}
