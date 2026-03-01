/**
 * Game API client – single place for all frontend→backend calls.
 * Contract: matches backend app/api/games.py (prefix /api/games).
 * All requests use absolute API URL so the static server never intercepts them.
 */

const API_BASE_URL_FALLBACK = 'https://escape-room-telegram-api.onrender.com' // Must match backend in production; override with VITE_API_URL.

function getApiBase(): string {
  const raw = import.meta.env.VITE_API_URL || API_BASE_URL_FALLBACK
  const base = typeof raw === 'string' ? String(raw).trim().replace(/\/+$/, '') : API_BASE_URL_FALLBACK
  return base || API_BASE_URL_FALLBACK
}

/** Base URL for room/media assets served by the API (e.g. /room/escape_room.png). Use for img/video src. */
export function getRoomMediaUrl(path: string): string {
  const p = path.replace(/^\/+/, '')
  return getApiBase() + '/room/' + p
}

/**
 * Resolve room image URL for display. If backend sent a frontend-relative URL or same-origin URL,
 * use the API media URL instead so the image is always loaded from the API.
 */
export function getEffectiveRoomImageUrl(roomImageUrl: string | undefined): string {
  const apiUrl = getRoomMediaUrl('escape_room.png')
  if (!roomImageUrl) return apiUrl
  if (roomImageUrl.startsWith('/')) return apiUrl
  try {
    if (typeof window !== 'undefined' && new URL(roomImageUrl).origin === window.location.origin)
      return apiUrl
  } catch {
    return apiUrl
  }
  return roomImageUrl
}

function apiBaseUrl(): string {
  return getApiBase() + '/api/games'
}

const API_BASE = apiBaseUrl()

function gameUrl(gameId: string): string {
  return API_BASE + '/' + encodeURIComponent(gameId)
}

/** Telegram Web App initData – required for game API (only registered players can access). */
function getInitData(): string {
  if (typeof window === 'undefined') return ''
  const data = (window as unknown as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData
  return data ?? ''
}

function gameHeaders(extra: HeadersInit = {}): HeadersInit {
  const init = getInitData()
  return {
    ...(init ? { 'X-Telegram-Init-Data': init } : {}),
    ...extra,
  }
}

export interface RoomItemResponse {
  id: string
  label: string
  x: number
  y: number
  action_type: string
}

export interface PuzzleResponse {
  item_id: string
  type: 'unlock' | 'examine'
  backstory: string
  encoded_clue?: string
  prompt_text?: string
}

export interface GameStateResponse {
  game_id: string
  players: Record<string, string>
  game_active: boolean
  room_image_url?: string
  room_image_width?: number
  room_image_height?: number
  room_name?: string
  room_description?: string
  room_lore?: string
  room_items?: RoomItemResponse[]
  puzzle?: PuzzleResponse
  puzzles?: PuzzleResponse[]
  /** item_ids with solved status in DB (per group) */
  solved_item_ids?: string[]
  /** ISO timestamp when first user clicked "התחל"; used for timer and rejoin */
  started_at?: string
  /** True when door animation was already triggered; used to resume in second room. */
  door_opened?: boolean
}

/** Room canvas size – larger than screen so user scrolls left/right (panorama) */
export const DEMO_ROOM_WIDTH = 1600
export const DEMO_ROOM_HEIGHT = 1200

export interface ApiError {
  status: number
  detail?: string
}

/**
 * GET /api/games/{game_id}
 * Backend returns room with items + positions (no image by default; image can be static later).
 */
export async function getGameState(gameId: string): Promise<GameStateResponse> {
  const res = await fetch(gameUrl(gameId), { headers: gameHeaders() })
  if (res.ok) return res.json()
  let detail: string
  try {
    const body = await res.json()
    detail = body?.detail ?? res.statusText
  } catch {
    detail = res.statusText
  }
  throw { status: res.status, detail } as ApiError
}

export interface ActionResponse {
  ok: boolean
  game_id: string
  correct?: boolean
  message?: string
}

/**
 * POST /api/games/{game_id}/action – e.g. { item_id, answer } for safe puzzle
 */
export async function sendGameAction(
  gameId: string,
  payload: object
): Promise<ActionResponse> {
  const res = await fetch(gameUrl(gameId) + '/action', {
    method: 'POST',
    headers: gameHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload ?? {}),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw { status: res.status, detail: body?.detail ?? res.statusText } as ApiError
  }
  return res.json()
}

/**
 * GET /api/games/{game_id}/lore/audio – returns blob for Audio. Requires initData header (registered players only).
 */
export function getLoreAudioUrl(gameId: string): string {
  return gameUrl(gameId) + '/lore/audio'
}

/** Fetch lore audio with initData header (for playback in GamePage). */
export function fetchLoreAudio(gameId: string): Promise<Response> {
  return fetch(getLoreAudioUrl(gameId), { headers: gameHeaders() })
}

/**
 * POST /api/games/{game_id}/time_up – notify backend that timer reached 0. Ends game and notifies group.
 */
export async function reportTimeUp(gameId: string): Promise<{ ok: boolean; message: string }> {
  const res = await fetch(gameUrl(gameId) + '/time_up', { method: 'POST', headers: gameHeaders() })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw { status: res.status, detail: body?.detail ?? res.statusText } as ApiError
  }
  return res.json()
}

/**
 * POST /api/games/{game_id}/start – record that the game has started (first "התחל" click). Enables rejoin with correct timer.
 */
export async function startGame(gameId: string): Promise<{ ok: boolean }> {
  const res = await fetch(gameUrl(gameId) + '/start', { method: 'POST', headers: gameHeaders() })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw { status: res.status, detail: body?.detail ?? res.statusText } as ApiError
  }
  return res.json()
}

/**
 * POST /api/games/{game_id}/door_opened – notify that door was clicked (all puzzles solved). Backend broadcasts door_opened so all clients play the animation together.
 */
export async function notifyDoorOpened(gameId: string): Promise<{ ok: boolean }> {
  const res = await fetch(gameUrl(gameId) + '/door_opened', { method: 'POST', headers: gameHeaders() })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw { status: res.status, detail: body?.detail ?? res.statusText } as ApiError
  }
  return res.json()
}

/** Base URL for API (no path). Used to derive WebSocket URL. Never uses window.location so it never points to frontend. */
function apiBaseOrigin(): string {
  const base = getApiBase()
  try {
    return new URL(base).origin
  } catch {
    return API_BASE_URL_FALLBACK
  }
}

/**
 * WebSocket URL for real-time game events (e.g. puzzle_solved).
 * ws:// in dev, wss:// when origin is https.
 */
export function getGameWebSocketUrl(gameId: string): string {
  const origin = apiBaseOrigin()
  const wsScheme = origin.startsWith('https') ? 'wss' : 'ws'
  const host = origin.replace(/^https?:\/\//, '')
  const init = getInitData()
  const path = `/ws/games/${encodeURIComponent(gameId)}`
  const query = init ? `?init_data=${encodeURIComponent(init)}` : ''
  return `${wsScheme}://${host}${path}${query}`
}

export interface PuzzleSolvedEvent {
  event: 'puzzle_solved'
  item_id: string
  item_label: string
  answer: string
  solver_name?: string
}

export interface GameOverEvent {
  event: 'game_over'
}

export interface DoorOpenedEvent {
  event: 'door_opened'
}
