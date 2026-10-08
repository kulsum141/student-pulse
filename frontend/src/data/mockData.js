export const studentProfile = {
  student_id: 'S001',
  name: 'Kulsum',
  email: 'kulsum@studentpulse.dev',
  department: 'Computer Science',
  year_of_study: 3,
  cgpa: 8.9,
  skills: ['Python', 'JavaScript', 'Data Analysis', 'SQL', 'Machine Learning'],
  interests: ['Web Development', 'Cloud Computing', 'AI/ML', 'Data Science'],
  preferred_location: 'Bengaluru',
  open_to_remote: true,
  career_goal: 'Cloud Engineer',
  past_internships: 2,
  courses_completed: ['Data Structures', 'Operating Systems', 'DBMS', 'Cloud Fundamentals'],
  language_known: ['English', 'Hindi', 'Kannada'],
}

export const dashboardMetrics = [
  { label: 'Recommended Internships', value: '12', accent: 'lavender' },
  { label: 'Upcoming Hackathons', value: '4', accent: 'pink' },
  { label: 'Research Papers', value: '9', accent: 'sky' },
  { label: 'Roadmap Progress', value: '68%', accent: 'mint' },
  { label: 'Skill Gap Score', value: '82%', accent: 'peach' },
]

export const recommendations = {
  opportunities: [
    {
      id: 'INT-204',
      type: 'internship',
      title: 'Software Engineering Intern',
      organization: 'Nimbus Cloud',
      domain: 'Cloud Infrastructure',
      location: 'Bengaluru',
      deadline: '12 Aug 2026',
      match: 92,
      skills: ['Python', 'AWS', 'Linux'],
      description: 'Build scalable cloud tooling and automation workflows for student-first products.',
    },
    {
      id: 'INT-118',
      type: 'internship',
      title: 'Full Stack Developer Intern',
      organization: 'Pioneer Labs',
      domain: 'Web Platforms',
      location: 'Remote',
      deadline: '18 Aug 2026',
      match: 89,
      skills: ['React', 'Node.js', 'REST APIs'],
      description: 'Build product dashboards and improve developer experience for internal tools.',
    },
  ],
  hackathons: [
    {
      id: 'HCK-07',
      type: 'hackathon',
      title: 'AI for Sustainability',
      organization: 'DataForge',
      domain: 'AI & Climate',
      location: 'Hybrid',
      deadline: '24 Aug 2026',
      match: 88,
      skills: ['Python', 'Modeling', 'Analytics'],
      description: 'Create AI-powered solutions for climate resilience using open public datasets.',
    },
    {
      id: 'HCK-14',
      type: 'hackathon',
      title: 'Build with Cloud',
      organization: 'CloudNest',
      domain: 'Cloud',
      location: 'Online',
      deadline: '03 Sep 2026',
      match: 84,
      skills: ['Terraform', 'AWS', 'DevOps'],
      description: 'Design resilient cloud architectures and automation workflows for modern apps.',
    },
  ],
  papers: [
    {
      id: 'PAP-33',
      type: 'paper',
      title: 'Efficient Feature Selection for Predictive Learning',
      organization: 'ACM Research',
      domain: 'Machine Learning',
      location: 'N/A',
      deadline: 'N/A',
      match: 90,
      skills: ['Machine Learning', 'Statistics', 'Python'],
      description: 'Recent work on dimensionality reduction and model explainability for educational systems.',
    },
    {
      id: 'PAP-41',
      type: 'paper',
      title: 'Edge AI for Smart Campus Systems',
      organization: 'IEEE Papers',
      domain: 'Embedded AI',
      location: 'N/A',
      deadline: 'N/A',
      match: 85,
      skills: ['AI', 'IoT', 'Python'],
      description: 'Research on low-latency AI inference on campus-scale device networks.',
    },
  ],
}

export const savedItems = [
  {
    id: 'INT-204',
    type: 'internship',
    title: 'Software Engineering Intern',
    organization: 'Nimbus Cloud',
    match: 92,
    date: 'Saved today',
  },
  {
    id: 'HCK-07',
    type: 'hackathon',
    title: 'AI for Sustainability',
    organization: 'DataForge',
    match: 88,
    date: 'Saved 2 days ago',
  },
  {
    id: 'PAP-33',
    type: 'paper',
    title: 'Efficient Feature Selection for Predictive Learning',
    organization: 'ACM Research',
    match: 90,
    date: 'Saved this week',
  },
]

