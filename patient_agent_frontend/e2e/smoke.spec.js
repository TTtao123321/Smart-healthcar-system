import { test, expect } from '@playwright/test'

test('FE-E2E-SMOKE login page is reachable from host browser', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByPlaceholder('请输入手机号')).toBeVisible()
  await expect(page.getByRole('button', { name: '获取验证码' })).toBeVisible()
})
