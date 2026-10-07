import styles from './SectionHeader.module.css'

export default function SectionHeader({ title, subtitle, action }) {
  return (
    <div className={styles.wrap}>
      <div>
        <h2 className={styles.title}>{title}</h2>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  )
}
