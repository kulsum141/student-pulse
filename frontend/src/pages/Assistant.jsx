import { useState } from 'react'
import Card from '../components/Card'
import PageHeader from '../components/PageHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'
import { assistantApi, STUDENT_ID } from '../api'
import styles from './Assistant.module.css'

const initialMessages = [
  {
    id: 1,
    from: 'assistant',
    text: 'Hello! I can help you plan your next internship, skill move, or roadmap step.',
  },
]

export default function Assistant() {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [suggestions, setSuggestions] = useState(['What internship should I apply for?', 'What skills should I learn next?', 'Which hackathons are suitable for me?'])

  const sendMessage = async () => {
    if (!input.trim()) return

    const query = input.trim()
    const userMessage = { id: Date.now(), from: 'user', text: query }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const { data } = await assistantApi.ask(STUDENT_ID, query)
      setMessages(prev => [...prev, { id: Date.now() + 1, from: 'assistant', text: data.answer }])
      if (Array.isArray(data.suggestions)) setSuggestions(data.suggestions)
    } catch {
      setError('The assistant is temporarily unavailable right now.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader title="AI Assistant" subtitle="Get planning support tailored to your goals" />

      <Card className={styles.wrapper} accent="lavender">
        <div className={styles.chatBox}>
          {messages.map(message => (
            <div key={message.id} className={`${styles.bubble} ${message.from === 'user' ? styles.user : styles.assistant}`}>
              {message.text}
            </div>
          ))}

          {loading && <LoadingState text="Student Pulse AI is thinking..." />}
          {error && <ErrorState message={error} />}
        </div>

        <div className={styles.suggestions}>
          {suggestions.map(item => (
            <button key={item} className={styles.suggestion} onClick={() => setInput(item)}>
              {item}
            </button>
          ))}
        </div>

        <div className={styles.inputRow}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask Student Pulse AI..."
            onKeyDown={(event) => event.key === 'Enter' && sendMessage()}
          />
          <button className={styles.sendButton} onClick={sendMessage}>Send</button>
        </div>
      </Card>
    </>
  )
}
