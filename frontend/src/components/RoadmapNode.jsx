import { useState } from 'react'
import { ArrowRight, Check, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import Card from './Card'
import ProgressBar from './ProgressBar'
import styles from './RoadmapNode.module.css'

export default function RoadmapNode({ item, onMarkComplete }) {
  const [detailsOpen, setDetailsOpen] = useState(false)
  const statusClass = item.status === 'done' ? styles.done : item.status === 'active' ? styles.active : styles.next
  const statusLabel = item.status === 'done' ? 'Completed' : item.status === 'active' ? 'Current stage' : 'Upcoming'

  return (
    <Card className={`${styles.node} ${statusClass}`} accent={item.status === 'done' ? 'mint' : item.status === 'active' ? 'lavender' : 'cream'}>
      <div className={styles.titleRow}>
        <span className={styles.dot}>{item.status === 'done' && <Check size={13} />}</span>
        <div className={styles.heading}>
          <span className={styles.status}>{statusLabel}</span>
          <h3>{item.title}</h3>
        </div>
      </div>
      <p className={styles.description}>{item.description}</p>
      <ProgressBar value={item.progress} label="Stage progress" color={item.status === 'done' ? 'mint' : item.status === 'active' ? 'lavender' : 'sky'} />
      <div className={styles.skills} aria-label="Relevant skills">
        {item.skills.map(skill => <span key={skill}>{skill}</span>)}
      </div>
      <ul className={styles.tasks}>
        {item.items.map(entry => <li key={entry}><CheckCircle2 size={14} />{entry}</li>)}
      </ul>
      {detailsOpen && <p className={styles.details}>{item.details}</p>}
      <div className={styles.actions}>
        {item.status === 'active' && (
          <Link to="/skill-gap" className={styles.continueButton}>Continue Learning <ArrowRight size={14} /></Link>
        )}
        <button type="button" className={styles.detailButton} aria-expanded={detailsOpen} onClick={() => setDetailsOpen(open => !open)}>
          {detailsOpen ? 'Hide Details' : 'View Details'} {detailsOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
        {item.status === 'active' && (
          <button type="button" className={styles.completeButton} onClick={() => onMarkComplete(item.title)}>Mark Complete</button>
        )}
      </div>
    </Card>
  )
}
