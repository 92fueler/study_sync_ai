import { expect, test } from '@playwright/test'
import { makeUserId, setUserIdLocalStorage } from './utils'

test('learning plan page can create a new plan', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  const createResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/learning-plans') && res.request().method() === 'POST'
  })

  await page.goto('/plan')
  await page.getByRole('button', { name: /create new plan/i }).click()

  const response = await createResponse
  expect(response.status()).toBe(200)

  await expect(page.getByText('Plan created successfully.')).toBeVisible()
})
