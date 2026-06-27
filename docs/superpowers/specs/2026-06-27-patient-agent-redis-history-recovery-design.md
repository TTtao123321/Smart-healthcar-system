# patient_agent 本地缓存过期后从 Redis 恢复历史会话设计

**日期：** 2026-06-27
**范围：** `patient_agent_backend`、`patient_agent_frontend`

## 概述

当前 `patient_agent` 的聊天历史正文存储在 Redis 中，key 形式为：

- `chat:memory:{patient_id}:{thread_id}`

前端展示历史会话时，依赖浏览器本地缓存保存：

- 会话列表
- 每条会话对应的 `thread_id`
- 已加载过的消息内容

当浏览器本地缓存 1 天后过期删除时，前端虽然还能通过登录态拿到当前 `patient_id`，但已经不知道该患者有哪些历史 `thread_id`。而后端目前只有按 `thread_id` 获取单条历史的接口，没有“按患者列出历史会话”的能力。

这会导致一种不一致：

- Redis 中聊天正文仍然存在
- 患者重新登录后却无法找回自己的历史会话入口

本次改造目标是让患者在浏览器缓存过期后，仍然可以从 Redis 中恢复自己所有历史会话，并在恢复成功后重新写入浏览器缓存，继续沿用当前“本地优先、后端兜底”的前端交互方式。

## 当前问题

### 1. Redis 只有正文，没有线程索引

- 当前 Redis 只保存 `chat:memory:{patient_id}:{thread_id}`
- 没有维护“该患者有哪些历史会话”的列表
- 无法按 `patient_id` 直接列出所有 `thread_id`

### 2. 后端接口只能按 thread_id 取历史

- 当前接口只有 `GET /api/chat/history?thread_id=...`
- 它要求前端已知 `thread_id`
- 本地缓存过期后，前端无法构造正确的查询参数

### 3. 前端本地缓存过期后无法自恢复

- 当前前端切换会话时支持“本地没有就去后端拉正文”
- 但这套逻辑的前提是前端已有线程列表和对应的 `thread_id`
- 一旦线程列表本身过期，历史会话入口也一并丢失

## 设计目标

### 业务目标

- 患者在本地缓存 1 天后过期的情况下，重新登录仍能看到自己的历史会话列表
- 历史会话恢复后，前端仍保持现有的会话切换体验
- 不让不同患者之间恢复到彼此的会话列表或会话正文

### 技术目标

- 在 Redis 中补齐“按患者列出历史线程”的索引能力
- 保留当前正文存储结构，避免大规模改动
- 让前端恢复历史后，重新回填浏览器缓存并重置本地 1 天 TTL
- 保持会话正文按需懒加载，避免登录时拉取全部正文

## 方案对比

### 方案 A：Redis 会话索引 + 线程摘要 + 正文懒加载

推荐方案。

- 正文继续存在 `chat:memory:{patient_id}:{thread_id}`
- 新增患者级线程索引
- 新增线程摘要数据
- 前端登录后先恢复线程列表，再按需获取正文

优点：

- 与当前 Redis 正文结构兼容
- 查询路径清晰，性能可控
- 能满足“恢复所有历史会话”
- 前端只在用户点开某条会话时才拉取正文

缺点：

- 需要新增索引维护逻辑

### 方案 B：登录时直接扫描 `chat:memory:{patient_id}:*`

不推荐。

- 由后端每次登录后在 Redis 中按 pattern 扫描所有正文 key
- 从 key 中提取 `thread_id`，再解析正文生成列表

问题：

- Redis `SCAN` 成本不可控
- 历史会话量增大后，性能会退化
- 难以稳定维护排序、标题、摘要等元信息

### 方案 C：把会话索引落 MySQL

本次不采用。

- 查询稳定，但超出当前问题边界
- 需要引入持久化表结构和额外同步逻辑

## 推荐方案

采用“Redis 会话索引 + 线程摘要 + 正文懒加载 + 前端恢复后回填本地缓存”的方案。

## Redis 数据模型

### 1. 保留正文 key

继续保留现有聊天正文：

- `chat:memory:{patient_id}:{thread_id}`

value 仍为消息数组 JSON。

### 2. 新增患者级线程索引

新增：

- `chat:threads:{patient_id}`

建议存储为 Redis Sorted Set。

用途：

- member：`thread_id`
- score：最近更新时间时间戳

这样可以高效按最近活跃时间倒序列出该患者全部线程。

