import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动附加 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('patient_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('patient_token')
      localStorage.removeItem('patient_user')
      window.location.reload()
    }
    return Promise.reject(err)
  }
)

// ============ 认证 ============

export const authApi = {
  /** 发送短信验证码 */
  sendSms(phone) {
    return api.post('/auth/send-sms', { phone })
  },
  /** 验证码登录 */
  login(phone, code) {
    return api.post('/auth/login', { phone, code })
  },
  /** 登出 */
  logout() {
    return api.post('/auth/logout')
  },
}

// ============ 聊天 ============

export const chatApi = {
  /** 发送消息（完整响应） */
  send(message, threadId) {
    return api.post('/chat', { message, thread_id: threadId })
  },
  /** 发送消息（SSE 流式） */
  sendStream(message, threadId) {
    return fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(localStorage.getItem('patient_token')
          ? { Authorization: `Bearer ${localStorage.getItem('patient_token')}` }
          : {}),
      },
      body: JSON.stringify({ message, thread_id: threadId }),
    })
  },
  /** 获取对话历史 */
  getHistory(threadId) {
    return api.get('/chat/history', { params: { thread_id: threadId } })
  },
}

// ============ 患者档案 ============

export const patientApi = {
  getProfile() {
    return api.get('/patient/profile')
  },
  getSidebar() {
    return api.get('/patient/sidebar')
  },
  updateProfile(payload) {
    return api.post('/patient/profile', payload)
  },
}

export default api
