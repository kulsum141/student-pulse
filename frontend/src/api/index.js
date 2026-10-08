import axios from 'axios'
import { assistantSuggestions } from '../data/mockData'

const STUDENT_SESSION_KEY = 'student-pulse-student-id'
export let STUDENT_ID = ''
const BASE = import.meta.env.VITE_API_BASE_URL?.trim() || '/api'

export function setStudentId(studentId) {
  STUDENT_ID = studentId || ''
  if (typeof window !== 'undefined') {
    if (STUDENT_ID) window.sessionStorage.setItem(STUDENT_SESSION_KEY, STUDENT_ID)
    else window.sessionStorage.removeItem(STUDENT_SESSION_KEY)
  }
}

if (typeof window !== 'undefined') STUDENT_ID = window.sessionStorage.getItem(STUDENT_SESSION_KEY) || ''

export const api = axios.create({ baseURL: BASE, timeout: 15000, withCredentials: true })

api.interceptors.response.use(
  response => response,
  error => {
    const detail = error.response?.data?.detail
    error.message = detail
      ? String(detail)
      : error.response
        ? `Student Pulse API returned ${error.response.status}.`
        : 'Unable to reach the Student Pulse API. Check the backend connection.'
    return Promise.reject(error)
  },
)

function expectObject(response, label) {
  const value = response?.data
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`The ${label} response was invalid.`)
  }
  return value
}

function expectArray(response, label) {
  if (!Array.isArray(response?.data)) throw new Error(`The ${label} response was invalid.`)
  return response.data
}

function asList(value) {
  if (Array.isArray(value)) return value.map(String)
  if (typeof value === 'string') return value.split(',').map(item => item.trim()).filter(Boolean)
  return []
}

function toPercent(value) {
  const score = Number(value)
  if (!Number.isFinite(score)) return undefined
  return Math.round(Math.max(0, Math.min(100, score <= 1 ? score * 100 : score)))
}

function normalizeOpportunity(item, category) {
  const id = item.opportunity_id || item.hackathon_id || item.paper_id || item.item_id || item.id
  const labels = { internship: 'Internships', hackathon: 'Hackathons', research: 'Research', job: 'Jobs' }
  const normalizedCategory = labels[item.category] || category
  const type = normalizedCategory === 'Internships' ? 'internship' : normalizedCategory === 'Hackathons' ? 'hackathon' : normalizedCategory === 'Jobs' ? 'job' : 'paper'
  return {
    id: String(id || item.title || `${category} opportunity`),
    category: normalizedCategory,
    type,
    title: item.title || 'Untitled opportunity',
    organization: item.organization || item.company || item.organizer || item.journal || item.authors || 'Organization not provided',
    domain: item.domain || item.theme || category,
    location: item.location || item.mode || '',
    deadline: normalizedCategory === 'Research' ? '' : item.registration_deadline || item.deadline || '',
    match: toPercent(item.score ?? item.skill_overlap),
    skills: asList(item.required_skills || item.matched_skills || item.keywords || item.skills),
    description: item.description || item.abstract || item.explanation || '',
    experienceLevel: item.experience_level || 'Not specified',
    remote: item.remote,
    mode: item.mode,
    difficulty: item.difficulty_level,
    duration: item.duration || item.duration_months,
    teamSize: item.team_size_min != null
      ? `${item.team_size_min}${item.team_size_max != null ? `-${item.team_size_max}` : '+'}`
      : '',
    publishedYear: item.year,
    url: item.url,
    feedbackType: type === 'internship' || type === 'job' ? 'opportunity' : type === 'paper' ? 'paper' : 'hackathon',
  }
}

function mapListResponse(response, category) {
  return { ...response, data: expectArray(response, category).map(item => normalizeOpportunity(item, category)) }
}

