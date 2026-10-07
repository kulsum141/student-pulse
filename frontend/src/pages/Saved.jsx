import { useEffect, useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { mockApi } from '../services/mockApi'
import styles from './Saved.module.css'

export default function Saved() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    mockApi.getSaved()
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

  return (
    <>
      <PageHeader title="Saved" subtitle="Keep track of opportunities worth revisiting" />
      <div className={styles.grid}>
        {items.map(item => (
          <Card key={item.id} accent={item.type === 'internship' ? 'lavender' : item.type === 'hackathon' ? 'pink' : 'sky'} className={styles.card}>
            <div className={styles.topRow}>
              <span className={styles.type}>{item.type}</span>
              <span className={styles.match}>{item.match}%</span>
            </div>
            <h3>{item.title}</h3>
            <p>{item.organization}</p>
            <small>{item.date}</small>
            <button className={styles.button}>View details</button>
          </Card>
        ))}
      </div>
    </>
  )
}
