import styles from './ErrorState.module.css'

export default function ErrorState({ message = 'Something went wrong while loading this section.' }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.icon}>⚠️</div>
      <p>{message}</p>
    </div>
  )
}