export const roadmapData = {
  careerGoal: 'Cloud Engineer',
  progress: 68,
  currentSkill: 'AWS Networking',
  completed: ['Python Basics', 'Linux Fundamentals', 'Git & GitHub', 'Data Structures'],
  upcoming: ['Terraform', 'Kubernetes', 'Docker', 'System Design'],
  nextSteps: [
    { title: 'Finish AWS networking fundamentals', detail: 'Review VPCs, subnets, routing, and security groups.', to: '/skill-gap' },
    { title: 'Build a small cloud-hosted project', detail: 'Deploy one portfolio project and document its architecture.', to: '/roadmap' },
    { title: 'Practice infrastructure as code', detail: 'Create a reusable Terraform setup for your project.', to: '/skill-gap' },
    { title: 'Find a cloud-focused internship', detail: 'Explore roles that match your current strengths.', to: '/internships' },
  ],
  steps: [
    {
      title: 'Foundation',
      status: 'done',
      progress: 100,
      description: 'Build the programming and computer science fundamentals that support your cloud journey.',
      skills: ['Python', 'Linux', 'Git'],
      items: ['Python basics', 'Linux fundamentals', 'Git & GitHub'],
      details: 'Your core foundations are in place. Keep them fresh as you move into cloud infrastructure.',
    },
    {
      title: 'Skill Building',
      status: 'active',
      progress: 72,
      description: 'Develop the networking and cloud knowledge needed to design reliable systems.',
      skills: ['AWS', 'Networking', 'Containers'],
      items: ['Review AWS networking', 'Practice VPC and subnet design', 'Learn Docker fundamentals'],
      details: 'Focus on AWS Networking next, then connect those concepts to containers and deployment.',
    },
    {
      title: 'Projects',
      status: 'next',
      progress: 0,
      description: 'Turn new skills into a portfolio project you can explain and demonstrate.',
      skills: ['Terraform', 'CI/CD', 'Cloud architecture'],
      items: ['Choose a portfolio project', 'Provision resources with Terraform', 'Document a CI/CD workflow'],
      details: 'A small, well-documented deployment is a strong way to show practical cloud experience.',
    },
    {
      title: 'Opportunities',
      status: 'next',
      progress: 0,
      description: 'Apply your growing skills in internships, hackathons, and collaborative work.',
      skills: ['Teamwork', 'Problem solving', 'Technical communication'],
      items: ['Join a cloud or infrastructure hackathon', 'Shortlist relevant internships', 'Prepare a project walkthrough'],
      details: 'Look for roles that match your current strengths while giving you room to grow.',
    },
    {
      title: 'Career Preparation',
      status: 'next',
      progress: 0,
      description: 'Prepare to communicate your experience clearly and confidently.',
      skills: ['System design', 'Interview practice', 'Portfolio'],
      items: ['Practice system design fundamentals', 'Polish your resume and portfolio', 'Rehearse technical interviews'],
      details: 'Bring your project decisions, trade-offs, and lessons learned into your interview stories.',
    },
  ],
}

