import { expect } from '@playwright/test'
import { resetE2EState } from '../utils/e2eApi'

export async function openLoginPage(page, scenario = 'baseline') {
  await resetE2EState(scenario)
  await page.context().clearCookies()
  await page.goto('/')
  await page.evaluate(() => localStorage.clear())
  await page.reload()
  await expect(page.getByPlaceholder('请输入手机号')).toBeVisible()
}

export async function loginAsDefaultPatient(page) {
  await page.getByPlaceholder('请输入手机号').fill('13800138000')
  await page.getByRole('button', { name: '获取验证码' }).click()
  await page.getByPlaceholder('请输入验证码').fill('123456')
  await page.getByRole('button', { name: /^登录/ }).click()
  await expect(page.getByPlaceholder('描述您的症状或健康问题...')).toBeVisible()
}
