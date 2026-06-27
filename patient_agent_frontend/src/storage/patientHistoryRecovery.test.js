import { beforeEach, describe, expect, it, vi } from 'vitest'

import { loadPatientThreads, restorePatientThreads } from './patientCache.js'

describe('patient history recovery', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('restores thread list from remote and writes it back into patient scoped cache', async () => {
    const fetchThreads = vi.fn().mockResolvedValue([
      {
        thread_id: 'thread-1',
        title: '我想挂号心内科',
        last_message: '已为您找到今日可预约医生。',
        updated_at: '2026-06-27T14:00:00',
      },
    ])

    const recovered = await restorePatientThreads(1, fetchThreads)

    expect(fetchThreads).toHaveBeenCalledTimes(1)
    expect(recovered).toEqual([
      {
        id: 'thread-1',
        title: '我想挂号心内科',
        lastMessage: '已为您找到今日可预约医生。',
        time: '2026-06-27T14:00:00',
      },
    ])
    expect(loadPatientThreads(1)).toEqual(recovered)
  })

  it('uses local cache first and skips remote recovery', async () => {
    const fetchThreads = vi.fn().mockResolvedValue([])

    await restorePatientThreads(2, async () => [
      {
        thread_id: 'thread-a',
        title: '已缓存的会话',
        last_message: '缓存消息',
        updated_at: '2026-06-27T09:00:00',
      },
    ])

    const recovered = await restorePatientThreads(2, fetchThreads)

    expect(fetchThreads).not.toHaveBeenCalled()
    expect(recovered).toEqual([
      {
        id: 'thread-a',
        title: '已缓存的会话',
        lastMessage: '缓存消息',
        time: '2026-06-27T09:00:00',
      },
    ])
  })
})
