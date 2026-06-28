import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient, waitForThreadVisible } from './fixtures/appHarness'

test('FE-E2E-004 历史线程恢复并展示', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await waitForThreadVisible(page, '历史对话一')
})

test('FE-E2E-005 页面刷新后继续在原线程续聊', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await waitForThreadVisible(page, '历史对话一')
  await page.getByText('历史对话一').click()
  await page.reload()
  await page.getByPlaceholder('描述您的症状或健康问题...').fill('继续刚才的话题')
  await page.getByRole('button', { name: /发送/ }).click()
  await expect(page.getByText('继续为您处理。')).toBeVisible()
})
