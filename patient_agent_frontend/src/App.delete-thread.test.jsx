import React from 'react'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  replaceCurrentSession,
  savePatientMessages,
  savePatientThreads,
} from './storage/patientCache.js'

const { deleteThreadMock, getThreadsMock } = vi.hoisted(() => ({
  deleteThreadMock: vi.fn(),
  getThreadsMock: vi.fn(),
}))

vi.mock('./api/index.js', () => ({
  authApi: {
    sendSms: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
  chatApi: {
    send: vi.fn(),
    sendStream: vi.fn(),
    getHistory: vi.fn(),
    getThreads: getThreadsMock,
    deleteThread: deleteThreadMock,
  },
  patientApi: {
    getProfile: vi.fn(),
    getSidebar: vi.fn(),
    sidebarAction: vi.fn(),
    updateProfile: vi.fn(),
  },
}))

vi.mock('./components/sidebar/PatientSidebar.jsx', () => ({
  default: function PatientSidebar() {
    return <div data-testid="patient-sidebar" />
  },
}))

import App from './App.jsx'

describe('App delete thread behavior', () => {
  beforeEach(() => {
    localStorage.clear()
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
  })

  afterEach(() => {
    cleanup()
  })

  it('keeps local thread cache when remote deletion fails', async () => {
    deleteThreadMock.mockRejectedValueOnce(new Error('redis delete failed'))

    render(<App />)

    await screen.findByText('历史对话一')

    fireEvent.click(screen.getByTitle('删除对话'))
    fireEvent.click(screen.getByRole('button', { name: '删除' }))

    await waitFor(() => {
      expect(screen.getByText('历史对话一')).toBeInTheDocument()
      expect(screen.getByText('删除失败，请稍后重试')).toBeInTheDocument()
    })
  })
})
