import '@testing-library/jest-dom/vitest'

function createMemoryStorage() {
  let store = {}
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null
    },
    setItem(key, value) {
      store[key] = String(value)
    },
    removeItem(key) {
      delete store[key]
    },
    clear() {
      store = {}
    },
  }
}

if (typeof window !== 'undefined' && typeof window.localStorage?.clear !== 'function') {
  const storage = createMemoryStorage()
  Object.defineProperty(globalThis, 'localStorage', {
    value: storage,
    configurable: true,
  })
  Object.defineProperty(window, 'localStorage', {
    value: storage,
    configurable: true,
  })
}

if (typeof window !== 'undefined' && typeof window.HTMLElement?.prototype?.scrollIntoView !== 'function') {
  window.HTMLElement.prototype.scrollIntoView = () => {}
}
