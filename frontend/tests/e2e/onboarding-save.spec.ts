import { expect, test } from '@playwright/test'
import { makeUserId, setAuthState, setUserAndAuth } from './utils'

test('signup redirects to onboarding (mock auth)', async ({ page }) => {
  await page.goto('/signup')
  await page.getByLabel(/full name/i).fill('E2E User')
  await page.getByLabel(/email address/i).fill('e2e@example.com')
  await page.getByLabel(/password/i).fill('password123')
  await page.getByRole('button', { name: /sign up/i }).click()

  await expect(page).toHaveURL(/\/onboarding$/)
})

test('onboarding save persists settings and redirects', async ({ page }) => {
  const userId = makeUserId()
  await setUserAndAuth(page, { userId, isAuthenticated: true })

  await page.goto('/dna')
  await page.evaluate(() => window.localStorage.removeItem('hasOnboarded'))

  const settingsResponse = page.waitForResponse((res) => {
    return res.url().includes(`/api/v1/settings/${userId}`) && res.request().method() === 'PATCH'
  })

  await page.getByRole('button', { name: /save & continue/i }).click()
  const response = await settingsResponse
  expect(response.status()).toBe(200)

  await expect(page.getByText(/saved!/i)).toBeVisible()
  const hasOnboarded = await page.evaluate(() => window.localStorage.getItem('hasOnboarded'))
  expect(hasOnboarded).toBe('true')
})

test('onboarding saves selected preferences in payload', async ({ page }) => {
  const userId = makeUserId()
  await setUserAndAuth(page, { userId, isAuthenticated: true })

  await page.goto('/dna')
  await page.evaluate(() => window.localStorage.removeItem('hasOnboarded'))

  await page.getByRole('button', { name: /Video Watching/i }).click()
  await page.getByRole('button', { name: /Podcast Style/i }).click()
  await page.getByRole('button', { name: /^Academic$/ }).click()
  await page
    .getByPlaceholder(/I prefer detailed historical context/i)
    .fill('I prefer concise summaries.')

  const settingsResponsePromise = page.waitForResponse((res) => {
    return res.url().includes(`/api/v1/settings/${userId}`) && res.request().method() === 'PATCH'
  })

  await page.getByRole('button', { name: /save & continue/i }).click()

  const settingsResponse = await settingsResponsePromise
  expect(settingsResponse.status()).toBe(200)

  const payload = settingsResponse.request().postDataJSON()
  expect(payload.study_preferences.formats).toEqual(expect.arrayContaining(['video']))
  expect(payload.study_preferences.preferences).toEqual(expect.arrayContaining(['podcast']))
  expect(payload.study_preferences.custom_style).toBe('I prefer concise summaries.')
  expect(payload.study_preferences.cognitive_tone).toBe('academic')
  await expect(page.getByText(/saved!/i)).toBeVisible()
})
