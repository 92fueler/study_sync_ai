import { expect, test } from '@playwright/test'
import { makeUserId, seedNote, setUserIdLocalStorage } from './utils'

test('knowledge bank refresh loads notes and topics', async ({ page }) => {
  const userId = makeUserId()
  await seedNote(userId, 'Knowledge Note')

  await setUserIdLocalStorage(page, userId)

  const notesResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/notes?') && res.status() === 200
  })
  const topicsResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/notes/topics?') && res.status() === 200
  })

  await page.goto('/bank')

  await expect(page.getByRole('heading', { name: /knowledge bank/i })).toBeVisible()
  await notesResponse
  await topicsResponse
  await expect(page.getByText('Knowledge Note')).toBeVisible()
  await expect(page.getByText('E2E')).toBeVisible()
})
