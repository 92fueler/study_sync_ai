import { expect, test } from '@playwright/test'
import { makeUserId, setUserIdLocalStorage } from './utils'

test('dashboard raw notes generate sends text ingestion + note + plan', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  await page.goto('/')

  const generateButton = page.getByRole('button', { name: /generate structure/i })
  await expect(generateButton).toBeDisabled()
  await page.getByPlaceholder(/paste a lecture url/i).fill('Raw notes input\nMore context')
  await expect(generateButton).toBeEnabled()

  const ingestionResponse = page.waitForResponse((res) => res.url().includes('/api/v1/ingestion'))
  const noteResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/notes') && res.request().method() === 'POST'
  })
  const planResponse = page.waitForResponse((res) => res.url().includes('/api/v1/learning-plans'))

  await page.getByRole('button', { name: /generate structure/i }).click()

  const ingestion = await ingestionResponse
  expect(ingestion.status()).toBe(200)
  const ingestionPayload = ingestion.request().postDataJSON()
  expect(ingestionPayload.job_type).toBe('text')

  const note = await noteResponse
  expect(note.status()).toBe(200)
  const notePayload = note.request().postDataJSON()
  expect(notePayload?.note_type).toBe('text')

  const plan = await planResponse
  expect(plan.status()).toBe(200)

  await expect(page.getByText('Saved. Generating structure now.')).toBeVisible()
})

test('dashboard URL input generate sends url ingestion + note', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  await page.goto('/')

  await page.getByRole('button', { name: /url input/i }).click()
  await page.getByPlaceholder(/paste a lecture url/i).fill('https://example.com/lecture')
  await expect(page.getByRole('button', { name: /generate structure/i })).toBeEnabled()

  const ingestionResponse = page.waitForResponse((res) => res.url().includes('/api/v1/ingestion'))
  const noteResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/notes') && res.request().method() === 'POST'
  })

  await page.getByRole('button', { name: /generate structure/i }).click()

  const ingestion = await ingestionResponse
  expect(ingestion.status()).toBe(200)
  const ingestionPayload = ingestion.request().postDataJSON()
  expect(ingestionPayload.job_type).toBe('url')

  const note = await noteResponse
  expect(note.status()).toBe(200)
  const notePayload = note.request().postDataJSON()
  expect(notePayload?.note_type).toBe('url')

  await expect(page.getByText('Saved. Generating structure now.')).toBeVisible()
})

test('dashboard upload PDF creates upload + ingestion job', async ({ page }) => {
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
    name: 'e2e-upload.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('E2E PDF content'),
  })

  const upload = await uploadResponse
  expect(upload.status()).toBe(200)
  const ingestion = await ingestionResponse
  expect(ingestion.status()).toBe(200)

  await expect(page.getByText(/Files uploaded|Upload processed/i)).toBeVisible()
})

test('dashboard upload audio creates upload + ingestion job', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  await page.goto('/')

  const uploadResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/upload') && res.request().method() === 'POST'
  })
  const ingestionResponse = page.waitForResponse((res) => {
    return res.url().includes('/api/v1/ingestion') && res.request().method() === 'POST'
  })

  const audioInput = page.locator('input[type="file"][accept="audio/*"]')
  await audioInput.setInputFiles({
    name: 'e2e-audio.wav',
    mimeType: 'audio/wav',
    buffer: Buffer.from('RIFF....WAVEfmt '),
  })

  const upload = await uploadResponse
  expect(upload.status()).toBe(200)
  const ingestion = await ingestionResponse
  expect(ingestion.status()).toBe(200)

  await expect(page.getByText(/Audio uploaded|Audio processed/i)).toBeVisible()
})

test('dashboard view all buttons route correctly', async ({ page }) => {
  const userId = makeUserId()
  await setUserIdLocalStorage(page, userId)

  await page.goto('/')

  await page.locator('a[href="/plan"]').first().click()
  await expect(page).toHaveURL(/\/plan$/)
  await expect(page.getByRole('heading', { name: /learning plans/i })).toBeVisible()

  await page.goto('/')
  await page.locator('a[href="/bank"]').first().click()
  await expect(page).toHaveURL(/\/bank$/)
  await expect(page.getByRole('heading', { name: /knowledge bank/i })).toBeVisible()
})
