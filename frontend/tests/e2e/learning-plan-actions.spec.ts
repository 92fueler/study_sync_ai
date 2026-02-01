import { expect, test } from '@playwright/test'
import { makeUserId, seedPlan, setUserIdLocalStorage } from './utils'

test('learning plan proposed card renders', async ({ page }) => {
  const userId = makeUserId()
  await seedPlan(userId, 'Modal Proposed Plan', 'proposed')

  await setUserIdLocalStorage(page, userId)
  await page.goto('/plan')

  await expect(page.getByText(/new study plans designed for you/i)).toBeVisible()
  await expect(page.locator('h3', { hasText: 'Modal Proposed Plan' }).first()).toBeVisible()
})

test('learning plan create shows new plan card', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  await page.goto('/plan')
  await page.getByRole('button', { name: /create new plan/i }).click()
  await expect(page.getByText('Plan created successfully.')).toBeVisible()
  await expect(page.getByText('New Learning Plan')).toBeVisible()
})
