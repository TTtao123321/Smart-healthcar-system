import { useState, useEffect, useCallback, createContext, useContext, useRef } from 'react'
import { authApi, chatApi } from './api/index.js'
import {
  User, Lock, CheckCircle, ArrowRight,
  LogOut, Trash2, Send, Shield, Eye, EyeOff,
  MessageSquare, Plus, MessageCircle, UserCircle,
  Calendar, Clock, Stethoscope, ChevronDown, X
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

const STORAGE_KEYS = {
  TOKEN: 'patient_token',
  USER: 'patient_user',
  THREADS: 'patient_threads',
  MESSAGES: 'patient_messages',
}

function loadFromStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function saveToStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch { /* ignore */ }
}

export default function App() {
  const [toastMsg, setToastMsg] = useState(null)
  const [user, setUser] = useState(() => loadFromStorage(STORAGE_KEYS.USER, null))

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
    localStorage.removeItem(STORAGE_KEYS.TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
    localStorage.removeItem(STORAGE_KEYS.THREADS)
    localStorage.removeItem(STORAGE_KEYS.MESSAGES)
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
      localStorage.setItem(STORAGE_KEYS.TOKEN, token)
      saveToStorage(STORAGE_KEYS.USER, userInfo)
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
  const [threads, setThreads] = useState(() => loadFromStorage(STORAGE_KEYS.THREADS, []))
  const [currentThreadId, setCurrentThreadId] = useState(null)
  const [messagesMap, setMessagesMap] = useState(() => loadFromStorage(STORAGE_KEYS.MESSAGES, {}))
  const [input, setInput] = useState('')
  const [aiThinking, setAiThinking] = useState(false)
  const [streamingMsgId, setStreamingMsgId] = useState(null)
  const [transitionKey, setTransitionKey] = useState(0)
  const messagesEndRef = useRef(null)
  const abortRef = useRef(null)

  const messages = currentThreadId ? (messagesMap[currentThreadId] || []) : []

  // Persist threads and messages
  useEffect(() => { saveToStorage(STORAGE_KEYS.THREADS, threads) }, [threads])
  useEffect(() => { saveToStorage(STORAGE_KEYS.MESSAGES, messagesMap) }, [messagesMap])

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
        const res = await chatApi.getHistory(String(user.patient_id), threadId)
        const historyMsgs = (res.data.messages || []).map((m, i) => ({
          id: `${threadId}-hist-${i}`,
          role: m.role === 'assistant' ? 'ai' : m.role,
          text: m.content,
          time: new Date(),
        }))
        setMessagesMap(prev => ({ ...prev, [threadId]: historyMsgs }))
      } catch {
        // silently ignore, use empty messages
      }
    }
  }, [user.patient_id, messagesMap, currentThreadId])

  const deleteThread = useCallback((threadId) => {
    setThreads(prev => prev.filter(t => t.id !== threadId))
    setMessagesMap(prev => {
      const next = { ...prev }
      delete next[threadId]
      return next
    })
    if (currentThreadId === threadId) {
      setCurrentThreadId(null)
    }
  }, [currentThreadId])

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
    const aiMsg = { id: aiMsgId, role: 'ai', text: '', time: new Date(), streaming: true }

    setMessagesMap(prev => ({
      ...prev,
      [threadId]: [...(prev[threadId] || []), userMsg, aiMsg],
    }))
    setStreamingMsgId(aiMsgId)
    updateThreadMeta(threadId, text)

    if (!overrideText) setInput('')
    setAiThinking(true)

    try {
      const response = await chatApi.sendStream(text, String(user.patient_id), threadId)

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullText = ''
      let receivedThreadId = threadId

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event:message')) {
            // Next data line is message content
          } else if (line.startsWith('event:done')) {
            // Stream complete
          } else if (line.startsWith('event:error')) {
            // Next data line has error
          } else if (line.startsWith('data:')) {
            const jsonStr = line.slice(5).trim()
            if (!jsonStr) continue
            try {
              const data = JSON.parse(jsonStr)
              if (data.content !== undefined) {
                fullText += data.content
                setMessagesMap(prev => ({
                  ...prev,
                  [receivedThreadId]: prev[receivedThreadId].map(m =>
                    m.id === aiMsgId ? { ...m, text: fullText } : m
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
  }, [input, aiThinking, currentThreadId, user.patient_id, createNewThread, updateThreadMeta, showToast])



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
        <RightPanel user={user} onSendChat={handleSend} />
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
                <div className="chat-item-title">{t.title}</div>
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

function RightPanel({ user, onSendChat }) {
  const [expandedDept, setExpandedDept] = useState(null)
  const [confirmDoctor, setConfirmDoctor] = useState(null)
  const showToast = useToast()

  const handleRegister = (doctor) => {
    setConfirmDoctor(doctor)
  }

  const handleConfirm = () => {
    const deptForConfirm = expandedDept !== null ? scheduleData[expandedDept].name : confirmDoctor.dept
    setConfirmDoctor(null)
    // Send chat message instead of mock behavior
    onSendChat(`我要预约挂号：${deptForConfirm} · ${confirmDoctor.name}（${confirmDoctor.title}）`)
  }

  const deptName = expandedDept !== null ? scheduleData[expandedDept].name : ''

  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <Calendar size={18} className="text-sky" />
        <span>今日排班</span>
      </div>
      <div className="schedule-date">2025年6月15日 周一</div>
      <div className="dept-tabs">
        {scheduleData.map((dept, i) => (
          <button key={i} onClick={() => setExpandedDept(expandedDept === i ? null : i)}
            className={`dept-tab ${expandedDept === i ? 'active' : ''}`}>
            <Stethoscope size={14} />
            <span>{dept.name}</span>
            <span className="dept-count">{dept.doctors.length}位</span>
          </button>
        ))}
      </div>
      <div className="schedule-list">
        {expandedDept === null ? (
          <div className="schedule-placeholder">
            <Stethoscope size={32} className="placeholder-icon" />
            <p className="placeholder-text">点击具体科室查看排班信息</p>
          </div>
        ) : (
          scheduleData[expandedDept].doctors.map((doctor, i) => (
            <div key={i} className="doctor-card">
              <div className="doctor-header">
                <div className="doctor-avatar">{doctor.name[0]}</div>
                <div className="doctor-info">
                  <div className="doctor-name">{doctor.name}</div>
                  <div className="doctor-title">{doctor.title}</div>
                </div>
              </div>
              <p className="doctor-bio">{doctor.bio}</p>
              <div className="doctor-times">
                <Clock size={13} className="text-sky" />
                {doctor.timeSlots.map((slot, j) => (
                  <span key={j} className="time-slot">{slot}</span>
                ))}
              </div>
              <button onClick={() => handleRegister(doctor)} className="register-btn">
                预约挂号
              </button>
            </div>
          ))
        )}
      </div>

      {confirmDoctor && (
        <div className="modal-overlay" onClick={() => setConfirmDoctor(null)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">确认挂号信息</span>
              <button onClick={() => setConfirmDoctor(null)} className="modal-close">
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <div className="modal-doctor">
                <div className="modal-avatar">{confirmDoctor.name[0]}</div>
                <div className="modal-doctor-info">
                  <div className="modal-doctor-name">{confirmDoctor.name}</div>
                  <div className="modal-doctor-title">{confirmDoctor.title}</div>
                  <div className="modal-dept">{deptName}</div>
                </div>
              </div>
              <div className="modal-details">
                <div className="modal-row">
                  <span className="modal-label">就诊日期</span>
                  <span className="modal-value">2025年6月15日 周一</span>
                </div>
                <div className="modal-row">
                  <span className="modal-label">出诊时段</span>
                  <span className="modal-value">{confirmDoctor.timeSlots.join(' / ')}</span>
                </div>
                <div className="modal-row">
                  <span className="modal-label">就诊科室</span>
                  <span className="modal-value">{deptName}</span>
                </div>
                <div className="modal-row">
                  <span className="modal-label">就诊患者</span>
                  <span className="modal-value">{user.name}</span>
                </div>
              </div>
              <p className="modal-note">确认后将通过AI助手提交挂号申请</p>
            </div>
            <div className="modal-footer">
              <button onClick={() => setConfirmDoctor(null)} className="modal-btn modal-btn-cancel">取消</button>
              <button onClick={handleConfirm} className="modal-btn modal-btn-confirm">确认挂号</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


const scheduleData = [
  {
    name: '内科',
    doctors: [
      { name: '张明华', title: '主任医师', bio: '擅长心血管疾病诊疗，30年临床经验', timeSlots: ['08:00-12:00', '14:00-17:00'] },
      { name: '李芳', title: '副主任医师', bio: '呼吸系统疾病专家，擅长慢性病管理', timeSlots: ['08:00-12:00'] },
    ]
  },
  {
    name: '外科',
    doctors: [
      { name: '王建国', title: '主任医师', bio: '普外科及微创手术专家', timeSlots: ['09:00-12:00', '14:00-18:00'] },
      { name: '赵雪梅', title: '主治医师', bio: '骨科与运动损伤康复', timeSlots: ['14:00-17:00'] },
    ]
  },
  {
    name: '儿科',
    doctors: [
      { name: '陈小慧', title: '副主任医师', bio: '儿童呼吸及消化系统疾病', timeSlots: ['08:30-12:00', '14:00-16:30'] },
    ]
  },
  {
    name: '妇产科',
    doctors: [
      { name: '刘美玲', title: '主任医师', bio: '高危妊娠管理及妇科微创手术', timeSlots: ['08:00-12:00', '14:00-17:30'] },
    ]
  },
]


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
        <div className={`bubble ${isAI ? 'bubble-ai' : 'bubble-user'}`}>
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
