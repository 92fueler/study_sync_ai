import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

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

// Response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error(
        'Backend connection failed. Make sure the gateway is running:\n' +
        '  docker-compose up -d gateway\n' +
        '  or\n' +
        '  ./scripts/startup/start-backend.sh'
      )
    }
    return Promise.reject(error)
  }
)

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

export const getContent = async (userId: string, contentId: string, includeRaw = false) => {
  const params = new URLSearchParams({ user_id: userId })
  if (includeRaw) {
    params.append('include_raw', 'true')
  }
  const response = await apiClient.get(`/content/${contentId}?${params.toString()}`)
  return response.data
}

export const listContent = async (
  userId: string,
  options?: { limit?: number; offset?: number; status?: string; sort?: string }
) => {
  const params = new URLSearchParams({ user_id: userId })
  if (options?.limit) params.append('limit', String(options.limit))
  if (options?.offset) params.append('offset', String(options.offset))
  if (options?.status) params.append('status', options.status)
  if (options?.sort) params.append('sort', options.sort)
  const response = await apiClient.get(`/content?${params.toString()}`)
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

export const pauseLearningPlan = async (planId: string, userId: string) => {
  const response = await apiClient.post(`/learning-plans/${planId}/pause?user_id=${userId}`)
  return response.data
}

export const resumeLearningPlan = async (planId: string, userId: string) => {
  const response = await apiClient.post(`/learning-plans/${planId}/resume?user_id=${userId}`)
  return response.data
}

export const generateSuggestedPlans = async (
  userId: string,
  contextMode: string = 'growth',
  maxPlans: number = 3
) => {
  const params = new URLSearchParams({ user_id: userId, context_mode: contextMode, max_plans: String(maxPlans) })
  const response = await apiClient.post(`/learning-plans/generate-suggested?${params.toString()}`)
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

export const deleteLearningPlan = async (planId: string, userId: string) => {
  const response = await apiClient.delete(`/learning-plans/${planId}?user_id=${userId}`)
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

export const getPriorityQueue = async (userId: string, limit = 10) => {
  const params = new URLSearchParams({ user_id: userId, limit: String(limit) })
  const response = await apiClient.get(`/queue?${params.toString()}`)
  return response.data
}

export const recalculatePriority = async (userId: string) => {
  const params = new URLSearchParams({ user_id: userId })
  const response = await apiClient.get(`/queue/recalculate?${params.toString()}`)
  return response.data
}

// Audio API
export const getAudioMetadata = async (artifactId: string) => {
  const response = await apiClient.get(`/audio/metadata/${artifactId}`)
  return response.data
}

export const getAudioUrl = (filename: string) => {
  return `${API_BASE_URL}/audio/${filename}`
}

// Video API
export type VideoMetadata = {
  status: string
  video_url?: string | null
  duration_seconds?: number | null
  file_size_bytes?: number | null
  resolution?: string | null
  aspect_ratio?: string | null
  generated_at?: string | null
  progress?: number
  current_segment?: number
  total_segments?: number
  error_message?: string | null
  error_code?: string | null
}

export const getVideoMetadata = async (artifactId: string) => {
  const response = await apiClient.get<VideoMetadata>(`/video/metadata/${artifactId}`)
  return response.data as VideoMetadata
}

export const generateVideo = async (
  artifactId: string,
  payload: { user_id: string; total_duration?: number },
  options?: { retry?: boolean; force?: boolean }
) => {
  const params = new URLSearchParams()
  if (options?.retry) params.set('retry', '1')
  if (options?.force) params.set('force', '1')
  const query = params.toString()
  const path = `/video/generate/${artifactId}${query ? `?${query}` : ''}`
  const response = await apiClient.post(path, payload)
  return response.data
}

export const getVideoUrl = (filename: string) => {
  return `${API_BASE_URL}/video/${filename}`
}
