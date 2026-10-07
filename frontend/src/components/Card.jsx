import styles from './Card.module.css'

export default function Card({ children, className = '', accent, style }) {
  return (
    <div
      className={`${styles.card} ${accent ? styles[accent] : ''} ${className}`}
      style={style}
    >
      {children}
    </div>
  )
}
