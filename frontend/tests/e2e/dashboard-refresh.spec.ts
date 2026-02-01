import { expect, test } from '@playwright/test'
import { makeUserId, seedNote, seedPlan, setUserIdLocalStorage } from './utils'

const notesRecentPath = /\/api\/v1\/notes\/recent\?/i
const plansPath = /\/api\/v1\/learning-plans\?/i

test('dashboard refresh loads recent notes and active plans', async ({ page }) => {
  const userId = makeUserId()
  await seedNote(userId, 'Dashboard Note')
  await seedPlan(userId, 'Dashboard Plan', 'active')

  await setUserIdLocalStorage(page, userId)

  const notesResponse = page.waitForResponse((res) => {
    return notesRecentPath.test(res.url()) && res.status() === 200
  })
  const plansResponse = page.waitForResponse((res) => {
    return plansPath.test(res.url()) && res.status() === 200
  })

  await page.goto('/')

  await expect(page.getByRole('heading', { name: /structure your chaos/i })).toBeVisible()
  await notesResponse
  await plansResponse
  await expect(page.getByText('Dashboard Note')).toBeVisible()
  await expect(page.getByText('Dashboard Plan')).toBeVisible()
})
