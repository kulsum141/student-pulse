import Card from './Card'
import styles from './RoadmapNode.module.css'

export default function RoadmapNode({ item }) {
  const statusClass = item.status === 'done' ? styles.done : item.status === 'active' ? styles.active : styles.next

  return (
    <Card className={`${styles.node} ${statusClass}`} accent={item.status === 'done' ? 'mint' : item.status === 'active' ? 'lavender' : 'cream'}>
      <div className={styles.titleRow}>
        <span className={styles.dot} />
        <h3>{item.title}</h3>
      </div>
      <ul>
        {item.items.map(entry => (
          <li key={entry}>{entry}</li>
        ))}
      </ul>
    </Card>
  )
}
