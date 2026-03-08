const LORE_ACK_STORAGE_PREFIX = 'lore_ack'

export function getLoreAckStorageKey(gameId: string, startedAt: string): string {
  return `${LORE_ACK_STORAGE_PREFIX}:${gameId}:${startedAt}`
}

export function hasLoreAck(gameId: string, startedAt: string): boolean {
  if (typeof window === 'undefined') return false
  try {
    return window.localStorage.getItem(getLoreAckStorageKey(gameId, startedAt)) === '1'
  } catch {
    return false
  }
}

export function persistLoreAck(gameId: string, startedAt: string): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(getLoreAckStorageKey(gameId, startedAt), '1')
  } catch {
    // ignore storage failures
  }
}