export const profileApi = {
  getAll: async () => {
    const response = await api.get('/profile/')
    expectArray(response, 'profiles')
    return response
  },
  get: async id => {
    const response = await api.get(`/profile/${id}`)
    expectObject(response, 'student profile')
    return response
  },
  me: async () => {
    const response = await api.get('/auth/me')
    const profile = expectObject(response, 'student profile')
    setStudentId(profile.student_id)
    return response
  },
  update: async data => {
    const response = await api.put('/profile/me', data)
    expectObject(response, 'updated student profile')
    return response
  },
}

export const authApi = {
  register: async data => {
    const response = await api.post('/auth/register', data)
    const result = expectObject(response, 'registration')
    setStudentId(result.student?.student_id)
    return response
  },
  login: async credentials => {
    const response = await api.post('/auth/login', credentials)
    const result = expectObject(response, 'login')
    setStudentId(result.student?.student_id)
    return response
  },
  logout: async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      setStudentId('')
    }
  },
  me: () => profileApi.me(),
}

export const preferencesApi = {
  get: async id => {
    const response = await api.get(`/preferences/${id}`)
    expectObject(response, 'preferences')
    return response
  },
  save: async (id, data) => {
    const response = await api.post(`/preferences/${id}`, { student_id: id, ...data })
    expectObject(response, 'saved preferences')
    return response
  },
}

export const recommendationsApi = {
  get: async (id, params) => {
    const response = await api.get(`/recommendations/${id}`, { params })
    const result = expectObject(response, 'recommendations')
    for (const key of ['opportunities', 'papers', 'hackathons']) {
      if (!Array.isArray(result[key])) throw new Error(`The recommendations response is missing ${key}.`)
    }
    return response
  },
  feedback: async body => {
    const response = await api.post('/recommendations/feedback', body)
    const result = expectObject(response, 'recommendation feedback')
    if (typeof result.success !== 'boolean') throw new Error('The feedback response was invalid.')
    if (!result.success) throw new Error('The backend could not record this feedback.')
    return response
  },
  save: (studentId, item) => recommendationsApi.feedback({
    student_id: studentId,
    item_id: item.id,
    item_type: item.feedbackType,
    feedback_type: 'saved',
    title: item.title,
    organization: item.organization,
    description: item.description,
    skills: item.skills || [],
    location: item.location,
    deadline: item.deadline,
    url: item.url,
  }),
}

export const skillGapApi = {
  careerGoal: (id, goal) => api.get(`/skill-gap/${id}/career-goal`, { params: goal ? { goal } : {} }),
  forOpportunity: (id, targetId) => api.get(`/skill-gap/${id}/opportunity/${targetId}`),
  all: (id, params) => api.get(`/skill-gap/${id}/all`, { params }),
  forCareerGoal: async (id, goal) => {
    const [response, levelsResponse] = await Promise.all([
      api.get(`/skill-gap/${id}/career-goal`, { params: goal ? { goal } : {} }),
      skillsApi.list(id),
    ])
    const report = expectObject(response, 'skill gap')
    const matchedSkills = asList(report.matched_skills)
    const missingSkills = asList(report.missing_skills)
    const priorities = asList(report.priority_skills_to_learn)
    const priorityOrder = new Map(priorities.map((skill, index) => [skill.toLowerCase(), index]))
    const levelsByName = new Map(levelsResponse.data.map(skill => [skill.name.toLowerCase(), skill]))
    const skillLevels = [
      ...matchedSkills.map(name => ({ name, status: 'strong', action: 'Already listed as a skill match for this goal.' })),
      ...missingSkills.map(name => ({
        name,
        status: 'focus',
        priority: priorityOrder.get(name.toLowerCase()) ?? priorities.length,
        action: priorityOrder.has(name.toLowerCase()) ? 'Prioritized by the skill-gap analysis.' : 'Required for this career goal.',
      })),
    ].map(skill => ({ ...skill, ...levelsByName.get(skill.name.toLowerCase()) }))
    return {
      ...response,
      data: {
        targetCareer: report.target_title || 'Career goal',
        readiness: toPercent(report.readiness_score) ?? 0,
        currentSkills: asList(report.current_skills),
        requiredSkills: asList(report.required_skills),
        matchedSkills,
        missingSkills,
        recommendedSkills: priorities,
        skillLevels: skillLevels.sort((first, second) => (first.priority ?? -1) - (second.priority ?? -1)),
      },
    }
  },
  saveLevels: (id, skills) => skillsApi.save(id, skills),
}

