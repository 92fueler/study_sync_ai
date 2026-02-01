import { request } from '@playwright/test'

const rawBackend = process.env.E2E_BACKEND_URL || 'http://localhost:8000'
const backendBase = rawBackend.endsWith('/api/v1') ? rawBackend : `${rawBackend}/api/v1`

export const makeUserId = () => `user_e2e_${Date.now()}`

export const seedNote = async (userId: string, title = 'E2E Note') => {
  const api = await request.newContext()
  const response = await api.post(`${backendBase}/notes`, {
    data: {
      user_id: userId,
      note_type: 'text',
      title,
      description: 'E2E note body',
      author: 'e2e',
      tags: [{ type: 'topic', label: 'E2E' }],
      topic: 'E2E',
    },
  })
  if (!response.ok()) {
    throw new Error(`Failed to seed note: ${response.status()} ${await response.text()}`)
  }
  return response.json()
}

export const seedPlan = async (
  userId: string,
  title = 'E2E Plan',
  status: 'active' | 'proposed' | 'paused' = 'active',
  options?: {
    items?: Array<{
      title: string
      description?: string
      content_ids?: string[]
      status?: string
      order_index?: number
      estimated_minutes?: number
    }>
  }
) => {
  const api = await request.newContext()
  const response = await api.post(`${backendBase}/learning-plans`, {
    data: {
      user_id: userId,
      title,
      goal: 'E2E goal',
      status,
      details: { source: 'e2e' },
      items: options?.items ?? undefined,
    },
  })
  if (!response.ok()) {
    throw new Error(`Failed to seed plan: ${response.status()} ${await response.text()}`)
  }
  const payload = await response.json()
  return payload.plan
}

export const seedSettings = async (userId: string) => {
  const api = await request.newContext()
  const response = await api.patch(`${backendBase}/settings/${userId}`, {
    data: {
      theme: 'light',
      study_preferences: {
        formats: ['video'],
        preferences: ['focus'],
        customStyle: 'concise',
        cognitiveTone: 'gentle',
      },
    },
  })
  if (!response.ok()) {
    throw new Error(`Failed to seed settings: ${response.status()} ${await response.text()}`)
  }
  return response.json()
}

export const setUserIdLocalStorage = async (page: { addInitScript: Function }, userId: string) => {
  await page.addInitScript((value: string) => {
    window.localStorage.setItem('user_id', value)
    window.localStorage.setItem('isAuthenticated', 'true')
    window.localStorage.setItem('hasOnboarded', 'true')
  }, userId)
}

export const setAuthState = async (
  page: { addInitScript: Function },
  options: {
    userId: string
    isAuthenticated?: boolean
    hasOnboarded?: boolean
  }
) => {
  const { userId, isAuthenticated = true, hasOnboarded = true } = options
  await page.addInitScript(
    (state: { userId: string; isAuthenticated: boolean; hasOnboarded: boolean }) => {
      window.localStorage.setItem('user_id', state.userId)
      if (state.isAuthenticated) {
        window.localStorage.setItem('isAuthenticated', 'true')
      } else {
        window.localStorage.removeItem('isAuthenticated')
      }
      if (state.hasOnboarded) {
        window.localStorage.setItem('hasOnboarded', 'true')
      } else {
        window.localStorage.removeItem('hasOnboarded')
      }
    },
    { userId, isAuthenticated, hasOnboarded }
  )
}

export const setUserAndAuth = async (
  page: { addInitScript: Function },
  options: { userId: string; isAuthenticated?: boolean }
) => {
  const { userId, isAuthenticated = true } = options
  await page.addInitScript(
    (state: { userId: string; isAuthenticated: boolean }) => {
      window.localStorage.setItem('user_id', state.userId)
      if (state.isAuthenticated) {
        window.localStorage.setItem('isAuthenticated', 'true')
      } else {
        window.localStorage.removeItem('isAuthenticated')
      }
    },
    { userId, isAuthenticated }
  )
}
