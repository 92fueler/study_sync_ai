import { expect, test } from '@playwright/test'
import { makeUserId, seedNote, seedPlan, setUserIdLocalStorage } from './utils'

test('note detail refresh loads the note', async ({ page }) => {
  const userId = makeUserId()
  const note = await seedNote(userId, 'Detail Note')

  await setUserIdLocalStorage(page, userId)

  const detailResponsePromise = page.waitForResponse((res) => {
    return res.url().includes(`/api/v1/notes/${note.id}`)
  })
  await page.goto(`/notes/${note.id}`)
  const detailResponse = await detailResponsePromise
  expect(detailResponse.status()).toBe(200)
  await expect(page.locator('h1', { hasText: 'Detail Note' })).toBeVisible()
})

test('plan detail refresh loads the plan', async ({ page }) => {
  const userId = makeUserId()
  const plan = await seedPlan(userId, 'Detail Plan', 'active')

  await setUserIdLocalStorage(page, userId)

  const detailResponsePromise = page.waitForResponse((res) => {
    return res.url().includes(`/api/v1/learning-plans/${plan.id}`)
  })
  await page.goto(`/plans/${plan.id}`)
  const detailResponse = await detailResponsePromise
  expect(detailResponse.status()).toBe(200)
  await expect(page.getByRole('heading', { name: 'Detail Plan' })).toBeVisible()
})
