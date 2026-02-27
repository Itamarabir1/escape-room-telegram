import type { GameStateResponse, PuzzleResponse } from '../api/client'

export function getPuzzles(room: GameStateResponse | null): PuzzleResponse[] {
  if (!room) return []
  if (room.puzzles && room.puzzles.length > 0) return room.puzzles
  if (room.puzzle) return [{ ...room.puzzle, type: room.puzzle.type ?? 'unlock' }]
  return []
}

export function getPuzzleByItemId(
  room: GameStateResponse | null,
  itemId: string
): PuzzleResponse | undefined {
  return getPuzzles(room).find((p) => p.item_id === itemId)
}
