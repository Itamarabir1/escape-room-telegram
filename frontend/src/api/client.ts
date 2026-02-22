/**
 * Game API client – single place for all frontend→backend calls.
 * Contract: matches backend app/api/games.py (prefix /api/games).
 */

const API_BASE = (import.meta.env.VITE_API_URL ?? '') + '/api/games'

function gameUrl(gameId: string): string {
  return API_BASE + '/' + encodeURIComponent(gameId)
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
  room_name?: string
  room_description?: string
  room_lore?: string
  room_items?: RoomItemResponse[]
  puzzle?: PuzzleResponse
  puzzles?: PuzzleResponse[]
}

/** Default room canvas size for placeholder (no image) */
export const DEMO_ROOM_WIDTH = 800
export const DEMO_ROOM_HEIGHT = 600

export interface ApiError {
  status: number
  detail?: string
}

/**
 * GET /api/games/{game_id}
 * Backend returns room with items + positions (no image by default; image can be static later).
 */
export async function getGameState(gameId: string): Promise<GameStateResponse> {
  const res = await fetch(gameUrl(gameId))
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload ?? {}),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw { status: res.status, detail: body?.detail ?? res.statusText } as ApiError
  }
  return res.json()
}

/**
 * GET /api/games/{game_id}/lore/audio – returns blob for Audio.
 */
export function getLoreAudioUrl(gameId: string): string {
  return gameUrl(gameId) + '/lore/audio'
}
