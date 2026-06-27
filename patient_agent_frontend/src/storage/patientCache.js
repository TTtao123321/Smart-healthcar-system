export const CACHE_TTL_MS = 24 * 60 * 60 * 1000

export const STORAGE_KEYS = {
  TOKEN: 'patient_token',
  CURRENT_USER: 'patient_current_user',
  LEGACY_USER: 'patient_user',
  LEGACY_THREADS: 'patient_threads',
  LEGACY_MESSAGES: 'patient_messages',
}

const PREFIXES = {
  user: 'patient_user',
  threads: 'patient_threads',
  messages: 'patient_messages',
}

function now() {
  return Date.now()
}

function wrapValue(value, patientId) {
  return JSON.stringify({
    value,
    patient_id: patientId ?? null,
    expires_at: now() + CACHE_TTL_MS,
  })
}

export function patientScopedKey(kind, patientId) {
  return `${PREFIXES[kind]}:${patientId}`
}

export function removeKey(key) {
  localStorage.removeItem(key)
}

export function writeCache(key, value, patientId = null) {
  localStorage.setItem(key, wrapValue(value, patientId))
}

export function readCache(key, expectedPatientId = null, fallback = null) {
  const raw = localStorage.getItem(key)
  if (!raw) return fallback

  try {
    const parsed = JSON.parse(raw)
    if (!parsed?.expires_at || parsed.expires_at <= now()) {
      removeKey(key)
      return fallback
    }
    if (
      expectedPatientId !== null
      && expectedPatientId !== undefined
      && parsed.patient_id !== expectedPatientId
    ) {
      removeKey(key)
      return fallback
    }
    return parsed.value ?? fallback
  } catch {
    removeKey(key)
    return fallback
  }
}

export function purgeLegacyCacheKeys() {
  removeKey(STORAGE_KEYS.LEGACY_USER)
  removeKey(STORAGE_KEYS.LEGACY_THREADS)
  removeKey(STORAGE_KEYS.LEGACY_MESSAGES)
}

export function clearPatientScopedCache(patientId) {
  if (patientId === null || patientId === undefined || patientId === '') return

  removeKey(patientScopedKey('user', patientId))
  removeKey(patientScopedKey('threads', patientId))
  removeKey(patientScopedKey('messages', patientId))
}

export function loadCurrentUser() {
  return readCache(STORAGE_KEYS.CURRENT_USER, null, null)
}

export function loadCurrentToken() {
  return readCache(STORAGE_KEYS.TOKEN, null, null)
}

export function saveCurrentSession({ token, user }) {
  writeCache(STORAGE_KEYS.TOKEN, token, user.patient_id)
  writeCache(STORAGE_KEYS.CURRENT_USER, user, user.patient_id)
  writeCache(patientScopedKey('user', user.patient_id), user, user.patient_id)
}

export function replaceCurrentSession({ token, user }) {
  const previousUser = loadCurrentUser()
  if (previousUser && previousUser.patient_id !== user.patient_id) {
    clearPatientScopedCache(previousUser.patient_id)
  }
  saveCurrentSession({ token, user })
}

export function loadPatientThreads(patientId) {
  if (!patientId) return []
  return readCache(patientScopedKey('threads', patientId), patientId, [])
}

export function savePatientThreads(patientId, threads) {
  if (!patientId) return
  writeCache(patientScopedKey('threads', patientId), threads, patientId)
}

function normalizeRecoveredThread(thread) {
  return {
    id: thread.thread_id,
    title: thread.title || '新对话',
    lastMessage: thread.last_message || '',
    time: thread.updated_at || new Date().toISOString(),
  }
}

export async function restorePatientThreads(patientId, fetchThreads) {
  if (!patientId) return []

  const cachedThreads = loadPatientThreads(patientId)
  if (cachedThreads.length > 0) {
    return cachedThreads
  }

  const remoteThreads = await fetchThreads()
  const recoveredThreads = (remoteThreads || []).map(normalizeRecoveredThread)
  savePatientThreads(patientId, recoveredThreads)
  return recoveredThreads
}

export function loadPatientMessages(patientId) {
  if (!patientId) return {}
  return readCache(patientScopedKey('messages', patientId), patientId, {})
}

export function savePatientMessages(patientId, messages) {
  if (!patientId) return
  writeCache(patientScopedKey('messages', patientId), messages, patientId)
}

export function clearCurrentSessionCache() {
  const currentUser = loadCurrentUser()

  removeKey(STORAGE_KEYS.TOKEN)
  removeKey(STORAGE_KEYS.CURRENT_USER)
  clearPatientScopedCache(currentUser?.patient_id ?? null)
}
