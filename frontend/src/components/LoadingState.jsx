import styles from './LoadingState.module.css'

export default function LoadingState({ text = 'Loading...' }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.loader} />
      <p>{text}</p>
    </div>
  )
}