export const roadmapApi = {
  get: (id, goal) => api.get(`/roadmap/${id}`, { params: goal ? { goal } : {} }),
  forPage: async (id, goal) => {
    const response = await api.get(`/roadmap/${id}`, { params: goal ? { goal } : {} })
    const result = expectObject(response, 'roadmap')
    if (!Array.isArray(result.steps)) throw new Error('The roadmap response is missing steps.')
    const progressResponse = await api.get(`/roadmap/${id}/progress`, {
      params: { career_goal: goal || result.career_goal },
    })
    const persistedProgress = expectArray(progressResponse, 'roadmap progress')
    const progressByStep = new Map(persistedProgress.map(item => [item.step_number, item]))

    const completed = asList(result.already_have)
    const completedSet = new Set(completed.map(skill => skill.toLowerCase()))
    let activeAssigned = false
    const steps = result.steps.map(step => {
      const skill = step.skill || 'Learning step'
      const persisted = progressByStep.get(step.step_number)
      const isCompleted = persisted ? persisted.completed : completedSet.has(skill.toLowerCase())
      const status = isCompleted ? 'done' : activeAssigned ? 'next' : 'active'
      if (!isCompleted) activeAssigned = true
      const resources = asList(step.suggested_resources)
      return {
        title: skill,
        stepNumber: step.step_number,
        status,
        progress: isCompleted ? 100 : 0,
        description: step.reason || `Build your ${skill} skill for ${result.career_goal}.`,
        skills: [skill],
        items: [`${step.resource_type || 'Learning'} · approximately ${step.estimated_weeks || 0} weeks`, ...resources],
        details: step.reason || resources.join(', '),
      }
    })
    const savedCompleted = steps.filter(step => step.status === 'done').map(step => step.title)
    const allCompleted = [...new Set([...completed, ...savedCompleted])]
    const allCompletedSet = new Set(allCompleted.map(skill => skill.toLowerCase()))
    const upcoming = asList(result.target_skills).filter(skill => !allCompletedSet.has(skill.toLowerCase()))
    const nextSteps = result.steps.slice(0, 4).map(step => ({
      title: `Learn ${step.skill}`,
      detail: `${step.resource_type || 'Learning'} · approximately ${step.estimated_weeks || 0} weeks`,
      to: step.resource_type === 'hackathon' ? '/hackathons' : step.resource_type === 'internship' ? '/internships' : step.resource_type === 'paper' ? '/research' : '/skill-gap',
    }))

    return {
      ...response,
      data: {
        careerGoal: result.career_goal || 'Career goal',
        progress: persistedProgress.length
          ? Math.round((steps.filter(step => step.status === 'done').length / Math.max(1, steps.length)) * 100)
          : toPercent(result.readiness_percentage) ?? 0,
        currentSkill: steps.find(step => step.status === 'active')?.title || '',
        completed: allCompleted,
        upcoming,
        steps,
        nextSteps,
        totalEstimatedWeeks: Number(result.total_estimated_weeks) || 0,
      },
    }
  },
  updateProgress: (id, data) => api.put(`/roadmap/${id}/progress`, data),
}

export const internshipsApi = {
  list: async params => mapListResponse(await api.get('/internships/', { params }), 'Internships'),
}

export const hackathonsApi = {
  list: async params => mapListResponse(await api.get('/hackathons/', { params }), 'Hackathons'),
}

export const researchApi = {
  list: async params => mapListResponse(await api.get('/research/', { params }), 'Research'),
}

export const savedApi = {
  list: async () => {
    const response = await api.get('/saved/')
    expectArray(response, 'saved opportunities')
    return response
  },
  remove: opportunityId => api.delete(`/saved/${encodeURIComponent(opportunityId)}`),
}

