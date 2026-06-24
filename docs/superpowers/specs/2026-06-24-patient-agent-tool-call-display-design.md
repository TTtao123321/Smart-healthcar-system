# Patient Agent 工具调用信息展示 — 设计文档

**日期**: 2026-06-24
**状态**: 已确认

## 概述

在 patient_agent 前端聊天界面中，模型回复内容框上方新增工具调用信息展示功能。用户可点击工具图标查看具体的调用信息（工具名、调用参数、返回结果、状态）。

## 一、后端改动 — SSE 流扩展

### 文件
`patient_agent_backend/app/api/chat.py` — `chat_stream` 函数

### 改动点

在 `astream_events` 循环中新增对两种 LangGraph 事件的监听：

| 事件 | 触发时机 | SSE event 名 | 数据字段 |
|------|---------|-------------|---------|
| `on_tool_start` | 工具开始调用 | `tool_start` | `tool_call_id`, `tool_name`, `tool_args` |
| `on_tool_end` | 工具调用结束 | `tool_end` | `tool_call_id`, `tool_name`, `tool_result`（成功）/ `tool_error`（失败） |

### SSE 数据格式示例

```
event:tool_start
data:{"tool_call_id":"call_xxx","tool_name":"query_dept","tool_args":{"dept_name":"内科"}}

event:tool_end
data:{"tool_call_id":"call_xxx","tool_name":"query_dept","tool_result":"内科有张明华主任医师、李芳副主任医师"}
```

错误情况：
```
event:tool_end
data:{"tool_call_id":"call_xxx","tool_name":"query_dept","tool_error":"查询超时，请稍后重试"}
```

## 二、前端数据结构

### 消息对象扩展

AI 消息对象新增 `toolCalls` 字段：

```js
{
  id: '...',
  role: 'ai',
  text: '',
  time: new Date(),
  streaming: true,
  toolCalls: [],  // 新增
}
```

### toolCalls 条目结构

```js
{
  toolCallId: 'call_xxx',
  toolName: 'query_dept',
  toolArgs: { dept_name: '内科' },
  status: 'running' | 'success' | 'error',
  toolResult: '...',   // status=success 时
  toolError: '...',    // status=error 时
}
```

## 三、前端 SSE 解析

在 `handleSend` 的流式读取循环中，新增对 `tool_start` 和 `tool_end` 事件的处理：

- `tool_start` → 向当前 AI 消息的 `toolCalls` 数组 push 一个 `status: 'running'` 的条目，通过 `setMessagesMap` 更新
- `tool_end` → 根据 event data 中是否有 `tool_error`，更新对应条目为 `status: 'success'` 或 `status: 'error'`

## 四、前端 UI — ToolCallBar 组件

### 位置
在 AI 回复气泡（`ChatBubble`）**上方**，纵向展示，每个工具调用一行。

### 外观设计

每个工具调用条目为一个紧凑的横向条：

- **左侧图标**：根据状态变化
  - 调用中 → 旋转的 `Loader` 图标
  - 成功 → 绿色 `CheckCircle` 图标
  - 失败 → 红色 `XCircle` 图标
- **工具名称**：使用中文映射显示
- **右侧箭头**：`ChevronDown` / `ChevronUp`，点击展开/折叠详情

### 展开详情面板

点击条目后展开，显示：
- 调用参数（JSON 格式化展示）
- 返回结果（成功时）
- 错误信息（失败时，红色文字）

### 工具名中文映射

```js
const TOOL_NAME_MAP = {
  query_dept: '查询科室',
  query_doctor: '查询医生',
  query_registration: '查询挂号',
  register: '预约挂号',
}
```

### 样式
- 整体区域：圆角卡片，浅蓝背景（`#F0F9FF`），内边距 8px
- 条目 hover 时轻微高亮
- 展开面板有平滑过渡动画
- 与 AI 气泡风格协调，位于气泡上方，间距 8px

## 五、改动范围

| 文件 | 改动类型 | 改动量 |
|------|---------|-------|
| `patient_agent_backend/app/api/chat.py` | 修改 | ~15 行新增 |
| `patient_agent_frontend/src/App.jsx` | 修改 | ~80 行新增（组件 + SSE 解析 + 状态） |
| `patient_agent_frontend/src/index.css` | 修改 | ~50 行新增样式 |

## 六、边界情况

- 无工具调用时：`toolCalls` 为空数组，不渲染 ToolCallBar
- 工具调用失败时：显示红色错误状态，用户可展开查看错误详情
- 多工具调用时：纵向排列，按调用顺序展示
- 切换对话时：历史消息若包含 toolCalls 数据则正常展示，否则不展示