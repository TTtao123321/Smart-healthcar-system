import { beforeEach, describe, expect, it } from 'vitest'
import {
  CACHE_TTL_MS,
  STORAGE_KEYS,
  clearCurrentSessionCache,
  loadCurrentUser,
  patientScopedKey,
  purgeLegacyCacheKeys,
  readCache,
  replaceCurrentSession,
  saveCurrentSession,
  writeCache,
} from './patientCache.js'

describe('patientCache', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns fallback and deletes expired cache entries', () => {
    localStorage.setItem(
      'patient_threads:1',
      JSON.stringify({
        value: [{ id: 'thread-1' }],
        patient_id: 1,
        expires_at: Date.now() - 1,
      })
    )

    expect(readCache('patient_threads:1', 1, [])).toEqual([])
    expect(localStorage.getItem('patient_threads:1')).toBeNull()
  })

  it('isolates scoped cache by patient id', () => {
    writeCache(patientScopedKey('messages', 1), { 'thread-1': [{ text: 'A' }] }, 1)

    expect(readCache(patientScopedKey('messages', 1), 1, {})).toEqual({
      'thread-1': [{ text: 'A' }],
    })
    expect(readCache(patientScopedKey('messages', 1), 2, {})).toEqual({})
  })

  it('persists current session with the same ttl envelope', () => {
    saveCurrentSession({
      token: 'token-1',
      user: { name: '张三', token: 'token-1', patient_id: 1, phone: '13800138001' },
    })

    expect(loadCurrentUser()).toMatchObject({ patient_id: 1, name: '张三' })
    const tokenEnvelope = JSON.parse(localStorage.getItem(STORAGE_KEYS.TOKEN))
    expect(tokenEnvelope.patient_id).toBe(1)
    expect(tokenEnvelope.expires_at - Date.now()).toBeLessThanOrEqual(CACHE_TTL_MS)
  })

  it('removes all session and scoped keys for the current patient', () => {
    saveCurrentSession({
      token: 'token-1',
      user: { name: '张三', token: 'token-1', patient_id: 1, phone: '13800138001' },
    })
    writeCache(patientScopedKey('threads', 1), [{ id: 'thread-1' }], 1)
    writeCache(patientScopedKey('messages', 1), { 'thread-1': [{ text: 'A' }] }, 1)

    clearCurrentSessionCache()

    expect(localStorage.getItem(STORAGE_KEYS.TOKEN)).toBeNull()
    expect(localStorage.getItem(STORAGE_KEYS.CURRENT_USER)).toBeNull()
    expect(localStorage.getItem(patientScopedKey('threads', 1))).toBeNull()
    expect(localStorage.getItem(patientScopedKey('messages', 1))).toBeNull()
  })

  it('purges legacy shared keys without migrating them', () => {
    localStorage.setItem(STORAGE_KEYS.LEGACY_USER, '{}')
    localStorage.setItem(STORAGE_KEYS.LEGACY_THREADS, '[]')
    localStorage.setItem(STORAGE_KEYS.LEGACY_MESSAGES, '{}')

    purgeLegacyCacheKeys()

    expect(localStorage.getItem(STORAGE_KEYS.LEGACY_USER)).toBeNull()
    expect(localStorage.getItem(STORAGE_KEYS.LEGACY_THREADS)).toBeNull()
    expect(localStorage.getItem(STORAGE_KEYS.LEGACY_MESSAGES)).toBeNull()
  })

  it('clears previous patient cache when a different patient logs in', () => {
    saveCurrentSession({
      token: 'token-a',
      user: { name: '张三', token: 'token-a', patient_id: 1, phone: '13800138001' },
    })
    writeCache(patientScopedKey('threads', 1), [{ id: 'thread-a' }], 1)
    writeCache(patientScopedKey('messages', 1), { 'thread-a': [{ text: '旧消息' }] }, 1)

    replaceCurrentSession({
      token: 'token-b',
      user: { name: '李四', token: 'token-b', patient_id: 2, phone: '13900139000' },
    })

    expect(localStorage.getItem(patientScopedKey('threads', 1))).toBeNull()
    expect(localStorage.getItem(patientScopedKey('messages', 1))).toBeNull()
    expect(loadCurrentUser()).toMatchObject({ patient_id: 2, name: '李四' })
  })
})
