import React from 'react'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  replaceCurrentSession,
  savePatientMessages,
  savePatientThreads,
} from './storage/patientCache.js'

const {
  getThreadsMock,
  getHistoryMock,
  sendStreamMock,
  sidebarActionMock,
} = vi.hoisted(() => ({
  getThreadsMock: vi.fn(),
  getHistoryMock: vi.fn(),
  sendStreamMock: vi.fn(),
  sidebarActionMock: vi.fn(),
}))

vi.mock('./api/index.js', () => ({
  authApi: {
    sendSms: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
  chatApi: {
    send: vi.fn(),
    sendStream: sendStreamMock,
    getHistory: getHistoryMock,
    getThreads: getThreadsMock,
    deleteThread: vi.fn(),
  },
  patientApi: {
    getProfile: vi.fn(),
    getSidebar: vi.fn(),
    sidebarAction: sidebarActionMock,
    updateProfile: vi.fn(),
  },
}))

vi.mock('./components/sidebar/PatientSidebar.jsx', () => ({
  default: function PatientSidebar({ onSidebarAction }) {
    return (
      <button
        type="button"
        onClick={() =>
          onSidebarAction?.('confirm_registration', {
            department_name: '心内科',
            doctor_name: '张医生',
          })
        }
      >
        触发侧栏操作
      </button>
    )
  },
}))

import App from './App.jsx'

function createMemoryStorage() {
  let store = {}
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null
    },
    setItem(key, value) {
      store[key] = String(value)
    },
    removeItem(key) {
      delete store[key]
    },
    clear() {
      store = {}
    },
  }
}

function createSseResponse(events) {
  const encoder = new TextEncoder()
  const payload = events
    .map(({ event, data }) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
    .join('')
  let sent = false

  return {
    ok: true,
    status: 200,
    body: {
      getReader() {
        return {
          async read() {
            if (sent) {
              return { done: true, value: undefined }
            }
            sent = true
            return { done: false, value: encoder.encode(payload) }
          },
        }
      },
    },
  }
}

describe('App thread context persistence', () => {
  beforeEach(() => {
    const storage = createMemoryStorage()
    Object.defineProperty(globalThis, 'localStorage', {
      value: storage,
      configurable: true,
    })
    Object.defineProperty(window, 'localStorage', {
      value: storage,
      configurable: true,
    })
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
    storage.clear()
    vi.clearAllMocks()
    globalThis.React = React

    replaceCurrentSession({
      token: 'token-1',
      user: { name: '张三', token: 'token-1', patient_id: 1, phone: '13800138001' },
    })

    getThreadsMock.mockResolvedValue({
      data: {
        threads: [
          {
            thread_id: 'thread-1',
            title: '历史对话一',
            last_message: '这是历史消息',
            updated_at: '2026-06-27T14:00:00',
          },
        ],
      },
    })
    getHistoryMock.mockResolvedValue({ data: { messages: [] } })
  })

  afterEach(() => {
    cleanup()
  })

  it('keeps chatting in the last selected thread after a page reload', async () => {
    savePatientThreads(1, [
      {
        id: 'thread-1',
        title: '历史对话一',
        lastMessage: '这是历史消息',
        time: '2026-06-27T14:00:00',
      },
    ])
    savePatientMessages(1, {
      'thread-1': [
        { id: 'm-1', role: 'user', text: '这是历史消息', time: '2026-06-27T14:00:00' },
      ],
    })

    sendStreamMock.mockResolvedValue(
      createSseResponse([
        { event: 'message', data: { content: '继续为您处理。', thread_id: 'thread-1' } },
        { event: 'done', data: { thread_id: 'thread-1' } },
      ])
    )

    const firstRender = render(<App />)
    await screen.findByText('历史对话一')

    fireEvent.click(screen.getByText('历史对话一'))
    await screen.findByText('这是历史消息')

    firstRender.unmount()
    render(<App />)

    await screen.findByText('历史对话一')
    fireEvent.change(screen.getByPlaceholderText('描述您的症状或健康问题...'), {
      target: { value: '继续刚才的话题' },
    })
    fireEvent.click(screen.getByRole('button', { name: /发送/ }))

    await waitFor(() => {
      expect(sendStreamMock).toHaveBeenCalledWith('继续刚才的话题', 'thread-1')
    })
  })

  it('uses the server returned thread id after a sidebar action', async () => {
    sidebarActionMock.mockResolvedValue({
      data: {
        message: '已为您确认挂号。',
        thread_id: 'server-thread-9',
      },
    })
    sendStreamMock.mockResolvedValue(
      createSseResponse([
        { event: 'message', data: { content: '继续处理完成。', thread_id: 'server-thread-9' } },
        { event: 'done', data: { thread_id: 'server-thread-9' } },
      ])
    )

    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: '触发侧栏操作' }))

    await waitFor(() => {
      expect(sidebarActionMock).toHaveBeenCalledTimes(1)
    })

    fireEvent.change(screen.getByPlaceholderText('描述您的症状或健康问题...'), {
      target: { value: '继续处理刚才那次挂号' },
    })
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /发送/ })).not.toBeDisabled()
    })
    fireEvent.click(screen.getByRole('button', { name: /发送/ }))

    await waitFor(() => {
      expect(sendStreamMock).toHaveBeenCalledWith('继续处理刚才那次挂号', 'server-thread-9')
    })
  })
})
