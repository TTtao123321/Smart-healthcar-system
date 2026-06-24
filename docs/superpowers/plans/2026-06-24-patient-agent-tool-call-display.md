# Patient Agent 工具调用信息展示 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 patient_agent 前端聊天界面中，模型回复内容框上方展示工具调用信息（工具名、参数、结果、状态），支持点击展开/折叠查看详情。

**Architecture:** 后端通过 LangGraph 的 `astream_events` 捕获 `on_tool_start` / `on_tool_end` 事件，通过 SSE 推送给前端。前端在流式处理器中解析工具事件，存入消息对象的 `toolCalls` 数组，由 `ToolCallBar` 组件在 AI 气泡上方渲染，纵向列表展示，点击展开详情。

**Tech Stack:** React + Vite + Tailwind CSS + lucide-react（前端），Python FastAPI + LangGraph + sse-starlette（后端）

## Global Constraints

- 前端所有代码在 `App.jsx`（单文件组件），样式在 `index.css`
- 使用 lucide-react 图标库（已引入 `Loader`, `CheckCircle`, `XCircle`, `ChevronDown`, `ChevronUp`, `Wrench`）
- 后端 SSE 事件格式：`event:xxx\ndata:json\n\n`
- 工具名使用中文映射，未映射的显示原始名称

---

### Task 1: 后端 — SSE 流添加工具调用事件

**Files:**
- Modify: `patient_agent_backend/app/api/chat.py:133-146`

**Interfaces:**
- Consumes: LangGraph `astream_events` v2 事件流
- Produces: SSE 事件 `tool_start`（`tool_call_id`, `tool_name`, `tool_args`）和 `tool_end`（`tool_call_id`, `tool_name`, `tool_result` 或 `tool_error`）

- [ ] **Step 1: 在 `astream_events` 循环中添加 `on_tool_start` 和 `on_tool_end` 事件处理**

在 `chat.py` 第 133 行的 `async for event in graph.astream_events(state, version="v2"):` 循环体内，`kind == "on_chat_model_stream"` 分支之后，新增两个事件处理分支。

编辑 `patient_agent_backend/app/api/chat.py`，在 `on_chat_model_stream` 处理块之后（第 146 行 `}` 之后，第 148 行 `# 保存对话历史` 之前）插入：

```python
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    run_id = event.get("run_id", "")
                    # 将不可序列化的参数转为字符串
                    safe_args = {}
                    for k, v in tool_input.items():
                        try:
                            json.dumps(v)
                            safe_args[k] = v
                        except (TypeError, ValueError):
                            safe_args[k] = str(v)
                    yield {
                        "event": "tool_start",
                        "data": json.dumps(
                            {
                                "tool_call_id": run_id,
                                "tool_name": tool_name,
                                "tool_args": safe_args,
                            },
                            ensure_ascii=False,
                        ),
                    }

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    run_id = event.get("run_id", "")
                    output = event.get("data", {}).get("output")
                    if output is not None:
                        yield {
                            "event": "tool_end",
                            "data": json.dumps(
                                {
                                    "tool_call_id": run_id,
                                    "tool_name": tool_name,
                                    "tool_result": str(output),
                                },
                                ensure_ascii=False,
                            ),
                        }
```

- [ ] **Step 2: 验证后端改动**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend && python -c "from app.api.chat import router; print('OK')"
```

- [ ] **Step 3: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add patient_agent_backend/app/api/chat.py && git commit -m "feat: add tool call events to SSE stream"
```

---

### Task 2: 前端 — 消息数据结构扩展 + SSE 工具事件解析

**Files:**
- Modify: `patient_agent_frontend/src/App.jsx`

**Interfaces:**
- Consumes: SSE `tool_start` / `tool_end` 事件
- Produces: 消息对象中的 `toolCalls` 数组（元素类型：`{ toolCallId, toolName, toolArgs, status, toolResult?, toolError? }`）

- [ ] **Step 1: 在 App.jsx 顶部添加工具名中文映射常量**

在 `App.jsx` 的 `STORAGE_KEYS` 常量定义之后（约第 41 行），添加：

```js
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
```

- [ ] **Step 2: 在 handleSend 中初始化 toolCalls 字段**

在 `handleSend` 中创建 `aiMsg` 对象时（约第 322 行），添加 `toolCalls: []`：

```js
const aiMsg = { id: aiMsgId, role: 'ai', text: '', time: new Date(), streaming: true, toolCalls: [] }
```

- [ ] **Step 3: 在 SSE 流式读取循环中解析 tool_start / tool_end 事件**

在 `handleSend` 的 SSE 解析循环中（约第 355-399 行），在现有的 `event:message` / `event:done` / `event:error` 处理分支旁边，新增 `tool_start` 和 `tool_end` 处理。

在 `line.startsWith('event:error')` 分支之后、`else if (line.startsWith('data:'))` 分支之前，添加：

```js
          } else if (line.startsWith('event:tool_start')) {
            // 下一行 data 是工具调用开始信息
          } else if (line.startsWith('event:tool_end')) {
            // 下一行 data 是工具调用结束信息
```

然后在 `data:` 解析分支中，在现有的 `if (data.content !== undefined)` 块之后、`if (data.thread_id)` 之前，添加 tool 事件的数据处理：

```js
              if (data.tool_call_id && data.tool_name && data.tool_args) {
                // tool_start
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
              } else if (data.tool_call_id && data.tool_name && (data.tool_result !== undefined || data.tool_error !== undefined)) {
                // tool_end
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
```

