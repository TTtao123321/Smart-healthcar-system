# patient_agent 前端本地缓存按患者隔离与 1 天过期设计

**日期：** 2026-06-27
**范围：** `patient_agent_frontend`

## 概述

当前 `patient_agent_frontend` 将登录态、会话列表和消息缓存统一存放在固定的 `localStorage` key 下：

- `patient_token`
- `patient_user`
- `patient_threads`
- `patient_messages`

这会导致同一浏览器中，不同患者账号之间共享本地缓存空间。若前一位患者未显式退出，或 token 失效后未完整清理本地数据，后一位患者可能看到上一位患者残留的会话列表和消息内容。

本次改造采用“双保险”方案：

1. 所有本地缓存按 `patient_id` 做命名隔离
2. 所有本地缓存增加 1 天 TTL，到期自动失效

改造后，前端同一浏览器中的不同患者拥有各自独立的本地缓存命名空间；即使用户不手动退出，缓存也只保留 1 天，避免长期残留历史数据。

## 当前问题

### 1. 本地缓存未按患者隔离

- 当前 `localStorage` key 为全局固定值，不包含 `patient_id`
- 登录不同患者时，会复用同一份 `patient_threads` 和 `patient_messages`
- 会话切换优先读取本地缓存，因此存在串会话记录的风险

### 2. 失效清理不完整

- 主动退出登录时会清理 `token/user/threads/messages`
- 但接口返回 `401` 时，当前只清理 `patient_token` 和 `patient_user`
- 一旦 session 失效但本地消息仍在，页面仍可能展示过期的会话内容

### 3. localStorage 没有原生 TTL

- 浏览器不会自动删除过期的 `localStorage`
- 旧缓存若不显式清理，可能长期保留
- 即使后端 Redis session 已过期，本地会话列表和消息仍可能存在

## 设计目标

### 业务目标

- 确保不同患者在同一浏览器中的本地聊天缓存互不串扰
- 减少过期本地缓存导致的“像已登录”或“看到旧会话”的误导
- 保持现有聊天、切换会话和历史加载体验基本不变

### 技术目标

- 让本地缓存具备患者维度隔离能力
- 让本地缓存具备 1 天自动失效能力
- 让登录、登出、401、切换账号等关键链路的缓存清理规则一致
- 尽量将改造限制在前端存储层，不改后端接口契约

## 推荐方案

采用“按患者隔离的 key 命名 + 包装存储对象 + 惰性过期 + 关键时机主动清理”的方案。

### 方案说明

- 将会话列表、消息缓存、用户信息改为按 `patient_id` 命名的 key
- 将 `token` 保持为全局当前登录态 key，但其 value 也带 1 天过期元信息
- 所有缓存 value 不再直接存业务数据，而是统一包装为带 `expires_at` 的对象
- 读取缓存时同时校验“是否属于当前患者”和“是否已过期”
- 登录成功、手动退出、接口 `401`、页面初始化时均执行一次主动清理

### 为什么不只做单一方案

- 只做 key 隔离：仍会留下长期不清理的旧缓存
- 只做 TTL：不同患者仍可能在 TTL 时间窗内读到上一位患者残留数据
- 同时做二者，才能同时解决“串患者”和“旧缓存长期驻留”两个问题

## 缓存模型设计

### 1. 全局 key

保留以下全局 key，用于表达“当前登录患者”：

- `patient_token`
- `patient_current_user`

其中：

- `patient_token` 保存当前患者 token 包装对象
- `patient_current_user` 保存当前患者最小身份信息包装对象，至少包含 `patient_id`、`name`、`phone`

这两个 key 仍然只有一份，因为系统当前本身只允许前端页面处于一个“当前患者登录态”。

### 2. 按患者隔离的 key

新增按患者隔离的命名规则：

- `patient_threads:{patient_id}`
- `patient_messages:{patient_id}`
- `patient_user:{patient_id}`

说明：

- `patient_threads:{patient_id}` 保存该患者的会话列表
- `patient_messages:{patient_id}` 保存该患者的消息映射 `messagesMap`
- `patient_user:{patient_id}` 保存该患者最近一次登录后的用户信息快照，便于恢复页面显示

### 3. 包装对象格式

统一使用如下存储结构：

```json
{
  "value": {},
  "patient_id": 1,
  "expires_at": 1782652800000
}
```

字段约定：

- `value`：实际业务数据
- `patient_id`：该缓存所属患者
- `expires_at`：毫秒级时间戳，固定为写入时间 + 1 天

对 `patient_token` 也使用相同包装方式，只是其 `value` 为 token 字符串。

## TTL 规则

### 1. TTL 常量

- TTL 固定为 `24 * 60 * 60 * 1000`
- 即 1 天

### 2. 过期判断

读取任何缓存前，统一进行以下判断：

1. key 是否存在
2. value 是否可正常 JSON 解析
3. `expires_at` 是否存在且未过期
4. 若为患者隔离 key，`patient_id` 是否与当前患者一致

只要任一检查失败，立即删除该 key，并返回空值或默认值。

### 3. 续期策略

本次不采用“读一次就续期”的滑动过期策略。

原因：

- 目标是限制旧缓存最长仅保留 1 天
- 若采用滑动续期，用户长期使用同一浏览器时，历史消息可能无限保留
- 固定 TTL 更符合本次“减少本地驻留时间”的隐私目标

## 关键流程设计

### 1. 页面启动

页面初始化时：

1. 读取 `patient_current_user`
2. 若不存在或已过期，则清空当前登录态相关 key 并进入未登录态
3. 若存在，则取出 `patient_id`
4. 使用该 `patient_id` 读取 `patient_user:{patient_id}`、`patient_threads:{patient_id}`、`patient_messages:{patient_id}`
5. 读取过程中如果发现任意 key 过期或损坏，立即删除并回退为空数据

