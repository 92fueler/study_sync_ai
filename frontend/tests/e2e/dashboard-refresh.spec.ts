import { expect, test } from '@playwright/test'
import { makeUserId, seedPlan, setUserIdLocalStorage } from './utils'

const artifactsPath = /\/api\/v1\/artifacts\?/i
const plansPath = /\/api\/v1\/learning-plans\?/i

test('dashboard refresh loads materials and active plans', async ({ page }) => {
  const userId = makeUserId()
  await seedPlan(userId, 'Dashboard Plan', 'active')

  await setUserIdLocalStorage(page, userId)

  const artifactsResponse = page.waitForResponse((res) => {
    return artifactsPath.test(res.url()) && res.status() === 200
  })
  const plansResponse = page.waitForResponse((res) => {
    return plansPath.test(res.url()) && res.status() === 200
  })

  await page.goto('/')

  await expect(page.getByRole('heading', { name: /structure your chaos/i })).toBeVisible()
  await artifactsResponse
  await plansResponse
  await expect(page.getByText('Dashboard Plan')).toBeVisible()
})