- [ ] **Step 4: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add patient_agent_frontend/src/App.jsx && git commit -m "feat: add tool call data parsing in SSE stream handler"
```

---

### Task 3: 前端 — ToolCallBar 组件 + ChatBubble 集成

**Files:**
- Modify: `patient_agent_frontend/src/App.jsx`

**Interfaces:**
- Consumes: 消息对象的 `toolCalls` 数组
- Produces: `ToolCallBar` 组件（在 `ChatBubble` 上方渲染，纵向列表，点击展开/折叠详情）

- [ ] **Step 1: 添加 ToolCallBar 组件**

在 `App.jsx` 中，`ChatBubble` 组件定义之前，添加 `ToolCallBar` 组件：

```jsx
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
```

- [ ] **Step 2: 在 ChatBubble 中集成 ToolCallBar**

在 `ChatBubble` 组件中，在 AI 气泡渲染之前插入 `ToolCallBar`。找到 `ChatBubble` 的 return 语句（约第 816 行），在 `bubble` div 之前添加：

```jsx
      <div className={`max-w-[72%] ${isAI ? '' : 'flex flex-col items-end'}`}>
        {isAI && msg.toolCalls && msg.toolCalls.length > 0 && (
          <ToolCallBar toolCalls={msg.toolCalls} />
        )}
        <div className={`bubble ${isAI ? 'bubble-ai' : 'bubble-user'}`}>
```

注意：这会替换原来 `ChatBubble` 中 `max-w-[72%]` div 内部的 `bubble` div 直接渲染。完整替换如下：

原来的代码：
```jsx
      <div className={`max-w-[72%] ${isAI ? '' : 'flex flex-col items-end'}`}>
        <div className={`bubble ${isAI ? 'bubble-ai' : 'bubble-user'}`}>
          {displayed}
          {!done && displayed && <span className="typing-cursor" />}
        </div>
        <span className="msg-time">{timeStr}</span>
      </div>
```

替换为：
```jsx
      <div className={`max-w-[72%] ${isAI ? '' : 'flex flex-col items-end'}`}>
        {isAI && msg.toolCalls && msg.toolCalls.length > 0 && (
          <ToolCallBar toolCalls={msg.toolCalls} />
        )}
        <div className={`bubble ${isAI ? 'bubble-ai' : 'bubble-user'}`}>
          {displayed}
          {!done && displayed && <span className="typing-cursor" />}
        </div>
        <span className="msg-time">{timeStr}</span>
      </div>
```

- [ ] **Step 3: 验证前端构建**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

- [ ] **Step 4: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add patient_agent_frontend/src/App.jsx && git commit -m "feat: add ToolCallBar component with expand/collapse details"
```

---

### Task 4: 前端 — ToolCallBar 样式

**Files:**
- Modify: `patient_agent_frontend/src/index.css`

**Interfaces:**
- 为 Task 3 的 ToolCallBar 组件提供样式

- [ ] **Step 1: 在 index.css 末尾添加 ToolCallBar 样式**

在 `patient_agent_frontend/src/index.css` 文件末尾追加：

```css
/* ========== TOOL CALL BAR ========== */
.tool-call-bar {
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-call-item {
  background: #F0F9FF;
  border: 1px solid #BAE6FD;
  border-radius: 10px;
  overflow: hidden;
  transition: box-shadow 0.15s;
}

.tool-call-item:hover {
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.08);
}

.tool-call-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.tool-call-row:hover {
  background: rgba(186, 230, 253, 0.3);
}

.tool-call-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.tool-call-spinner {
  animation: tool-call-spin 1s linear infinite;
  color: #0EA5E9;
}

@keyframes tool-call-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.tool-call-name {
  font-size: 13px;
  font-weight: 500;
  color: #334155;
  flex: 1;
}

.tool-call-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
}

.tool-call-status-running {
  background: #FEF3C7;
  color: #D97706;
}

.tool-call-status-success {
  background: #D1FAE5;
  color: #059669;
}

.tool-call-status-error {
  background: #FEE2E2;
  color: #DC2626;
}

.tool-call-chevron {
  color: #94A3B8;
  flex-shrink: 0;
}

.tool-call-detail {
  padding: 0 12px 10px;
  border-top: 1px solid #BAE6FD;
  display: flex;
  flex-direction: column;
  gap: 8px;
  animation: tool-call-detail-in 0.2s ease-out;
}

@keyframes tool-call-detail-in {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.tool-call-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-call-label {
  font-size: 11px;
  font-weight: 600;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tool-call-code {
  font-size: 12px;
  line-height: 1.5;
  color: #334155;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  padding: 8px 10px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'SF Mono', 'Fira Code', 'Fira Mono', Menlo, Consolas, monospace;
  max-height: 200px;
  overflow-y: auto;
}

.tool-call-error {
  color: #DC2626;
  background: #FEF2F2;
  border-color: #FECACA;
}

.text-emerald { color: #059669; }
```

- [ ] **Step 2: 验证样式不冲突**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_frontend && npm run build
```

- [ ] **Step 3: 提交**

```bash
cd /Users/bytedance/Desktop/mywork/Smart-healthcar-system && git add patient_agent_frontend/src/index.css && git commit -m "style: add ToolCallBar styles with expand/collapse animation"
```

---

### 最终验证

- [ ] **验证完整流程**

启动后端和前端，发送一条需要工具调用的消息（如"有哪些科室"），确认工具调用信息在前端正确展示。