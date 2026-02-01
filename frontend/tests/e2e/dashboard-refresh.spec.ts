import { expect, test } from '@playwright/test'
import { makeUserId, setUserIdLocalStorage } from './utils'

const artifactsPath = /\/api\/v1\/artifacts\?/i
test('dashboard refresh loads materials', async ({ page }) => {
  const userId = makeUserId()

  await setUserIdLocalStorage(page, userId)

  const artifactsResponse = page.waitForResponse((res) => {
    return artifactsPath.test(res.url()) && res.status() === 200
  })

  await page.goto('/')

  await expect(page.getByRole('heading', { name: /structure your chaos/i })).toBeVisible()
  await artifactsResponse
  await expect(page.getByRole('heading', { name: /latest materials/i })).toBeVisible()
})
