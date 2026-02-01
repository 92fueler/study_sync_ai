import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth tokens if needed
apiClient.interceptors.request.use((config) => {
  // Add auth token if available
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default apiClient

// API endpoints
export const uploadFiles = async (
  userId: string,
  files: File[],
  onProgress?: (percent: number) => void
) => {
  const formData = new FormData()
  formData.append('user_id', userId)
  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return
      const percent = Math.min(100, Math.round((event.loaded / event.total) * 100))
      onProgress(percent)
    },
  })
  return response.data
}

export const getUploadStatus = async (taskId: string) => {
  const response = await apiClient.get(`/upload/status/${taskId}`)
  return response.data
}

export const createProfile = async (profileData: any) => {
  const response = await apiClient.post('/profile', profileData)
  return response.data
}

export const getProfile = async (userId: string) => {
  const response = await apiClient.get(`/profile/${userId}`)
  return response.data
}

export const updateProfile = async (userId: string, updateData: any) => {
  const response = await apiClient.put(`/profile/${userId}`, updateData)
  return response.data
}

export const listArtifacts = async (userId: string, artifactType?: string) => {
  const params = new URLSearchParams({ user_id: userId })
  if (artifactType) {
    params.append('type', artifactType)
  }
  const response = await apiClient.get(`/artifacts?${params.toString()}`)
  return response.data
}

export const getArtifact = async (artifactId: string) => {
  const response = await apiClient.get(`/artifacts/${artifactId}`)
  return response.data
}

export const getNotifications = async (userId: string, unreadOnly = false) => {
  const response = await apiClient.get(
    `/notifications?user_id=${userId}&unread_only=${unreadOnly}`
  )
  return response.data
}

export const getNotificationBadge = async (userId: string) => {
  const response = await apiClient.get(`/notifications/badge?user_id=${userId}`)
  return response.data
}

export const markNotificationRead = async (notificationId: string, userId: string) => {
  const response = await apiClient.post(`/notifications/${notificationId}/read?user_id=${userId}`)
  return response.data
}

export const getGoogleCalendarAuthUrl = async (userId: string) => {
  const response = await apiClient.get(`/calendar/google/auth-url?user_id=${userId}`)
  return response.data
}

export const syncGoogleCalendar = async (payload: {
  user_id: string
  time_min?: string
  time_max?: string
  calendar_id?: string
}) => {
  const response = await apiClient.post(`/calendar/google/sync`, payload)
  return response.data
}

export const createIngestionJob = async (payload: {
  user_id: string
  name: string
  job_type: string
  status?: string
  progress?: number
  metadata?: Record<string, unknown>
}) => {
  const response = await apiClient.post('/ingestion', payload)
  return response.data
}

export const createNote = async (payload: {
  user_id: string
  note_type: string
  title: string
  description?: string
  tags?: Array<{ type: string; label: string }> | string[]
  author?: string
  topic?: string
  thumbnail_url?: string
  source_id?: string
}) => {
  const response = await apiClient.post('/notes', payload)
  return response.data
}

export const listNotes = async (
  userId: string,
  options?: { topic?: string; limit?: number; offset?: number }
) => {
  const params = new URLSearchParams({ user_id: userId })
  if (options?.topic) params.append('topic', options.topic)
  if (options?.limit) params.append('limit', String(options.limit))
  if (options?.offset) params.append('offset', String(options.offset))
  const response = await apiClient.get(`/notes?${params.toString()}`)
  return response.data
}

export const listRecentNotes = async (userId: string, limit = 6) => {
  const response = await apiClient.get(`/notes/recent?user_id=${userId}&limit=${limit}`)
  return response.data
}

export const listNoteTopics = async (userId: string) => {
  const response = await apiClient.get(`/notes/topics?user_id=${userId}`)
  return response.data
}

export const getNote = async (noteId: string, userId: string) => {
  const response = await apiClient.get(`/notes/${noteId}?user_id=${userId}`)
  return response.data
}

export const listLearningPlans = async (
  userId: string,
  options?: { status?: string; limit?: number; offset?: number }
) => {
  const params = new URLSearchParams({ user_id: userId })
  if (options?.status) params.append('status', options.status)
  if (options?.limit) params.append('limit', String(options.limit))
  if (options?.offset) params.append('offset', String(options.offset))
  const response = await apiClient.get(`/learning-plans?${params.toString()}`)
  return response.data
}

export const listProposedLearningPlans = async (
  userId: string,
  options?: { limit?: number; offset?: number }
) => {
  const params = new URLSearchParams({ user_id: userId })
  if (options?.limit) params.append('limit', String(options.limit))
  if (options?.offset) params.append('offset', String(options.offset))
  const response = await apiClient.get(`/learning-plans/proposed?${params.toString()}`)
  return response.data
}

export const approveLearningPlan = async (planId: string, userId: string) => {
  const response = await apiClient.post(`/learning-plans/${planId}/approve?user_id=${userId}`)
  return response.data
}

export const createLearningPlan = async (payload: {
  user_id: string
  title?: string
  description?: string
  goal?: string
  status?: string
  difficulty?: string
  category?: string
  category_color?: string
  estimated_time?: string
  module_count?: number
  details?: Record<string, unknown>
  metadata?: Record<string, unknown>
}) => {
  const response = await apiClient.post('/learning-plans', payload)
  return response.data
}

export const getLearningPlan = async (planId: string, userId: string) => {
  const response = await apiClient.get(`/learning-plans/${planId}?user_id=${userId}&include_items=true`)
  return response.data
}

export const updateLearningPlan = async (planId: string, userId: string, payload: {
  title?: string
  description?: string
  goal?: string
  status?: string
  difficulty?: string
  category?: string
  category_color?: string
  estimated_time?: string
  module_count?: number
  details?: Record<string, unknown>
  metadata?: Record<string, unknown>
}) => {
  const response = await apiClient.patch(`/learning-plans/${planId}?user_id=${userId}`, payload)
  return response.data
}

export const updateSettings = async (userId: string, payload: {
  theme?: string
  notifications?: Record<string, unknown>
  timezone?: string
  study_preferences?: Record<string, unknown>
}) => {
  const response = await apiClient.patch(`/settings/${userId}`, payload)
  return response.data
}

export const getSettings = async (userId: string) => {
  const response = await apiClient.get(`/settings/${userId}`)
  return response.data
}

export const searchAll = async (userId: string, query: string, limit = 10) => {
  const params = new URLSearchParams({ user_id: userId, q: query, limit: String(limit) })
  const response = await apiClient.get(`/search?${params.toString()}`)
  return response.data
}