### 3. 新增线程摘要 key

新增：

- `chat:threadmeta:{patient_id}:{thread_id}`

建议存储为 Redis Hash 或 JSON 字符串，字段至少包括：

- `thread_id`
- `title`
- `last_message`
- `updated_at`
- `message_count`

其中：

- `title`：首次用户消息的裁剪标题，保持与前端现有逻辑一致
- `last_message`：最后一条可见消息摘要
- `updated_at`：最近更新时间
- `message_count`：当前会话消息条数

## Redis 读写规则

### 1. 保存正文时同步维护索引

当前在保存会话历史正文时，同时更新：

1. `chat:memory:{patient_id}:{thread_id}`
2. `chat:threads:{patient_id}`
3. `chat:threadmeta:{patient_id}:{thread_id}`

即：

- 保存正文
- 将 `thread_id` 写入患者线程索引
- 更新线程摘要
- 刷新三类 key 的 TTL

### 2. TTL 统一规则

保持与当前聊天正文一致，统一为 7 天：

- 正文 TTL：7 天
- 线程索引 TTL：7 天
- 线程摘要 TTL：7 天

每次该线程有新消息时，统一刷新上述 TTL。

设计意图：

- 只要正文还在，线程列表入口也还在
- 避免正文存在但索引提前消失，导致“有数据却列不出来”

### 3. 删除线程时同步清理

若前端支持删除单条会话，则后端也必须提供对应删除能力，统一清理：

- `chat:memory:{patient_id}:{thread_id}`
- `chat:threadmeta:{patient_id}:{thread_id}`
- `chat:threads:{patient_id}` 中对应 member

否则会出现：

- 前端本地删掉
- 本地缓存过期后又从 Redis 恢复回来

## 后端接口设计

### 1. 保留现有接口

继续保留：

- `GET /api/chat/history?thread_id=...`

用途不变：

- 根据当前登录患者 `patient_id` 和指定 `thread_id` 获取正文

### 2. 新增历史会话列表接口

新增：

- `GET /api/chat/threads`

鉴权要求：

- 必须登录
- 只能读取当前 session 对应 `patient_id` 的线程列表

返回结构建议：

```json
{
  "threads": [
    {
      "thread_id": "c5c9f3f2-6cbe-4c1e-ae3d-d6f2d8c5c201",
      "title": "我想挂号心内科",
      "last_message": "已为您查询到今天可预约的医生排班。",
      "updated_at": "2026-06-27T14:00:00",
      "message_count": 8
    }
  ]
}
```

排序规则：

- 按 `updated_at` 倒序

### 3. 可选新增删除接口

若要保证“删除会话后不再恢复”，建议新增：

- `DELETE /api/chat/threads/{thread_id}`

行为：

- 校验该线程属于当前登录患者
- 删除正文、摘要和索引项

本接口虽然不是“恢复历史”最小闭环的硬性前置，但属于强烈建议补齐的一致性能力。

## 后端模块调整建议

### 1. `RedisMemory`

在现有正文保存/读取能力之上新增：

- `save_thread_meta(...)`
- `list_threads(patient_id, limit?)`
- `delete_thread(patient_id, thread_id)`

保持责任边界：

- `RedisMemory` 统一负责 Redis key 的读写与序列化
- API 层只负责鉴权和返回格式

### 2. `chat/orchestrator.py`

在保存历史正文的位置，同步维护线程摘要和索引。

当前保存历史入口在：

