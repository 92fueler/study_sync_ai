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
export const uploadFiles = async (userId: string, files: File[]) => {
  const formData = new FormData()
  formData.append('user_id', userId)
  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
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
