import { useState, useEffect, useCallback, createContext, useContext, useRef } from 'react'
import { authApi, chatApi, patientApi } from './api/index.js'
import PatientSidebar from './components/sidebar/PatientSidebar.jsx'
import {
  clearPatientCurrentThreadId,
  clearCurrentSessionCache,
  loadCurrentUser,
  loadPatientCurrentThreadId,
  loadPatientMessages,
  loadPatientThreads,
  purgeLegacyCacheKeys,
  replaceCurrentSession,
  restorePatientThreads,
  savePatientCurrentThreadId,
  savePatientMessages,
  savePatientThreads,
} from './storage/patientCache.js'
import {
  User, Lock, CheckCircle, ArrowRight,
  LogOut, Trash2, Send, Shield, Eye, EyeOff,
  MessageSquare, Plus, MessageCircle, UserCircle,
  Calendar, Clock, Stethoscope, ChevronDown, ChevronUp, X,
  Loader, XCircle, Brain, Sparkles
} from 'lucide-react'

const ToastContext = createContext(null)
const useToast = () => useContext(ToastContext)

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

function formatTime(date) {
  if (typeof date === 'string') date = new Date(date)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatShortTime(date) {
  if (typeof date === 'string') date = new Date(date)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return formatTime(date)
  if (diff < 172800000) return '昨天'
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const TOOL_NAME_MAP = {
  query_departments: '查询科室列表',
  query_dept_detail: '查询科室详情',
  query_doctors: '查询医生列表',
  query_doctor_detail: '查询医生详情',
  query_doctor_schedules: '查询医生排班',
  query_schedule_detail: '查询排班详情',
  create_registration: '创建挂号',
  query_registration: '查询挂号',
  cancel_registration: '取消挂号',
}

export default function App() {
  const [toastMsg, setToastMsg] = useState(null)
  const [user, setUser] = useState(() => {
    purgeLegacyCacheKeys()
    return loadCurrentUser()
  })

  const showToast = useCallback((msg) => {
    setToastMsg(msg)
    setTimeout(() => setToastMsg(null), 2000)
  }, [])

  const handleLogin = useCallback((u) => {
    setUser(u)
    showToast('登录成功，欢迎回来')
  }, [showToast])

  const handleLogout = useCallback(() => {
    setUser(null)
    clearCurrentSessionCache()
    showToast('已退出登录')
  }, [showToast])

  return (
    <ToastContext.Provider value={showToast}>
      <div className="min-h-screen relative overflow-hidden">
        {!user ? (
          <LoginPage onLogin={handleLogin} />
        ) : (
          <ChatPage user={user} onLogout={handleLogout} />
        )}

        {toastMsg && (
          <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[200]">
            <div className="bg-white border border-[#E4E7ED] rounded px-4 py-3 shadow-md flex items-center gap-2">
              <CheckCircle size={16} className="text-[#67C23A]" />
              <span className="text-sm">{toastMsg}</span>
            </div>
          </div>
        )}
      </div>
    </ToastContext.Provider>
  )
}

function LoginPage({ onLogin }) {
  const showToast = useToast()
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [countdown, setCountdown] = useState(0)

  const phoneValid = /^1[3-9]\d{9}$/.test(phone)

  useEffect(() => {
    if (countdown <= 0) return
    const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown])

  const handleSendCode = async () => {
    if (!phoneValid || sending || countdown > 0) return
    setSending(true)
    try {
      const res = await authApi.sendSms(phone)
      const devCode = res.data.code_dev
      showToast(devCode ? `验证码已发送：${devCode}` : '验证码已发送')
      setCountdown(60)
    } catch (err) {
      showToast(err.response?.data?.detail || '发送验证码失败，请稍后重试')
    } finally {
      setSending(false)
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!phoneValid) {
      showToast('请输入正确的手机号码')
      return
    }
    if (!code.trim()) {
      showToast('请输入验证码')
      return
    }
    setLoading(true)
    try {
      const res = await authApi.login(phone, code.trim())
      const { token, patient_id, name } = res.data
      const userInfo = { name, token, patient_id, phone }
      replaceCurrentSession({ token, user: userInfo })
      onLogin(userInfo)
    } catch (err) {
      showToast(err.response?.data?.detail || '登录失败，请检查验证码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-bg" />
      <div className="login-container">
        <div className="login-brand">
          <div className="login-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
              <rect x="8" y="8" width="8" height="8" rx="2" />
            </svg>
          </div>
          <h1 className="login-title">飞码医疗智能助手</h1>
          <p className="login-subtitle">智慧医疗 · 患者服务系统</p>
        </div>

        <form className="login-form" onSubmit={submit}>
          <div className="login-field">
            <div className="login-input-group">
              <User size={17} className="login-input-icon" />
              <input
                type="tel"
                placeholder="请输入手机号"
                value={phone}
                onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
                className="login-input"
                maxLength={11}
              />
            </div>
          </div>

          <div className="login-field">
            <div className="login-input-group">
              <Lock size={17} className="login-input-icon" />
              <input
                type="text"
                placeholder="请输入验证码"
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="login-input"
                maxLength={6}
              />
              <button
                type="button"
                onClick={handleSendCode}
                disabled={!phoneValid || sending || countdown > 0}
                className="sms-code-btn"
              >
                {sending ? '发送中...' : countdown > 0 ? `${countdown}s` : '获取验证码'}
              </button>
            </div>
          </div>

          <button type="submit" disabled={loading} className="login-submit">
            {loading ? (
              <span className="login-spinner" />
            ) : (
              <>登录<ArrowRight size={16} /></>
            )}
          </button>
        </form>

        <div className="login-footer">
          <span>版本 5.0.12x</span>
          <span className="login-footer-dot" />
          <span>飞码科技</span>
        </div>
      </div>
    </div>
  )
}

function ChatPage({ user, onLogout }) {
  const showToast = useToast()
  const patientId = user?.patient_id ?? null
  const [threads, setThreads] = useState(() => loadPatientThreads(patientId))
  const [currentThreadId, setCurrentThreadId] = useState(() => loadPatientCurrentThreadId(patientId))
  const [messagesMap, setMessagesMap] = useState(() => loadPatientMessages(patientId))
  const [input, setInput] = useState('')
  const [aiThinking, setAiThinking] = useState(false)
  const [streamingMsgId, setStreamingMsgId] = useState(null)
  const [transitionKey, setTransitionKey] = useState(0)
  const messagesEndRef = useRef(null)
  const abortRef = useRef(null)

  const messages = currentThreadId ? (messagesMap[currentThreadId] || []) : []

  useEffect(() => {
    let cancelled = false

    if (!patientId) {
      setThreads([])
      setMessagesMap({})
      setCurrentThreadId(null)
      return undefined
    }

    setMessagesMap(loadPatientMessages(patientId))
    const restoredCurrentThreadId = loadPatientCurrentThreadId(patientId)
    setCurrentThreadId(restoredCurrentThreadId)

    async function hydrateThreads() {
      try {
        const restoredThreads = await restorePatientThreads(
          patientId,
          async () => {
            const res = await chatApi.getThreads()
            return res.data.threads || []
          }
        )
        if (!cancelled) {
          setThreads(restoredThreads)
          if (
            restoredCurrentThreadId
            && !restoredThreads.some(thread => thread.id === restoredCurrentThreadId)
          ) {
            setCurrentThreadId(null)
            clearPatientCurrentThreadId(patientId)
          }
        }
      } catch {
        if (!cancelled) {
          setThreads([])
          setCurrentThreadId(null)
          clearPatientCurrentThreadId(patientId)
        }
      }
    }

    hydrateThreads()

    return () => {
      cancelled = true
    }
  }, [patientId])

  // Persist threads and messages
  useEffect(() => {
    if (patientId) {
      savePatientThreads(patientId, threads)
    }
  }, [patientId, threads])

  useEffect(() => {
    if (patientId) {
      savePatientMessages(patientId, messagesMap)
    }
  }, [patientId, messagesMap])

  useEffect(() => {
    if (!patientId) return
    if (currentThreadId) {
      savePatientCurrentThreadId(patientId, currentThreadId)
      return
    }
    clearPatientCurrentThreadId(patientId)
  }, [patientId, currentThreadId])

  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }
  useEffect(() => { scrollToBottom() }, [messages, aiThinking])

  const createNewThread = useCallback(() => {
    const id = generateUUID()
    const thread = { id, title: '新对话', lastMessage: '', time: new Date().toISOString() }
    setThreads(prev => [thread, ...prev])
    setCurrentThreadId(id)
    setMessagesMap(prev => ({ ...prev, [id]: [] }))
    return id
  }, [])

  const startNewChat = useCallback(() => {
    setCurrentThreadId(null)
    setTransitionKey(k => k + 1)
  }, [])

  const switchThread = useCallback(async (threadId) => {
    if (threadId === currentThreadId) return
    setCurrentThreadId(threadId)
    setTransitionKey(k => k + 1)
    // Load history from backend if no local messages
    if (!messagesMap[threadId] || messagesMap[threadId].length === 0) {
      try {
        const res = await chatApi.getHistory(threadId)
        const historyMsgs = (res.data.messages || []).map((m, i) => ({
          id: `${threadId}-hist-${i}`,
          role: m.role === 'assistant' ? 'ai' : m.role,
          text: m.content,
          time: new Date(),
        }))
        setMessagesMap(prev => {
          const next = { ...prev, [threadId]: historyMsgs }
          if (patientId) {
            savePatientMessages(patientId, next)
          }
          return next
        })
      } catch {
        // silently ignore, use empty messages
      }
    }
  }, [messagesMap, currentThreadId, patientId])

  const deleteThread = useCallback(async (threadId) => {
    try {
      await chatApi.deleteThread(threadId)
    } catch (err) {
      showToast(err.response?.data?.detail || '删除失败，请稍后重试')
      return
    }
    setThreads(prev => prev.filter(t => t.id !== threadId))
    setMessagesMap(prev => {
      const next = { ...prev }
      delete next[threadId]
      return next
    })
    if (currentThreadId === threadId) {
      setCurrentThreadId(null)
    }
  }, [currentThreadId, showToast])

  const updateThreadMeta = useCallback((threadId, text) => {
    setThreads(prev => prev.map(t =>
      t.id === threadId
        ? {
            ...t,
            title: t.title === '新对话' ? text.slice(0, 12) + (text.length > 12 ? '...' : '') : t.title,
            lastMessage: text.slice(0, 30),
            time: new Date().toISOString(),
          }
        : t
    ))
  }, [])

  const handleSend = useCallback(async (overrideText) => {
    const text = (overrideText || input).trim()
    if (!text || aiThinking) return

    let threadId = currentThreadId
    if (!threadId) {
      threadId = createNewThread()
    }

    const userMsg = { id: Date.now(), role: 'user', text, time: new Date() }
    const aiMsgId = Date.now() + 1
    const aiMsg = { id: aiMsgId, role: 'ai', text: '', time: new Date(), streaming: true, toolCalls: [], thinking: '' }

    setMessagesMap(prev => ({
      ...prev,
      [threadId]: [...(prev[threadId] || []), userMsg, aiMsg],
    }))
    setStreamingMsgId(aiMsgId)
    updateThreadMeta(threadId, text)

    if (!overrideText) setInput('')
    setAiThinking(true)

    try {
      const response = await chatApi.sendStream(text, threadId)

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullText = ''
      let fullThinking = ''
      let currentEvent = ''
      let receivedThreadId = threadId

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            // 兼容 "event: name" 和 "event:name" 两种格式
            currentEvent = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            const jsonStr = line.slice(5).trim()
            if (!jsonStr) continue
            try {
              const data = JSON.parse(jsonStr)
              if (currentEvent === 'thinking' && data.content !== undefined) {
                fullThinking += data.content
                setMessagesMap(prev => ({
                  ...prev,
                  [receivedThreadId]: prev[receivedThreadId].map(m =>
                    m.id === aiMsgId ? { ...m, thinking: fullThinking } : m
                  ),
                }))
              } else if (currentEvent === 'message' && data.content !== undefined) {
                fullText += data.content
                setMessagesMap(prev => ({
                  ...prev,
                  [receivedThreadId]: prev[receivedThreadId].map(m =>
                    m.id === aiMsgId ? { ...m, text: fullText } : m
                  ),
                }))
              }
              if (currentEvent === 'tool_start' && data.tool_call_id && data.tool_name && data.tool_args) {
                setMessagesMap(prev => ({
                  ...prev,
                  [receivedThreadId]: prev[receivedThreadId].map(m =>
                    m.id === aiMsgId ? {
                      ...m,
                      toolCalls: [
                        ...(m.toolCalls || []),
                        {
                          toolCallId: data.tool_call_id,
                          toolName: data.tool_name,
                          toolArgs: data.tool_args,
                          status: 'running',
                        },
                      ],
                    } : m
                  ),
                }))
              } else if (currentEvent === 'tool_end' && data.tool_call_id && data.tool_name) {
                setMessagesMap(prev => ({
                  ...prev,
                  [receivedThreadId]: prev[receivedThreadId].map(m =>
                    m.id === aiMsgId ? {
                      ...m,
                      toolCalls: (m.toolCalls || []).map(tc =>
                        tc.toolCallId === data.tool_call_id
                          ? {
                              ...tc,
                              status: data.tool_error ? 'error' : 'success',
                              toolResult: data.tool_result,
                              toolError: data.tool_error,
                            }
                          : tc
                      ),
                    } : m
                  ),
                }))
              }
              if (data.thread_id) {
                receivedThreadId = data.thread_id
                // If server returned a different thread_id, update
                if (data.thread_id !== threadId) {
                  setCurrentThreadId(data.thread_id)
                  setMessagesMap(prev => {
                    const msgs = prev[threadId] || []
                    const withoutOld = { ...prev }
                    delete withoutOld[threadId]
                    return { ...withoutOld, [data.thread_id]: msgs.map(m =>
                      m.id === aiMsgId ? { ...m, text: fullText } : m
                    )}
                  })
                  setThreads(prev => prev.map(t =>
                    t.id === threadId ? { ...t, id: data.thread_id } : t
                  ))
                  threadId = data.thread_id
                }
              }
              if (data.error) {
                showToast(data.error)
              }
            } catch { /* ignore parse errors */ }
          }
        }
      }

      // Finalize the message
      setMessagesMap(prev => ({
        ...prev,
        [threadId]: (prev[threadId] || []).map(m =>
          m.id === aiMsgId ? { ...m, text: fullText || '抱歉，未收到回复。', streaming: false } : m
        ),
      }))
      updateThreadMeta(threadId, fullText || text)
    } catch (err) {
      showToast(err.message || '发送失败，请稍后重试')
      setMessagesMap(prev => ({
        ...prev,
        [threadId]: (prev[threadId] || []).map(m =>
          m.id === aiMsgId ? { ...m, text: '抱歉，请求出错了，请稍后重试。', streaming: false } : m
        ),
      }))
    } finally {
      setAiThinking(false)
      setStreamingMsgId(null)
    }
  }, [input, aiThinking, currentThreadId, createNewThread, updateThreadMeta, showToast])

  const handleSidebarAction = useCallback(async (action, payload) => {
    if (aiThinking) return

    let threadId = currentThreadId
    if (!threadId) {
      threadId = createNewThread()
    }

    const userText = action === 'confirm_registration'
      ? `确认挂号：${payload.department_name} · ${payload.doctor_name}`
      : '执行侧栏操作'
    const userMsg = { id: Date.now(), role: 'user', text: userText, time: new Date() }
    const aiMsgId = Date.now() + 1
    const aiMsg = { id: aiMsgId, role: 'ai', text: '', time: new Date(), streaming: false }

    setMessagesMap(prev => ({
      ...prev,
      [threadId]: [...(prev[threadId] || []), userMsg, aiMsg],
    }))
    updateThreadMeta(threadId, userText)
    setAiThinking(true)

    try {
      const res = await patientApi.sidebarAction(action, threadId, payload)
      if (res.data?.thread_id && res.data.thread_id !== threadId) {
        const nextThreadId = res.data.thread_id
        setCurrentThreadId(nextThreadId)
        setMessagesMap(prev => {
          const msgs = prev[threadId] || []
          const withoutOld = { ...prev }
          delete withoutOld[threadId]
          return { ...withoutOld, [nextThreadId]: msgs }
        })
        setThreads(prev => prev.map(t =>
          t.id === threadId ? { ...t, id: nextThreadId } : t
        ))
        threadId = nextThreadId
      }
      const reply = res.data?.message || '已收到请求，请稍后查看结果。'

      setMessagesMap(prev => ({
        ...prev,
        [threadId]: (prev[threadId] || []).map(m =>
          m.id === aiMsgId ? { ...m, text: reply, streaming: false } : m
        ),
      }))
      updateThreadMeta(threadId, reply)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || '侧栏操作失败，请稍后重试'
      showToast(errorMessage)
      setMessagesMap(prev => ({
        ...prev,
        [threadId]: (prev[threadId] || []).map(m =>
          m.id === aiMsgId ? { ...m, text: errorMessage, streaming: false } : m
        ),
      }))
    } finally {
      setAiThinking(false)
    }
  }, [aiThinking, currentThreadId, createNewThread, showToast, updateThreadMeta])



  return (
    <div className="chat-page page-glass-enter">
      <nav className="chat-nav">
        <div className="nav-inner">
          <div className="nav-brand">
            <div className="nav-logo">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-white">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
                <rect x="8" y="8" width="8" height="8" rx="2" />
              </svg>
            </div>
            <span className="nav-title">飞码医疗智能助手</span>
          </div>
          <div className="nav-user">
            <div className="nav-avatar">{user.name[0]}</div>
            <span className="nav-username">{user.name}</span>
            <button onClick={onLogout} className="nav-logout"><LogOut size={15} /></button>
          </div>
        </div>
      </nav>

      <div className="chat-layout">
        <LeftPanel
          threads={threads}
          currentThreadId={currentThreadId}
          onNewChat={startNewChat}
          onSwitchThread={switchThread}
          onDeleteThread={deleteThread}
        />
        <ChatWindow
          messages={messages}
          aiThinking={aiThinking}
          streamingMsgId={streamingMsgId}
          input={input}
          setInput={setInput}
          onSend={handleSend}
          messagesEndRef={messagesEndRef}
          hasThread={!!currentThreadId}
          transitionKey={transitionKey}
        />
        <PatientSidebar user={user} onSidebarAction={handleSidebarAction} />
      </div>
    </div>
  )
}

