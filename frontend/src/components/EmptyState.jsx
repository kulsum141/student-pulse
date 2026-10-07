import styles from './EmptyState.module.css'

export default function EmptyState({ title, description }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.icon}>✨</div>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
    </div>
  )
}
