import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Bookmark, BookmarkCheck, CalendarDays, MapPin } from 'lucide-react'
import Card from './Card'
import styles from './OpportunityCard.module.css'

export default function OpportunityCard({
  title,
  organization,
  domain,
  location,
  deadline,
  match,
  skills = [],
  description,
  type = 'opportunity',
  actionLabel = 'View',
  secondaryLabel = 'Save',
  detailTo,
  onSave,
}) {
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState('')

  const saveOpportunity = async () => {
    if (saved) return
    try {
      await onSave?.()
      setSaved(true)
      setSaveError('')
    } catch (error) {
      setSaveError(error.message || 'Unable to save this opportunity.')
    }
  }

  return (
    <Card className={styles.card} accent={type === 'internship' ? 'lavender' : type === 'hackathon' ? 'pink' : 'sky'}>
      <div className={styles.topRow}>
        <span className={styles.type}>{type}</span>
        {typeof match === 'number' && <span className={styles.score}>{match}% match</span>}
      </div>

      <h3 className={styles.title}>{title}</h3>
      <p className={styles.org}>{organization}</p>

      <div className={styles.metaRow}>
        {domain && <span>{domain}</span>}
        {location && <span><MapPin size={13} aria-hidden="true" />{location}</span>}
        {deadline && <span><CalendarDays size={13} aria-hidden="true" />{deadline}</span>}
      </div>

      {description && <p className={styles.description}>{description}</p>}

      {skills.length > 0 && (
        <div className={styles.tagList}>
          {skills.map(skill => (
            <span key={skill} className={styles.tag}>{skill}</span>
          ))}
        </div>
      )}

      <div className={styles.actions}>
        <button
          type="button"
          className={`${styles.secondary} ${saved ? styles.saved : ''}`}
          aria-pressed={saved}
          disabled={saved}
          onClick={saveOpportunity}
        >
          {saved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
          {saved ? 'Saved' : secondaryLabel}
        </button>
        {detailTo ? (
          <Link className={styles.primary} to={detailTo}>
            {actionLabel}<ArrowUpRight size={15} />
          </Link>
        ) : (
          <button type="button" className={styles.primary}>
            {actionLabel}<ArrowUpRight size={15} />
          </button>
        )}
      </div>
      {saveError && <p className={styles.saveError} role="alert">{saveError}</p>}
    </Card>
  )
}
