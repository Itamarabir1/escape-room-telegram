import { useCallback } from 'react'
import type { MutableRefObject } from 'react'
import { getGameState } from '../api/client'
import type { GameStateResponse } from '../api/client'
import { hasLoreAck } from '../utils/loreAck'

export interface GameStateSyncParams {
  gameId: string | null
  setRoom: (r: GameStateResponse | null) => void
  setSolvedItemIds: (ids: string[] | ((prev: string[]) => string[])) => void
  setDoorVideoPlaying: (v: boolean) => void
  setScienceLabImageLoaded: (v: boolean) => void
  setShowScienceLabRoom: (v: boolean) => void
  setGameStarted: (v: boolean) => void
  setStartedAtIso: (v: string | null) => void
  setTimerVisible: (v: boolean) => void
  setLoreNarrationActive: (v: boolean) => void
  setShowNarrationButton: (v: boolean) => void
  stopTimerAndSetGameOver: () => void
  startTimerFromServerTime: (startedAt: string) => void
  narrationInProgressRef: MutableRefObject<boolean>
}

/**
 * Applies server game state to local state. Single responsibility: sync from API (apply started, room, door, game over).
 */
export function useGameStateSync(params: GameStateSyncParams) {
  const {
    gameId,
    setRoom,
    setSolvedItemIds,
    setDoorVideoPlaying,
    setScienceLabImageLoaded,
    setShowScienceLabRoom,
    setGameStarted,
    setStartedAtIso,
    setTimerVisible,
    setLoreNarrationActive,
    setShowNarrationButton,
    stopTimerAndSetGameOver,
    startTimerFromServerTime,
    narrationInProgressRef,
  } = params

  const applyStartedState = useCallback(
    (startedAt: string) => {
      setGameStarted(true)
      setStartedAtIso(startedAt)
      startTimerFromServerTime(startedAt)
      if (narrationInProgressRef.current) {
        setTimerVisible(false)
        return
      }
      if (gameId && hasLoreAck(gameId, startedAt)) {
        setLoreNarrationActive(false)
        setShowNarrationButton(false)
        setTimerVisible(true)
      }
    },
    [
      gameId,
      startTimerFromServerTime,
      narrationInProgressRef,
      setTimerVisible,
      setLoreNarrationActive,
      setShowNarrationButton,
      setGameStarted,
      setStartedAtIso,
    ]
  )

  const applyGameStateFromServer = useCallback(
    (data: GameStateResponse) => {
      setRoom(data)
      setSolvedItemIds(data.solved_item_ids ?? [])
      if (data.door_opened) {
        setDoorVideoPlaying(false)
        setScienceLabImageLoaded(false)
        setShowScienceLabRoom(true)
      }
      if (data.started_at) {
        applyStartedState(data.started_at)
      }
      if (data.game_over) {
        stopTimerAndSetGameOver()
      }
    },
    [
      applyStartedState,
      stopTimerAndSetGameOver,
      setRoom,
      setSolvedItemIds,
      setDoorVideoPlaying,
      setScienceLabImageLoaded,
      setShowScienceLabRoom,
    ]
  )

  const waitForStart = useCallback(() => {
    const pollInterval = setInterval(async () => {
      if (!gameId) return
      try {
        const data = await getGameState(gameId)
        if (data.started_at) {
          clearInterval(pollInterval)
          applyGameStateFromServer(data)
        }
      } catch {
        // ignore
      }
    }, 3000)
    return () => clearInterval(pollInterval)
  }, [gameId, applyGameStateFromServer])

  const syncGameStateFromServer = useCallback(async () => {
    if (!gameId) return
    const data = await getGameState(gameId)
    applyGameStateFromServer(data)
  }, [gameId, applyGameStateFromServer])

  return {
    applyStartedState,
    applyGameStateFromServer,
    waitForStart,
    syncGameStateFromServer,
  }
}
