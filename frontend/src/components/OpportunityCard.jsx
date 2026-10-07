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
}) {
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
        {location && <span>{location}</span>}
        {deadline && <span>{deadline}</span>}
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
        <button className={styles.secondary}>{secondaryLabel}</button>
        <button className={styles.primary}>{actionLabel}</button>
      </div>
    </Card>
  )
}
