import { expect, test } from '@playwright/test'
import { makeUserId, setUserIdLocalStorage } from './utils'

test('dashboard generate structure posts ingestion, note, and plan', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  await page.goto('/')

  await page.getByPlaceholder(/paste a lecture url/i).fill('Linear algebra basics\nMatrices, vectors, eigenvalues.')

  const ingestionResponse = page.waitForResponse((res) => res.url().includes('/api/v1/ingestion') && res.status() === 200)
  const noteResponse = page.waitForResponse((res) => res.url().includes('/api/v1/notes') && res.status() === 200)
  const planResponse = page.waitForResponse((res) => res.url().includes('/api/v1/learning-plans') && res.status() === 200)

  await page.getByRole('button', { name: /generate structure/i }).click()

  await ingestionResponse
  await noteResponse
  await planResponse

  await expect(page.getByText('Saved. Generating structure now.')).toBeVisible()
})