export const skillGapData = {
  currentSkills: ['Python', 'JavaScript', 'SQL', 'Git', 'Linux'],
  targetCareer: 'Cloud Engineer',
  requiredSkills: ['AWS', 'Terraform', 'Docker', 'Kubernetes', 'Networking'],
  missingSkills: ['Terraform', 'Kubernetes', 'Docker', 'Networking'],
  recommendedSkills: ['AWS Certified Cloud Practitioner', 'Docker Bootcamp', 'Terraform labs'],
  readiness: 82,
  skillLevels: [
    { name: 'Python', current: 78, target: 90, gap: 12, status: 'strong', priority: 4, action: 'Build a small automation script for a cloud task.' },
    { name: 'DSA', current: 54, target: 80, gap: 26, status: 'focus', priority: 3, action: 'Practice a few data structure problems each week.' },
    { name: 'Web Development', current: 72, target: 85, gap: 13, status: 'strong', priority: 5, action: 'Add a polished project page to your portfolio.' },
    { name: 'Cloud Computing', current: 58, target: 85, gap: 27, status: 'focus', priority: 1, action: 'Complete an AWS networking and deployment lab.' },
    { name: 'Machine Learning', current: 64, target: 80, gap: 16, status: 'focus', priority: 2, action: 'Apply core concepts in a small data project.' },
    { name: 'Git/GitHub', current: 88, target: 90, gap: 2, status: 'strong', priority: 6, action: 'Keep your project history clear and easy to review.' },
  ],
  learningActions: [
    { title: 'Complete a course', detail: 'Build a guided foundation in cloud concepts.', to: '/roadmap', tone: 'lavender' },
    { title: 'Practice problems', detail: 'Strengthen DSA with consistent short sessions.', to: '/roadmap', tone: 'pink' },
    { title: 'Build a project', detail: 'Apply cloud and web skills in a portfolio project.', to: '/roadmap', tone: 'sky' },
    { title: 'Join a hackathon', detail: 'Collaborate and practice solving open-ended problems.', to: '/hackathons', tone: 'mint' },
    { title: 'Apply for an internship', detail: 'Put your growing skills to work with a team.', to: '/internships', tone: 'peach' },
  ],
}

export const assistantSuggestions = [
  'What internship should I apply for?',
  'What skills should I learn next?',
  'Which hackathons are suitable for me?',
  'Give me a roadmap for cloud engineering.',
]

export const internshipList = [
  { id: 'INT-204', title: 'Software Engineering Intern', organization: 'Nimbus Cloud', type: 'Internship', location: 'Bengaluru', remote: false, domain: 'Cloud', duration: '6 months', deadline: '12 Aug 2026', match: 92, skills: ['Python', 'AWS', 'Linux'] },
  { id: 'INT-118', title: 'Full Stack Developer Intern', organization: 'Pioneer Labs', type: 'Internship', location: 'Remote', remote: true, domain: 'Web Development', duration: '4 months', deadline: '18 Aug 2026', match: 89, skills: ['React', 'API', 'Node.js'] },
  { id: 'INT-087', title: 'ML Research Intern', organization: 'Vector AI', type: 'Research', location: 'Hyderabad', remote: false, domain: 'AI', duration: '5 months', deadline: '05 Sep 2026', match: 86, skills: ['Python', 'ML', 'NLP'] },
]

export const hackathonList = [
  { id: 'HCK-07', title: 'AI for Sustainability', organization: 'DataForge', mode: 'Hybrid', difficulty: 'Intermediate', domain: 'AI', deadline: '24 Aug 2026', teamSize: '2-4', match: 88 },
  { id: 'HCK-14', title: 'Build with Cloud', organization: 'CloudNest', mode: 'Online', difficulty: 'Beginner', domain: 'Cloud', deadline: '03 Sep 2026', teamSize: 'Solo/Team', match: 84 },
  { id: 'HCK-19', title: 'Cyber Security Sprint', organization: 'SecureStack', mode: 'Offline', difficulty: 'Advanced', domain: 'Security', deadline: '11 Sep 2026', teamSize: '3-5', match: 80 },
]

export const researchList = [
  { id: 'PAP-33', title: 'Efficient Feature Selection for Predictive Learning', organization: 'ACM Research', domain: 'Machine Learning', difficulty: 'Advanced', date: '2026-06-18', match: 90 },
  { id: 'PAP-41', title: 'Edge AI for Smart Campus Systems', organization: 'IEEE Papers', domain: 'Embedded AI', difficulty: 'Intermediate', date: '2026-05-11', match: 85 },
  { id: 'PAP-22', title: 'Reliable Distributed Storage for Education Platforms', organization: 'Springer', domain: 'Distributed Systems', difficulty: 'Advanced', date: '2026-02-20', match: 83 },
]

export const profileSections = {
  education: {
    degree: 'B.E. in Computer Science',
    university: 'BMS Institute of Technology',
    graduation: '2027',
    cgpa: '8.9/10',
  },
  customization: {
    interests: ['Web Development', 'Cloud Computing', 'AI/ML'],
    career_goals: ['Cloud Engineer', 'Software Engineer'],
    opportunity_preferences: ['Internships', 'Hackathons', 'Research Papers'],
  },
}
