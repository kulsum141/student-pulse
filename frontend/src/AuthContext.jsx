import { createContext, useEffect, useState } from 'react'
import { authApi, setStudentId } from './api'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [student, setStudent] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    authApi.me()
      .then(({ data }) => {
        if (!active) return
        setStudent(data)
        setStudentId(data.student_id)
      })
      .catch(() => {
        if (!active) return
        setStudent(null)
        setStudentId('')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const login = async credentials => {
    const { data } = await authApi.login(credentials)
    setStudent(data.student)
    return data.student
  }

  const register = async profile => {
    const { data } = await authApi.register(profile)
    setStudent(data.student)
    return data.student
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } finally {
      setStudent(null)
      setStudentId('')
    }
  }

  return (
    <AuthContext.Provider value={{ student, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}