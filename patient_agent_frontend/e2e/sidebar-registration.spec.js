import { test, expect } from '@playwright/test'
import { openLoginPage, loginAsDefaultPatient } from './fixtures/appHarness'

test('FE-E2E-006 右侧栏失败时展示 fallback', async ({ page }) => {
  await openLoginPage(page, 'sidebar_load_failure')
  await loginAsDefaultPatient(page)
  await expect(page.getByText('王小雨')).toBeVisible()
  await expect(page.getByRole('tab', { name: /内科/ })).toBeVisible()
})

test('FE-E2E-008 右侧栏确认挂号', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await page.locator('.patient-sidebar .register-btn').first().click()
  await expect(page.getByText('确认挂号信息')).toBeVisible()
  const sidebarActionRequest = page.waitForRequest((request) => {
    return request.url().includes('/api/patient/sidebar/action') && request.method() === 'POST'
  })
  await page.getByRole('button', { name: '确认挂号' }).click()
  const payload = JSON.parse((await sidebarActionRequest).postData() || '{}')
  expect(payload.action).toBe('confirm_registration')
  expect(payload.payload?.department_name).toBe('心内科')
  expect(payload.payload?.doctor_id).toBe('doctor-003')
  expect(payload.payload?.doctor_name).toBe('张医生')
  await expect(page.getByText('确认挂号信息')).toHaveCount(0)
  await expect(page.getByText('确认挂号：心内科')).toBeVisible()
})

test('FE-E2E-009 侧栏动作切换服务端线程后继续聊天', async ({ page }) => {
  await openLoginPage(page)
  await loginAsDefaultPatient(page)
  await page.locator('.patient-sidebar .register-btn').first().click()
  await page.getByRole('button', { name: '确认挂号' }).click()
  await page.getByPlaceholder('描述您的症状或健康问题...').fill('继续处理刚才那次挂号')
  await page.getByRole('button', { name: /发送/ }).click()
  await expect(page.getByText('继续处理完成。')).toBeVisible()
})
