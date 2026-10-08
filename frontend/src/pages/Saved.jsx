import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { savedApi } from '../api'
import styles from './Saved.module.css'

export default function Saved() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    savedApi.list()
      .then(({ data }) => {
        setItems(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Unable to load saved items.')
        setLoading(false)
      })
  }, [])

  if (loading) return <LoadingState text="Loading your saved items..." />
  if (error) return <ErrorState message={error} />

  const removeSaved = async opportunityId => {
    try {
      await savedApi.remove(opportunityId)
      setItems(current => current.filter(item => item.id !== opportunityId))
    } catch (requestError) {
      setError(requestError.message || 'Unable to remove this saved opportunity.')
    }
  }

  return (
    <>
      <PageHeader title="Saved Opportunities" subtitle="Keep track of opportunities worth revisiting" />
      {items.length > 0 ? <div className={styles.grid}>
        {items.map(item => (
          <Card key={item.id} accent={item.type === 'internship' ? 'lavender' : item.type === 'hackathon' ? 'pink' : 'sky'} className={styles.card}>
            <div className={styles.topRow}>
              <span className={styles.type}>{item.type}</span>
              <span className={styles.match}>Saved</span>
            </div>
            <h3>{item.title}</h3>
            <p>{item.organization}</p>
            <small>Saved {new Date(item.date).toLocaleDateString()}</small>
            <div className={styles.actions}>
              <Link className={styles.button} to={item.type === 'hackathon' ? '/hackathons' : item.type === 'paper' ? '/research' : '/opportunities'}>View opportunities</Link>
              <button type="button" className={styles.removeButton} onClick={() => removeSaved(item.id)}>Remove</button>
            </div>
          </Card>
        ))}
      </div> : <EmptyState title="Nothing saved yet" description="Save opportunities that you want to come back to." />}
      {error && <ErrorState message={error} />}
    </>
  )
}
