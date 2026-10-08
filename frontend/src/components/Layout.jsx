import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import { useAuth } from '../hooks/useAuth'
import styles from './Layout.module.css'

export default function Layout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const { student, logout } = useAuth()

  return (
    <div className={styles.shell}>
      <Sidebar studentProfile={student} isOpen={mobileNavOpen} onNavigate={() => setMobileNavOpen(false)} onClose={() => setMobileNavOpen(false)} />
      <div className={styles.content}>
        <Header studentProfile={student} onLogout={logout} onMenuClick={() => setMobileNavOpen(open => !open)} />
        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
