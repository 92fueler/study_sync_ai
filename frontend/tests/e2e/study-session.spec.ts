import { expect, test } from '@playwright/test'
import { makeUserId, seedPlan, setUserIdLocalStorage } from './utils'

test('study session loads plan modules', async ({ page }) => {
  const userId = makeUserId()
  const plan = await seedPlan(userId, 'Session Plan', 'active', {
    items: [
      { title: 'Module One', description: 'Intro module', order_index: 0 },
      { title: 'Module Two', description: 'Deep dive', order_index: 1 },
    ],
  })

  await setUserIdLocalStorage(page, userId)

  const detailResponse = page.waitForResponse((res) => {
    return res.url().includes(`/api/v1/learning-plans/${plan.id}`) && res.status() === 200
  })

  await page.goto(`/session/${plan.id}`)
  await detailResponse

  await expect(page.getByRole('heading', { name: 'Session Plan' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Module One' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Module Two' })).toBeVisible()
})
