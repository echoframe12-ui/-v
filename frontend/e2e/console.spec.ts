import { test, expect } from '@playwright/test'

test.describe('Ω∞v Verification Console E2E', () => {
  test('navigates between Console, Becoming, and Consensus pages', async ({ page }) => {
    await page.goto('/')

    // Console Page check
    await expect(page.locator('h1')).toContainText('Ω∞v Verification Console')

    // Navigate to Becoming
    await page.click('text=Becoming')
    await expect(page.locator('h1')).toContainText('Continuous Becoming')
    await expect(page.locator('text=Lifecycle Ring')).toBeVisible()

    // Navigate to Consensus
    await page.click('text=Consensus')
    await expect(page.locator('h1')).toContainText('Multi-Agent Consensus')
    await expect(page.locator('text=Cross-Repo Handoff')).toBeVisible()
  })

  test('runs handoff export in consensus page UI', async ({ page }) => {
    await page.goto('/consensus')

    await page.fill('input[value="oceanic-a"]', 'repo-alpha')
    await page.fill('input[value="oceanic-b"]', 'repo-beta')
    await page.click('button:has-text("Export Packet")')

    await expect(page.locator('text=1 packet in session')).toBeVisible()
  })
})
