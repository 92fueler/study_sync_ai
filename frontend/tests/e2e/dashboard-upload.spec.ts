import { expect, test } from '@playwright/test'
import { makeUserId, setUserIdLocalStorage } from './utils'

test('dashboard upload creates ingestion job', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  await page.goto('/')

  const uploadResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/upload') && res.request().method() === 'POST'
  })
  const ingestionResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/ingestion') && res.request().method() === 'POST'
  })

  const fileInput = page.locator('input[type="file"][multiple]')
  await fileInput.setInputFiles({
    name: 'e2e-upload.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('E2E upload content'),
  })

  const upload = await uploadResponse
  expect(upload.status()).toBe(200)
  const ingestion = await ingestionResponse
  expect(ingestion.status()).toBe(200)

  await expect(page.getByText(/Files uploaded|Upload processed/i)).toBeVisible()
})
