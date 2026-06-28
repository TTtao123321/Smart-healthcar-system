import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient } from './fixtures/appHarness'

test('FE-E2E-001 登录成功进入聊天页', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await expect(page.getByPlaceholder('描述您的症状或健康问题...')).toBeVisible()
})

test('FE-E2E-002 非法手机号不触发登录', async ({ page }) => {
  await openLoginPage(page)
  await page.getByPlaceholder('请输入手机号').fill('123')
  await page.getByRole('button', { name: /^登录/ }).click()
  await expect(page.getByText('请输入正确的手机号码')).toBeVisible()
})

test('FE-E2E-003 空验证码不触发登录', async ({ page }) => {
  await openLoginPage(page)
  await page.getByPlaceholder('请输入手机号').fill('13800138000')
  await page.getByRole('button', { name: /^登录/ }).click()
  await expect(page.getByText('请输入验证码')).toBeVisible()
})
