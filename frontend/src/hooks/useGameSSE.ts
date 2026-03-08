import { useEffect, useRef } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import { getGameSSEUrl } from '../api/client'
import type { PuzzleSolvedEvent } from '../api/client'
import { getPuzzleSolvedNotificationText } from '../constants/puzzleMessages'

export interface GameSSEParams {
  gameId: string | null
  applyStartedState: (startedAt: string) => void
  syncGameStateFromServer: () => Promise<void>
  stopTimerAndSetGameOver: () => void
  setSolvedItemIds: Dispatch<SetStateAction<string[]>>
  setDoorVideoPlaying: (v: boolean) => void
  setPuzzleSolvedNotification: (text: string | null) => void
}

/**
 * SSE connection + recovery polling. Single responsibility: subscribe to game events, update state.
 */
export function useGameSSE(params: GameSSEParams): void {
  const {
    gameId,
    applyStartedState,
    syncGameStateFromServer,
    stopTimerAndSetGameOver,
    setSolvedItemIds,
    setDoorVideoPlaying,
    setPuzzleSolvedNotification,
  } = params

  const puzzleSolvedTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!gameId) return
    const url = getGameSSEUrl(gameId)
    const es = new EventSource(url)
    const sseRecoveryPollRef = { current: null as ReturnType<typeof setInterval> | null }

    const stopRecoveryPolling = () => {
      if (sseRecoveryPollRef.current) {
        clearInterval(sseRecoveryPollRef.current)
        sseRecoveryPollRef.current = null
      }
    }
    const startRecoveryPolling = () => {
      if (sseRecoveryPollRef.current) return
      sseRecoveryPollRef.current = setInterval(() => {
        syncGameStateFromServer().catch(() => {})
      }, 3000)
    }

    es.onopen = () => {
      stopRecoveryPolling()
      syncGameStateFromServer().catch(() => {})
    }

    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as {
          event?: string
          type?: string
          started_at?: string
          item_id?: string
          item_label?: string
          answer?: string
        }
        if (data.type === 'game_started' && data.started_at) {
          applyStartedState(data.started_at)
          return
        }
        if (data.type === 'game_over' || data.event === 'game_over') {
          stopTimerAndSetGameOver()
          return
        }
        if (data.event === 'door_opened') {
          setDoorVideoPlaying(true)
          return
        }
        if (data.event !== 'puzzle_solved') return
        const payload = data as PuzzleSolvedEvent
        setSolvedItemIds((prev) => (prev.includes(payload.item_id) ? prev : [...prev, payload.item_id]))
        const text = getPuzzleSolvedNotificationText(payload.item_id, payload.item_label, payload.answer)
        if (puzzleSolvedTimeoutRef.current) clearTimeout(puzzleSolvedTimeoutRef.current)
        setPuzzleSolvedNotification(text)
        puzzleSolvedTimeoutRef.current = setTimeout(() => setPuzzleSolvedNotification(null), 8000)
      } catch {
        // ignore
      }
    }

    es.onerror = () => {
      startRecoveryPolling()
    }

    return () => {
      stopRecoveryPolling()
      es.close()
      if (puzzleSolvedTimeoutRef.current) {
        clearTimeout(puzzleSolvedTimeoutRef.current)
        puzzleSolvedTimeoutRef.current = null
      }
    }
  }, [
    gameId,
    applyStartedState,
    syncGameStateFromServer,
    stopTimerAndSetGameOver,
    setSolvedItemIds,
    setDoorVideoPlaying,
    setPuzzleSolvedNotification,
  ])
}
