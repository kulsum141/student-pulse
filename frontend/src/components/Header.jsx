import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell, BriefcaseBusiness, LogOut, Menu, Search, Settings2, X } from 'lucide-react'
import styles from './Header.module.css'

export default function Header({ onMenuClick, onLogout, studentProfile }) {
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const studentName = studentProfile?.name || 'Kulsum'
  const studentDepartment = studentProfile?.department || 'Computer Science'
  const studentYear = studentProfile?.year_of_study || 3

  return (
    <header className={styles.header}>
      <button type="button" className={styles.menuButton} aria-label="Open navigation" onClick={onMenuClick}>
        <Menu size={20} />
      </button>
      <div className={styles.searchWrap}>
        <Search className={styles.searchIcon} size={18} aria-hidden="true" />
        <input
          aria-label="Search Student Pulse"
          type="search"
          placeholder="Search opportunities, skills, and more"
          className={styles.searchInput}
        />
      </div>

      <div className={styles.actions}>
        <div className={styles.notificationWrap}>
          <button
            type="button"
            className={`${styles.iconButton} ${notificationsOpen ? styles.iconButtonActive : ''}`}
            aria-label="Notifications"
            aria-expanded={notificationsOpen}
            onClick={() => setNotificationsOpen(open => !open)}
          >
            <Bell size={18} />
            <span className={styles.notificationDot} />
          </button>
          {notificationsOpen && (
            <div className={styles.notificationPanel} aria-label="Recent notifications">
              <div className={styles.notificationHeading}>
                <strong>You are right on time</strong>
                <button type="button" aria-label="Close notifications" onClick={() => setNotificationsOpen(false)}>
                  <X size={16} />
                </button>
              </div>
              <Link to="/internships" className={styles.notificationItem} onClick={() => setNotificationsOpen(false)}>
                <span className={styles.notificationIcon}><BriefcaseBusiness size={16} /></span>
                <span><strong>Application window closing soon</strong><small>Cloud internship · 3 days left</small></span>
              </Link>
              <Link to="/roadmap" className={styles.notificationItem} onClick={() => setNotificationsOpen(false)}>
                <span className={styles.notificationIcon}><Settings2 size={16} /></span>
                <span><strong>Your next roadmap step is ready</strong><small>Pick up where you left off</small></span>
              </Link>
            </div>
          )}
        </div>
        <Link to="/customize" className={styles.iconButton} aria-label="Customize settings" title="Customize settings">
          <Settings2 size={18} />
        </Link>
        <button type="button" className={styles.iconButton} aria-label="Sign out" title="Sign out" onClick={onLogout}>
          <LogOut size={18} />
        </button>
        <Link to="/profile" className={styles.userChip} aria-label={`View ${studentName}'s profile`}>
          <span className={styles.avatar}>{studentName.charAt(0)}</span>
          <div><strong>{studentName}</strong><small>{studentDepartment} · Year {studentYear}</small></div>
        </Link>
      </div>
    </header>
  )
}
