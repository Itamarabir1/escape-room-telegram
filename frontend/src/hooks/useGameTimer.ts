import { useCallback, useEffect, useRef, useState } from 'react'
import { reportTimeUp } from '../api/client'
import { INITIAL_TIMER_SECONDS } from '../constants/roomHotspots'

/**
 * Manages game countdown and game-over from timer.
 * Single responsibility: timer state + sync from server time + time-up reporting.
 */
export function useGameTimer(gameId: string | null) {
  const [secondsLeft, setSecondsLeft] = useState(INITIAL_TIMER_SECONDS)
  const [gameOver, setGameOver] = useState(false)
  const [timerVisible, setTimerVisible] = useState(false)

  const timerIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const timeUpSentRef = useRef(false)

  const stopTimerAndSetGameOver = useCallback(() => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current)
      timerIntervalRef.current = null
    }
    setGameOver(true)
  }, [])

  const handleTimeUp = useCallback(() => {
    stopTimerAndSetGameOver()
    if (gameId && !timeUpSentRef.current) {
      timeUpSentRef.current = true
      reportTimeUp(gameId).catch(() => {})
    }
  }, [gameId, stopTimerAndSetGameOver])

  const startTimerFromServerTime = useCallback(
    (startedAt: string) => {
      const elapsed = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)
      let remaining = Math.max(INITIAL_TIMER_SECONDS - elapsed, 0)
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current)
        timerIntervalRef.current = null
      }
      if (remaining === 0) {
        handleTimeUp()
        return
      }
      setSecondsLeft(remaining)
      timerIntervalRef.current = setInterval(() => {
        remaining -= 1
        setSecondsLeft(remaining)
        if (remaining <= 0 && timerIntervalRef.current) {
          clearInterval(timerIntervalRef.current)
          timerIntervalRef.current = null
          handleTimeUp()
        }
      }, 1000)
    },
    [handleTimeUp]
  )

  const clearTimer = useCallback(() => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current)
      timerIntervalRef.current = null
    }
  }, [])

  useEffect(() => {
    timeUpSentRef.current = false
  }, [gameId])

  return {
    secondsLeft,
    gameOver,
    setGameOver,
    timerVisible,
    setTimerVisible,
    stopTimerAndSetGameOver,
    handleTimeUp,
    startTimerFromServerTime,
    clearTimer,
  }
}
