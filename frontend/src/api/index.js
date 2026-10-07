import axios from 'axios'

const BASE = 'http://localhost:8000/api'

const api = axios.create({ baseURL: BASE, timeout: 15000 })

export const profileApi = {
  getAll: ()           => api.get('/profile/'),
  get: (id)            => api.get(`/profile/${id}`),
}

export const preferencesApi = {
  get:  (id)           => api.get(`/preferences/${id}`),
  save: (id, data)     => api.post(`/preferences/${id}`, { student_id: id, ...data }),
}

export const recommendationsApi = {
  get: (id, params)    => api.get(`/recommendations/${id}`, { params }),
  feedback: (body)     => api.post('/recommendations/feedback', body),
}

export const skillGapApi = {
  careerGoal: (id, goal) => api.get(`/skill-gap/${id}/career-goal`, { params: goal ? { goal } : {} }),
  forOpportunity: (id, targetId) => api.get(`/skill-gap/${id}/opportunity/${targetId}`),
  all:  (id, params)   => api.get(`/skill-gap/${id}/all`, { params }),
}

export const roadmapApi = {
  get: (id, goal)      => api.get(`/roadmap/${id}`, { params: goal ? { goal } : {} }),
}

export const internshipsApi = {
  list: (params)       => api.get('/internships/', { params }),
}

export const hackathonsApi = {
  list: (params)       => api.get('/hackathons/', { params }),
}

export const researchApi = {
  list: (params)       => api.get('/research/', { params }),
}

export const assistantApi = {
  ask: (student_id, query) => api.post('/assistant/ask', { student_id, query }),
}
