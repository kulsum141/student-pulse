import {
  studentProfile,
  dashboardMetrics,
  recommendations,
  savedItems,
  roadmapData,
  skillGapData,
  assistantSuggestions,
  internshipList,
  hackathonList,
  researchList,
} from '../data/mockData'

export const mockApi = {
  getStudentProfile: async () => ({ data: studentProfile }),
  getDashboardData: async () => ({
    data: {
      metrics: dashboardMetrics,
      recommendations,
      saved: savedItems,
      roadmap: roadmapData,
      skillGap: skillGapData,
      assistantSuggestions,
    },
  }),
  getRoadmap: async () => ({ data: roadmapData }),
  getSkillGap: async () => ({ data: skillGapData }),
  getInternships: async () => ({ data: internshipList }),
  getHackathons: async () => ({ data: hackathonList }),
  getResearch: async () => ({ data: researchList }),
  getSaved: async () => ({ data: savedItems }),
  askAssistant: async () => ({
    data: {
      answer: 'Based on your current profile, the best next step is to deepen your AWS and cloud networking fundamentals while polishing your portfolio project. I would prioritize Terraform and Docker before applying for advanced internships.',
      suggestions: assistantSuggestions,
    },
  }),
}