### 2. 登录成功

登录成功后：

1. 解析服务端返回的 `patient_id`
2. 读取当前全局 `patient_current_user`
3. 若旧患者存在且 `old_patient_id != new_patient_id`，主动清理上一位患者的：
   - `patient_user:{old_patient_id}`
   - `patient_threads:{old_patient_id}`
   - `patient_messages:{old_patient_id}`
4. 写入新的：
   - `patient_token`
   - `patient_current_user`
   - `patient_user:{new_patient_id}`
5. 当前患者的 `threads/messages` 初始为空，后续随使用过程再写入

这样可以保证“切换账号时立即清上一位患者缓存”，不依赖 TTL 被动淘汰。

### 3. 主动退出登录

退出登录时：

1. 读取当前患者 `patient_id`
2. 删除全局 key：
   - `patient_token`
   - `patient_current_user`
3. 删除该患者隔离 key：
   - `patient_user:{patient_id}`
   - `patient_threads:{patient_id}`
   - `patient_messages:{patient_id}`
4. 清空内存态 `user / threads / messages`

### 4. 接口 401

当任意受保护接口返回 `401` 时，执行与“主动退出登录”相同的完整清理流程，而不是仅清理 token 和 user。

这样可以避免：

- token 已失效
- 但页面里仍保留旧的会话列表和消息缓存

### 5. 会话切换

会话切换逻辑保持现状：

- 先读当前患者的本地 `messagesMap`
- 若当前线程本地无数据，再请求 `/api/chat/history`

变化点只有一处：

- `messagesMap` 不再来自共享 key，而是来自 `patient_messages:{patient_id}`

因此不会跨患者读取到错误线程内容。

### 6. 旧 key 迁移

本次不做复杂迁移，采用“一次性清理旧共享 key”的保守策略。

页面初始化时若发现以下旧 key 存在，则直接删除：

- `patient_user`
- `patient_threads`
- `patient_messages`

原因：

- 旧共享数据本身已经不安全
- 无法可靠判断其归属患者
- 强行迁移会放大串数据风险

## 模块改造建议

### 1. `App.jsx`

新增或内聚以下能力：

- 统一的缓存包装读写函数
- 当前患者 ID 解析函数
- 按患者生成 key 的函数
- 完整的“清理当前患者缓存”函数
- 登录成功后的跨患者切换清理逻辑
- 页面初始化的旧 key 清理与 TTL 校验逻辑

### 2. `api/index.js`

将现有 `401` 拦截器从“只删 `patient_token` / `patient_user`”改为调用统一清理逻辑，完整清掉当前患者本地缓存。

### 3. 不改动后端

后端当前已通过 Redis key `chat:memory:{patient_id}:{thread_id}` 实现按患者隔离，本次无需调整：

- `/api/auth/login`
- `/api/chat/history`
- Redis Memory 实现

## 数据流

```text
登录成功
  -> 获取 token / patient_id / name
  -> 识别旧当前患者
  -> 如切换患者，清理旧患者隔离缓存
  -> 写入 patient_token / patient_current_user / patient_user:{patient_id}

聊天过程中
  -> 更新内存态 threads / messages
  -> 写入 patient_threads:{patient_id} / patient_messages:{patient_id}

切换会话
  -> 先读当前患者的 patient_messages:{patient_id}
  -> 若本地无该线程，再调 /api/chat/history

401 / 登出
  -> 删除 patient_token / patient_current_user
  -> 删除 patient_user:{patient_id} / patient_threads:{patient_id} / patient_messages:{patient_id}
```

## 边界条件

### 1. 当前患者信息损坏

- 若 `patient_current_user` 无法解析或已过期，直接视为未登录
- 同时清理 `patient_token`，避免 UI 进入不一致状态

### 2. token 与 user 不一致

- 若 `patient_token` 与 `patient_current_user` 的 `patient_id` 不一致，优先判为脏数据
- 清空两者并要求重新登录

### 3. 同患者重复登录

- 若旧患者 ID 与新患者 ID 相同，则不清该患者自己的 `threads/messages`
- 仅刷新 `patient_token`、`patient_current_user`、`patient_user:{patient_id}` 的 TTL

### 4. 老旧缓存 JSON 解析失败

- 捕获异常后立即删除该 key
- 返回默认值，不阻塞页面渲染

## 测试与验证

### 1. 手工验证

至少覆盖以下场景：

1. 患者 A 登录并产生 1 条会话
2. 不退出，直接切换为患者 B 登录
3. 确认患者 B 看不到患者 A 的本地会话列表和消息
4. 刷新页面，确认患者 B 仍只恢复自己的缓存
5. 将缓存时间伪造为过期后刷新页面，确认本地缓存自动失效
6. 人为制造 `401`，确认 token、user、threads、messages 均被清理

### 2. 回归重点

- 登录成功后聊天是否仍能正常工作
- 切换会话是否仍能优先命中本地缓存
- 本地没有缓存时是否仍能正确从 `/api/chat/history` 拉取 Redis 历史
- 手动退出后是否仍能回到登录页

## 非目标

- 不支持同一浏览器同时保留多个患者的“活跃登录态”
- 不引入 IndexedDB 或其他持久化介质
- 不修改后端 Redis TTL 或登录态存储结构
- 不对已有聊天记录做跨 key 数据迁移

## 实施建议

建议按以下顺序实施：

1. 抽象统一的本地缓存读写与清理工具
2. 改造 `App.jsx` 的登录初始化、登录成功、登出、切换线程读写逻辑
3. 改造 `api/index.js` 的 `401` 清理逻辑
4. 做手工验证，重点验证“跨患者切换”和“1 天过期”