function LeftPanel({ threads, currentThreadId, onNewChat, onSwitchThread, onDeleteThread }) {
  const [pendingDeleteId, setPendingDeleteId] = useState(null)

  const handleDelete = (id) => {
    setPendingDeleteId(id)
  }

  const confirmDelete = () => {
    if (pendingDeleteId) {
      onDeleteThread(pendingDeleteId)
      setPendingDeleteId(null)
    }
  }

  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <MessageSquare size={18} className="text-sky" />
        <span>对话记录</span>
      </div>
      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={15} /> 新对话
      </button>
      <div className="chat-list">
        {threads.filter(t => t.lastMessage).length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px 0', color: '#94A3B8', fontSize: '13px' }}>
            暂无对话记录
          </div>
        ) : (
          threads.filter(t => t.lastMessage).map((t) => (
            <div
              key={t.id}
              className={`chat-item ${t.id === currentThreadId ? 'active glass-shimmer-active' : ''}`}
              onClick={() => onSwitchThread(t.id)}
            >
              <div className="chat-item-icon">
                <MessageCircle size={14} />
              </div>
              <div className="chat-item-content">
                <div className="chat-item-title" data-testid="thread-title">{t.title}</div>
              </div>
              <span className="chat-item-time">{formatShortTime(t.time)}</span>
              <button
                className="chat-item-delete"
                onClick={(e) => { e.stopPropagation(); handleDelete(t.id) }}
                title="删除对话"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))
        )}
      </div>

      {pendingDeleteId && (
        <div className="modal-overlay" onClick={() => setPendingDeleteId(null)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">删除对话</span>
              <button onClick={() => setPendingDeleteId(null)} className="modal-close">
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: '14px', color: '#475569', margin: 0, lineHeight: 1.6 }}>
                确定要删除这条对话记录吗？删除后将无法恢复。
              </p>
            </div>
            <div className="modal-footer">
              <button onClick={() => setPendingDeleteId(null)} className="modal-btn modal-btn-cancel">取消</button>
              <button onClick={confirmDelete} className="modal-btn modal-btn-danger">删除</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ChatWindow({ messages, aiThinking, streamingMsgId, input, setInput, onSend, messagesEndRef, hasThread, transitionKey }) {
  const [time, setTime] = useState(new Date())
  useEffect(() => { const t = setInterval(() => setTime(new Date()), 30000); return () => clearInterval(t) }, [])

  const now = new Date()
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`

  return (
    <div className="chat-main">
      <div className="chat-header">
        <div className="flex items-center gap-3">
          <div className="chat-header-icon">
            <Shield size={20} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[15px]">AI 医疗助手</span>
              <span className="online-badge">在线</span>
            </div>
            <span className="header-subtitle">AI 智能诊疗中 · {timeStr}</span>
          </div>
        </div>
      </div>
      <div className="chat-messages chat-messages-transition" key={transitionKey}>
        {messages.length === 0 && !aiThinking ? (
          <WelcomeScreen setInput={setInput} />
        ) : (
          <>
            {messages.map((msg, i) => (
              <ChatBubble
                key={msg.id}
                msg={msg}
                isStreaming={msg.id === streamingMsgId}
                isLast={i === messages.length - 1 && msg.role === 'ai' && !msg.streaming}
              />
            ))}
            {aiThinking && messages[messages.length - 1]?.role !== 'ai' && <ThinkingBubble />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      <div className="chat-input-area">
        <div className="chat-input-row">
          <div className="chat-input-wrap">
            <input type="text" value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.nativeEvent.isComposing) { e.preventDefault(); onSend() } }}
              placeholder="描述您的症状或健康问题..." />
          </div>
          <button onClick={() => onSend()} disabled={!input.trim() || aiThinking} className="chat-send-btn">
            发送 <Send size={14} />
          </button>
        </div>
        <p className="chat-disclaimer">AI 医疗助手仅供参考，不能替代医生诊断。如有紧急情况请立即就医。</p>
      </div>
    </div>
  )
}

function WelcomeScreen({ setInput }) {
  const inputRef = useRef(null)
  const prompts = [
    { icon: <Stethoscope size={16} />, text: '查询医院有哪些科室', label: '科室查询' },
    { icon: <UserCircle size={16} />, text: '内科有哪些医生出诊？', label: '医生排班' },
    { icon: <Calendar size={16} />, text: '我想预约挂号', label: '预约挂号' },
    { icon: <Clock size={16} />, text: '查看我的挂号记录', label: '挂号查询' },
  ]

  return (
    <div className="welcome-screen">
      <div className="welcome-icon">
        <Shield size={40} className="text-[#0EA5E9]" />
      </div>
      <h1 className="welcome-title">您好，我是您的 AI 医疗助手</h1>
      <p className="welcome-subtitle">我可以帮您查询科室、了解医生排班、预约挂号及管理挂号记录</p>
      <div className="welcome-prompts">
        {prompts.map((p, i) => (
          <button key={i} className="welcome-prompt-btn" onClick={() => setInput(p.text)}>
            <span className="welcome-prompt-icon">{p.icon}</span>
            <div className="welcome-prompt-text">
              <span className="welcome-prompt-label">{p.label}</span>
              <span className="welcome-prompt-value">{p.text}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function ThinkingBar({ thinking, isStreaming }) {
  const [expanded, setExpanded] = useState(true)
  const [autoCollapsed, setAutoCollapsed] = useState(false)

  // 流式结束后自动折叠一次
  useEffect(() => {
    if (!isStreaming && !autoCollapsed && thinking) {
      setExpanded(false)
      setAutoCollapsed(true)
    }
  }, [isStreaming, thinking, autoCollapsed])

  if (!thinking) return null

  return (
    <div className="thinking-bar">
      <div className="thinking-header" onClick={() => setExpanded(!expanded)}>
        <Brain size={14} className={isStreaming ? 'thinking-icon thinking-icon-active' : 'thinking-icon'} />
        <span className="thinking-title">
          {isStreaming ? (
            <>思考中<span className="thinking-dots"><span>.</span><span>.</span><span>.</span></span></>
          ) : '思考过程'}
        </span>
        {expanded ? (
          <ChevronUp size={14} className="thinking-chevron" />
        ) : (
          <ChevronDown size={14} className="thinking-chevron" />
        )}
      </div>
      {expanded && (
        <div className="thinking-content">
          {thinking}
          {isStreaming && <span className="thinking-cursor" />}
        </div>
      )}
    </div>
  )
}

function ToolCallBar({ toolCalls }) {
  const [expandedId, setExpandedId] = useState(null)

  if (!toolCalls || toolCalls.length === 0) return null

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="tool-call-bar">
      {toolCalls.map((tc) => (
        <div key={tc.toolCallId} className="tool-call-item">
          <div
            className="tool-call-row"
            onClick={() => toggleExpand(tc.toolCallId)}
          >
            <span className="tool-call-icon">
              {tc.status === 'running' ? (
                <Loader size={14} className="tool-call-spinner" />
              ) : tc.status === 'error' ? (
                <XCircle size={14} className="text-rose" />
              ) : (
                <CheckCircle size={14} className="text-emerald" />
              )}
            </span>
            <span className="tool-call-name">
              {TOOL_NAME_MAP[tc.toolName] || tc.toolName}
            </span>
            <span className={`tool-call-status tool-call-status-${tc.status}`}>
              {tc.status === 'running' ? '调用中' : tc.status === 'error' ? '失败' : '成功'}
            </span>
            {expandedId === tc.toolCallId ? (
              <ChevronUp size={14} className="tool-call-chevron" />
            ) : (
              <ChevronDown size={14} className="tool-call-chevron" />
            )}
          </div>
          {expandedId === tc.toolCallId && (
            <div className="tool-call-detail">
              <div className="tool-call-section">
                <span className="tool-call-label">调用参数</span>
                <pre className="tool-call-code">
                  {JSON.stringify(tc.toolArgs, null, 2)}
                </pre>
              </div>
              {tc.status === 'success' && tc.toolResult && (
                <div className="tool-call-section">
                  <span className="tool-call-label">返回结果</span>
                  <pre className="tool-call-code">{tc.toolResult}</pre>
                </div>
              )}
              {tc.status === 'error' && tc.toolError && (
                <div className="tool-call-section">
                  <span className="tool-call-label">错误信息</span>
                  <pre className="tool-call-code tool-call-error">{tc.toolError}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function ChatBubble({ msg, isStreaming, isLast }) {
  const isAI = msg.role === 'ai'
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)
  const [isNew, setIsNew] = useState(true)

  useEffect(() => {
    if (isStreaming) {
      setDisplayed(msg.text)
      setDone(false)
      return
    }
    if (!isAI) {
      setDisplayed(msg.text)
      setDone(true)
      return
    }
    // Non-streaming AI message (history): show immediately, no animation
    setDisplayed(msg.text)
    setDone(true)
    // Remove "new" flag after animation completes
    const timer = setTimeout(() => setIsNew(false), 400)
    return () => clearTimeout(timer)
  }, [msg.id, isStreaming, isAI, msg.text])

  const timeStr = msg.time instanceof Date
    ? msg.time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    : formatTime(msg.time)

  return (
    <div className={`flex gap-3 ${isAI ? '' : 'flex-row-reverse'} ${isNew ? 'bubble-enter' : ''}`}>
      <div className={`bubble-avatar ${isAI ? 'bubble-avatar-ai' : 'bubble-avatar-user'}`}>
        {isAI ? <Shield size={15} className="text-white" /> : <User size={15} className="text-white" />}
      </div>
      <div className={`max-w-[72%] ${isAI ? '' : 'flex flex-col items-end'}`}>
        {isAI && msg.thinking && (
          <ThinkingBar thinking={msg.thinking} isStreaming={!!msg.streaming} />
        )}
        {isAI && msg.toolCalls && msg.toolCalls.length > 0 && (
          <ToolCallBar toolCalls={msg.toolCalls} />
        )}
        <div
          className={`bubble ${isAI ? 'bubble-ai' : 'bubble-user'}`}
          data-testid={isAI ? 'ai-message' : 'user-message'}
        >
          {displayed}
          {!done && displayed && <span className="typing-cursor" />}
        </div>
        <span className="msg-time">{timeStr}</span>
      </div>
    </div>
  )
}

function ThinkingBubble() {
  return (
    <div className="flex gap-3">
      <div className="bubble-avatar bubble-avatar-ai" style={{ width: 32, height: 32 }}>
        <Shield size={14} className="text-white" />
      </div>
      <div className="thinking-dots">
        {[0, 1, 2].map(i => (
          <div key={i} className="thinking-dot" style={{ animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>
    </div>
  )
}
