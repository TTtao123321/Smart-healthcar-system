import { useState, useEffect, useCallback, createContext, useContext, useRef } from 'react'
import {
  User, Lock, CheckCircle, ArrowRight,
  LogOut, Trash2, Send, Shield, Eye, EyeOff,
  MessageSquare, Plus, MessageCircle, UserCircle,
  Calendar, Clock, Stethoscope, ChevronDown, X
} from 'lucide-react'

const ToastContext = createContext(null)
const useToast = () => useContext(ToastContext)

export default function App() {
  const [toastMsg, setToastMsg] = useState(null)
  const [user, setUser] = useState(null)

  const showToast = useCallback((msg) => {
    setToastMsg(msg)
    setTimeout(() => setToastMsg(null), 2000)
  }, [])

  return (
    <ToastContext.Provider value={showToast}>
      <div className="min-h-screen relative overflow-hidden">
        {!user ? (
          <LoginPage onLogin={(u) => { setUser(u); showToast('登录成功，欢迎回来') }} />
        ) : (
          <ChatPage user={user} onLogout={() => { setUser(null); showToast('已退出登录') }} />
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
  const [username, setUsername] = useState('zhangsan')
  const [password, setPassword] = useState('zhangsan')
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)

  const submit = (e) => {
    e.preventDefault()
    if (username === 'zhangsan' && password === 'zhangsan') {
      setLoading(true)
      setTimeout(() => { setLoading(false); onLogin({ name: '张三', role: 'admin', avatar: null }) }, 600)
      return
    }
    showToast('账号或密码错误（默认: zhangsan/zhangsan）')
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
                type="text"
                placeholder="请输入用户名"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="login-input"
              />
            </div>
          </div>

          <div className="login-field">
            <div className="login-input-group">
              <Lock size={17} className="login-input-icon" />
              <input
                type={showPwd ? 'text' : 'password'}
                placeholder="请输入密码"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="login-input"
              />
              <button type="button" onClick={() => setShowPwd(!showPwd)} className="login-eye-btn">
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
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
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [aiThinking, setAiThinking] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }
  useEffect(() => { scrollToBottom() }, [messages])

  const aiReplies = {
    '\u611f\u5192': '根据您的描述，可能是上呼吸道感染。建议：\n\n1. **多休息**：保证充足睡眠，避免劳累\n2. **多饮水**：每日饮水 1500-2000ml\n3. **监测体温**：如发热超过 38.5\u00b0C 可使用退热药\n4. **观察症状**：如出现呼吸困难、持续高热，请及时就医\n\n\u26a0\ufe0f 以上建议仅供参考，不能替代医生诊断。',
    '\u5934\u75bc': '头疼可能由多种原因引起。请告诉我更多细节：\n\n- 疼痛部位（前额/后脑/太阳穴）\n- 疼痛性质（跳痛/胀痛/刺痛）\n- 持续时间\n- 有无恶心、畏光等症状\n\n同时建议：\n- 保持充足睡眠\n- 避免过度用眼\n- 适当按摩太阳穴',
    '\u5931\u7720': '改善睡眠质量可以尝试以下方法：\n\n\ud83c\udf19 **睡眠卫生**\n- 固定作息时间，每天同一时间上床和起床\n- 睡前 1 小时避免使用电子设备\n- 保持卧室安静、黑暗、凉爽\n\n\ud83e\uddd8 **放松技巧**\n- 睡前进行 10 分钟冥想或深呼吸\n- 温水泡脚 15-20 分钟\n\n\u26a0\ufe0f 如果失眠持续超过 2 周，建议咨询医生。',
    '\u9ad8\u8840\u538b': '关于高血压的管理，以下是一些建议：\n\n\ud83d\udc8a **用药管理**\n- 按时服药，不要自行停药\n- 定期监测血压并记录\n\n\ud83e\udd57 **饮食建议**\n- 低盐饮食（每日 < 6g）\n- 多吃蔬菜水果\n- 限制饮酒\n\n\ud83c\udfc3 **运动建议**\n- 每周至少 150 分钟中等强度运动\n- 如快走、游泳、太极等\n\n\ud83d\udccb 建议每 3 个月复查一次。',
  }

  const handleSend = () => {
    const text = input.trim()
    if (!text || aiThinking) return

    const userMsg = { id: Date.now(), role: 'user', text, time: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setAiThinking(true)

    setTimeout(() => {
      let reply
      let matched = false
      for (const [k, v] of Object.entries(aiReplies)) {
        if (text.includes(k)) { reply = v; matched = true; break }
      }
      if (!matched) {
        reply = '感谢您的咨询。根据您的描述，我建议：\n\n1. **初步评估**：您的症状需要进一步了解\n2. **建议检查**：可能需要相关检查以明确诊断\n3. **生活调整**：保持健康的生活方式\n\n\ud83d\udccc 为了给您更精准的建议，请详细描述：\n- 症状开始的时间\n- 症状的变化趋势\n- 是否有其他伴随症状\n\n\u26a0\ufe0f 本助手为 AI 辅助工具，不能替代专业医生诊断。如有紧急情况请立即就医。'
      }
      const aiMsg = { id: Date.now() + 1, role: 'ai', text: reply, time: new Date(), fullText: reply }
      setMessages(prev => [...prev, aiMsg])
      setAiThinking(false)
    }, 1000 + Math.random() * 1000)
  }

  const clearChat = () => setMessages([])

  return (
    <div className="chat-page">
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
        <LeftPanel user={user} />
        <ChatWindow
          messages={messages}
          aiThinking={aiThinking}
          input={input}
          setInput={setInput}
          onSend={handleSend}
          onClear={clearChat}
          messagesEndRef={messagesEndRef}
        />
        <RightPanel user={user} />
      </div>
    </div>
  )
}

function LeftPanel({ user }) {
  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <MessageSquare size={18} className="text-sky" />
        <span>对话记录</span>
      </div>
      <button className="new-chat-btn">
        <Plus size={15} /> 新对话
      </button>
      <div className="chat-list">
        {demoConversations.map((c, i) => (
          <div key={i} className={`chat-item ${i === 0 ? 'active' : ''}`}>
            <div className="chat-item-icon">
              <MessageCircle size={14} />
            </div>
            <div className="chat-item-content">
              <div className="chat-item-title">{c.title}</div>
              <div className="chat-item-preview">{c.preview}</div>
            </div>
            <span className="chat-item-time">{c.time}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function RightPanel({ user }) {
  const [expandedDept, setExpandedDept] = useState(null)
  const [confirmDoctor, setConfirmDoctor] = useState(null)
  const showToast = useToast()

  const handleRegister = (doctor) => {
    setConfirmDoctor(doctor)
  }

  const handleConfirm = () => {
    const deptForConfirm = expandedDept !== null ? scheduleData[expandedDept].name : confirmDoctor.dept
    showToast(`已成功预约 ${deptForConfirm} · ${confirmDoctor.name}，请按时就诊`)
    setConfirmDoctor(null)
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
          <button key={i} onClick={() => setExpandedDept(i)}
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
              <p className="modal-note">确认后将提交挂号申请，请按时到院就诊</p>
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


const demoConversations = [
  { title: '感冒咨询', preview: '根据您的描述，可能是上呼吸道感染...', time: '10:30' },
  { title: '头痛问题', preview: '头痛可能由多种原因引起...', time: '昨天' },
  { title: '失眠困扰', preview: '改善睡眠质量可以尝试以下方法...', time: '昨天' },
  { title: '体检报告解读', preview: '您的体检结果显示各项指标...', time: '周一' },
]

function ChatWindow({ messages, aiThinking, input, setInput, onSend, onClear, messagesEndRef }) {
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
        <button onClick={onClear} className="clear-btn">
          <Trash2 size={14} /> 清空
        </button>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && !aiThinking ? (
          <WelcomeScreen />
        ) : (
          <>
            {messages.map((msg, i) => (
              <ChatBubble key={msg.id} msg={msg} isLast={i === messages.length - 1 && msg.role === 'ai'} />
            ))}
            {aiThinking && <ThinkingBubble />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      <div className="chat-input-area">
        <div className="chat-input-row">
          <div className="chat-input-wrap">
            <input type="text" value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); onSend() } }}
              placeholder="描述您的症状或健康问题..." />
          </div>
          <button onClick={onSend} disabled={!input.trim() || aiThinking} className="chat-send-btn">
            发送 <Send size={14} />
          </button>
        </div>
        <p className="chat-disclaimer">AI 医疗助手仅供参考，不能替代医生诊断。如有紧急情况请立即就医。</p>
      </div>
    </div>
  )
}

function WelcomeScreen() {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">
        <Shield size={40} className="text-[#0EA5E9]" />
      </div>
      <h1 className="welcome-title">您好，我是您的 AI 医疗助手</h1>
      <p className="welcome-subtitle">请直接描述您的症状或健康问题，我会尽力为您解答</p>
    </div>
  )
}

function ChatBubble({ msg, isLast }) {
  const isAI = msg.role === 'ai'
  const [displayed, setDisplayed] = useState(isAI && isLast ? '' : msg.text)
  const [done, setDone] = useState(!(isAI && isLast))

  useEffect(() => {
    if (!isAI || !isLast) return
    let i = 0
    const full = msg.text
    setDisplayed('')
    setDone(false)
    const timer = setInterval(() => {
      i++
      setDisplayed(full.slice(0, i))
      if (i >= full.length) { clearInterval(timer); setDone(true) }
    }, 15)
    return () => clearInterval(timer)
  }, [msg.id, isAI, isLast])

  const timeStr = msg.time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className={`flex gap-3 ${isAI ? '' : 'flex-row-reverse'}`}>
      <div className={`bubble-avatar ${isAI ? 'bubble-avatar-ai' : 'bubble-avatar-user'}`}>
        {isAI ? <Shield size={15} className="text-white" /> : <User size={15} className="text-white" />}
      </div>
      <div className={`max-w-[72%] ${isAI ? '' : 'flex flex-col items-end'}`}>
        <div className={`bubble ${isAI ? 'bubble-ai' : 'bubble-user'}`}>
          {displayed}
          {!done && <span className="typing-cursor" />}
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