export const skillsApi = {
  list: async studentId => {
    const response = await api.get(`/skills/${studentId}`)
    expectArray(response, 'skill levels')
    return response
  },
  save: async (studentId, skills) => {
    const response = await api.put(`/skills/${studentId}`, { skills })
    expectArray(response, 'saved skill levels')
    return response
  },
}

export const assistantApi = {
  ask: async (student_id, query) => {
    const response = await api.post('/assistant/ask', { student_id, query })
    const result = expectObject(response, 'assistant')
    if (typeof result.answer !== 'string') throw new Error('The assistant response was invalid.')
    return response
  },
}

export const opportunitiesApi = {
  internships: params => internshipsApi.list(params),
  hackathons: params => hackathonsApi.list(params),
  research: params => researchApi.list(params),
  list: async params => {
    const response = await api.get('/opportunities/', { params })
    return { ...response, data: expectArray(response, 'application opportunities').map(item => normalizeOpportunity(item, 'Jobs')) }
  },
  discover: async studentId => {
    const [recommendationResponse, internshipResponse, hackathonResponse, researchResponse, databaseResponse] = await Promise.all([
      recommendationsApi.get(studentId),
      internshipsApi.list({ student_id: studentId, top_k: 25 }),
      hackathonsApi.list({ student_id: studentId, top_k: 25 }),
      researchApi.list({ student_id: studentId, top_k: 25 }),
      opportunitiesApi.list(),
    ])
    const recommendation = recommendationResponse.data
    const listings = [...internshipResponse.data, ...hackathonResponse.data, ...researchResponse.data]
    const listingById = new Map(listings.map(item => [item.id, item]))
    const featured = [
      ...recommendation.opportunities.map(item => normalizeOpportunity({ ...listingById.get(item.item_id), ...item }, 'Internships')),
      ...recommendation.hackathons.map(item => normalizeOpportunity({ ...listingById.get(item.item_id), ...item }, 'Hackathons')),
      ...recommendation.papers.map(item => normalizeOpportunity({ ...listingById.get(item.item_id), ...item }, 'Research')),
    ]
    const allItems = [...featured, ...listings, ...databaseResponse.data]
    const items = [...new Map(allItems.map(item => [item.id, item])).values()]
    return { data: { featured, items } }
  },
}

export const dashboardApi = {
  get: async studentId => {
    const [profileResponse, opportunityResponse, roadmapResponse, skillGapResponse, savedResponse] = await Promise.all([
      profileApi.get(studentId),
      opportunitiesApi.discover(studentId),
      roadmapApi.forPage(studentId),
      skillGapApi.forCareerGoal(studentId),
      savedApi.list(),
    ])
    const items = opportunityResponse.data.items
    const recommendations = {
      opportunities: opportunityResponse.data.featured.filter(item => item.category === 'Internships'),
      hackathons: opportunityResponse.data.featured.filter(item => item.category === 'Hackathons'),
      papers: opportunityResponse.data.featured.filter(item => item.category === 'Research'),
    }
    const metrics = [
      { label: 'Recommended Internships', value: String(items.filter(item => item.category === 'Internships').length), accent: 'lavender' },
      { label: 'Upcoming Hackathons', value: String(items.filter(item => item.category === 'Hackathons').length), accent: 'pink' },
      { label: 'Research Papers', value: String(items.filter(item => item.category === 'Research').length), accent: 'sky' },
      { label: 'Roadmap Progress', value: `${roadmapResponse.data.progress}%`, accent: 'mint' },
      { label: 'Skill Gap Score', value: `${skillGapResponse.data.readiness}%`, accent: 'peach' },
    ]
    return {
      data: {
        metrics,
        profile: profileResponse.data,
        recommendations,
        saved: savedResponse.data,
        roadmap: roadmapResponse.data,
        skillGap: skillGapResponse.data,
        assistantSuggestions,
      },
    }
  },
}