- [orchestrator.py](file:///Users/bytedance/Desktop/mywork/Smart-healthcar-system/patient_agent_backend/app/chat/orchestrator.py#L54-L65)

这里应补充：

- 标题生成逻辑
- 最后消息摘要更新
- message_count 统计

### 3. `app/api/chat.py`

新增：

- `GET /api/chat/threads`

可选新增：

- `DELETE /api/chat/threads/{thread_id}`

## 前端恢复策略

### 1. 登录后恢复顺序

登录成功或页面初始化后，按以下顺序恢复：

1. 尝试读取本地 `patient_threads:{patient_id}`
2. 若本地会话列表存在且未过期，则直接使用本地
3. 若本地会话列表为空或已过期，则请求 `GET /api/chat/threads`
4. 将恢复得到的线程列表重新写入本地缓存
5. 本地缓存 TTL 重新设置为 1 天

### 2. 正文仍采用懒加载

前端不在登录后一次性拉取所有正文。

保持现有交互：

- 先展示线程列表
- 用户点击某个线程时，再调用 `/api/chat/history?thread_id=...`
- 获取到正文后，重新写入 `patient_messages:{patient_id}`

这样可以：

- 保持首屏恢复开销可控
- 避免用户历史消息很多时登录变慢

### 3. 恢复成功后重新写入浏览器缓存

这是本次设计的强制要求。

原因：

- 如果只从 Redis 恢复但不回填本地缓存，页面刷新后仍会再次回到“无会话列表”状态
- 回填本地缓存后，后续仍可继续使用“本地优先、后端兜底”的既有逻辑

回填规则：

- 恢复线程列表后，写回 `patient_threads:{patient_id}`，TTL 重置为 1 天
- 恢复正文后，写回 `patient_messages:{patient_id}`，TTL 重置为 1 天

### 4. 恢复失败时的回退行为

- 若 `/api/chat/threads` 返回空列表，则前端写入空列表缓存
- 若某条线程列表存在，但正文已过期，则点击后显示空消息或无历史内容
- 不做伪恢复，不生成假线程

## 前端模块调整建议

### 1. `App.jsx`

扩展当前页面初始化逻辑：

- 当本地 `threads` 为空或过期时，主动从 `/api/chat/threads` 恢复
- 恢复后重新写入本地患者隔离缓存

现有会话切换逻辑可基本保留，因为它已经支持：

- 本地没有某线程消息时，再请求 `/api/chat/history`

### 2. `api/index.js`

新增：

- `chatApi.getThreads()`

可选新增：

- `chatApi.deleteThread(threadId)`

## 数据流

```text
患者重新登录
  -> 拿到当前 patient_id
  -> 读取 patient_threads:{patient_id}
  -> 若本地有效，直接展示
  -> 若本地失效，调用 GET /api/chat/threads
  -> 后端从 chat:threads:{patient_id} + chat:threadmeta:{patient_id}:{thread_id} 组装列表
  -> 前端收到 threads 后写回 patient_threads:{patient_id}

用户点击某条历史会话
  -> 调用 GET /api/chat/history?thread_id=...
  -> 后端按 chat:memory:{patient_id}:{thread_id} 返回正文
  -> 前端写回 patient_messages:{patient_id}
```

## 边界条件

### 1. 本地缓存过期但 Redis 仍在

- 可以恢复线程列表
- 可以按需恢复正文
- 恢复成功后重建本地缓存

### 2. 线程索引在，正文已过期

- 线程仍可出现在列表中
- 点击后拿不到消息正文

建议行为：

- 前端显示空消息
- 或提示“该历史会话内容已过期”

### 3. Redis 索引丢失但正文残留

- 当前推荐方案通过统一刷新 TTL 来尽量避免
- 若仍发生，则以“无法恢复线程列表”为准，不做 Redis 扫描补救

### 4. 不同患者隔离

- 所有线程列表与正文查询都必须基于当前 session 的 `patient_id`
- 不允许前端自行传入 `patient_id`
- 只允许传 `thread_id`

## 测试与验证

### 1. 后端验证

至少覆盖：

1. 同一患者产生多条会话后，`GET /api/chat/threads` 能按更新时间倒序返回全部线程
2. 不同患者登录后，只能看到自己的线程列表
3. 更新某条会话后，其 `updated_at` 和排序会刷新
4. 删除线程后，索引、摘要、正文均被清理

### 2. 前端验证

至少覆盖：

1. 本地 `threads/messages` 过期后，登录仍能恢复线程列表
2. 恢复后的线程列表会重新写回本地缓存
3. 点击历史线程后，正文能从 Redis 取回并重新写回本地缓存
4. 刷新页面后，优先读取刚刚回填的本地缓存，不重复请求线程列表

## 非目标

- 不在本次改造中引入 MySQL 会话表
- 不一次性拉取所有历史正文
- 不为 Redis 中残留但未建索引的旧数据做兼容扫描恢复
- 不改变当前 token/session 的 Redis 存储模型

## 实施建议

建议按以下顺序实施：

1. 为 `RedisMemory` 增加线程索引和摘要能力
2. 新增 `/api/chat/threads` 接口
3. 让正文保存时同步维护索引和摘要
4. 前端新增 `getThreads()`，在本地线程缓存缺失时调用
5. 恢复成功后回填 `patient_threads:{patient_id}` 与 `patient_messages:{patient_id}`
