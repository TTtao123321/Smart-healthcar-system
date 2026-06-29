import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient, waitForThreadVisible } from './fixtures/appHarness'

test('FE-E2E-010 删除线程成功', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await waitForThreadVisible(page, '历史对话一')
  await page.getByTitle('删除对话').click()
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await expect(page.getByText('历史对话一')).toHaveCount(0)
})

test('FE-E2E-011 删除线程失败时回滚本地列表', async ({ page }) => {
  await openLoginPage(page, 'delete_thread_failure')
  await loginAsDefaultPatient(page)
  await waitForThreadVisible(page, '历史对话一')
  await page.getByTitle('删除对话').click()
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await expect(page.getByText('删除失败，请稍后重试')).toBeVisible()
  await expect(page.getByText('历史对话一')).toBeVisible()
})
