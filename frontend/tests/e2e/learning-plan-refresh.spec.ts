import { expect, test } from '@playwright/test'
import { makeUserId, seedPlan, setUserIdLocalStorage } from './utils'

test('learning plan page refresh loads active and proposed plans', async ({ page }) => {
  const userId = makeUserId()
  await seedPlan(userId, 'Active Plan', 'active')
  await seedPlan(userId, 'Proposed Plan', 'proposed')

  await setUserIdLocalStorage(page, userId)

  const activeResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/learning-plans?') && res.status() === 200
  })
  const proposedResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/learning-plans/proposed?') && res.status() === 200
  })

  await page.goto('/plan')

  await expect(page.getByRole('heading', { name: /learning plan/i })).toBeVisible()
  await activeResponse
  await proposedResponse
  await expect(page.getByText('Active Plan')).toBeVisible()
  await expect(page.locator('h3', { hasText: 'Proposed Plan' }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: /view details/i }).first()).toBeVisible()
})
