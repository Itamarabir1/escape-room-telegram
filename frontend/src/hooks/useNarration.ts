import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchLoreAudio } from '../api/client'
import type { GameStateResponse } from '../api/client'
import { hasLoreAck, persistLoreAck } from '../utils/loreAck'

/**
 * Plays lore audio (fetch blob → AudioContext or HTMLAudioElement or TTS fallback).
 */
function speakWithBrowserTTS(text: string, onEnd?: () => void): void {
  if (!text.trim()) {
    onEnd?.()
    return
  }
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    onEnd?.()
    return
  }
  const u = new SpeechSynthesisUtterance(text)
  u.lang = 'he-IL'
  u.rate = 0.95
  if (onEnd) u.onend = () => onEnd()
  u.onerror = () => onEnd?.()
  window.speechSynthesis.speak(u)
}

/**
 * Narration button + lore audio playback. Single responsibility: show "האזן לסיפור" once, play audio, persist ack.
 */
export function useNarration(
  gameId: string | null,
  gameStarted: boolean,
  startedAtIso: string | null,
  room: GameStateResponse | null,
  setTimerVisible: (v: boolean) => void
) {
  const [showNarrationButton, setShowNarrationButton] = useState(false)
  const [loreNarrationActive, setLoreNarrationActive] = useState(false)

  const lorePlayedRef = useRef(false)
  const narrationInProgressRef = useRef(false)
  const narrationUIShownForThisStartRef = useRef(false)

  const playLoreAudio = useCallback(
    (
      gid: string,
      loreTextForFallback?: string,
      onNarrationEnd?: () => void,
      audioContext?: AudioContext | null,
      audioElementForFallback?: HTMLAudioElement | null
    ) => {
      if (lorePlayedRef.current) {
        onNarrationEnd?.()
        return
      }
      lorePlayedRef.current = true
      const tryFallback = () => {
        if (loreTextForFallback?.trim()) {
          speakWithBrowserTTS(loreTextForFallback, onNarrationEnd)
        } else {
          onNarrationEnd?.()
        }
        lorePlayedRef.current = false
      }
      const playWithAudioElement = (blob: Blob, audioEl: HTMLAudioElement) => {
        const objectUrl = URL.createObjectURL(blob)
        const cleanup = () => URL.revokeObjectURL(objectUrl)
        const onEnded = () => {
          cleanup()
          onNarrationEnd?.()
        }
        const onPlayFailed = () => {
          cleanup()
          tryFallback()
        }
        if (audioEl.src && audioEl.src.startsWith('blob:')) URL.revokeObjectURL(audioEl.src)
        audioEl.src = objectUrl
        audioEl.load()
        audioEl.addEventListener('ended', onEnded)
        audioEl.addEventListener('error', onPlayFailed)
        audioEl.play().catch(onPlayFailed)
      }
      fetchLoreAudio(gid)
        .then((r) => (r.ok ? r.blob() : null))
        .then(async (blob) => {
          if (!blob) {
            tryFallback()
            return
          }
          if (audioContext && audioContext.state !== 'closed') {
            try {
              const arrayBuffer = await blob.arrayBuffer()
              const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
              const source = audioContext.createBufferSource()
              source.buffer = audioBuffer
              source.connect(audioContext.destination)
              source.onended = () => onNarrationEnd?.()
              source.start(0)
              return
            } catch {
              // fallback
            }
          }
          if (audioElementForFallback) {
            playWithAudioElement(blob, audioElementForFallback)
          } else {
            tryFallback()
          }
        })
        .catch(tryFallback)
    },
    []
  )

  const handleNarrationClick = useCallback(async () => {
    setShowNarrationButton(false)
    setLoreNarrationActive(true)
    narrationInProgressRef.current = true

    const SILENT_WAV =
      'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA='
    const unlockedAudioEl = new Audio(SILENT_WAV)
    unlockedAudioEl.play().catch(() => {})

    const situationText = room?.room_lore || room?.room_description || ''

    const onNarrationEnd = () => {
      narrationInProgressRef.current = false
      if (gameId && startedAtIso) persistLoreAck(gameId, startedAtIso)
      setLoreNarrationActive(false)
      setTimerVisible(true)
    }

    if (!situationText || !gameId) {
      onNarrationEnd()
      return
    }

    const AudioContextClass =
      typeof window !== 'undefined' &&
      (window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)
    if (AudioContextClass) {
      try {
        const ctx = new AudioContextClass()
        await ctx.resume()
        playLoreAudio(gameId, situationText, onNarrationEnd, ctx, unlockedAudioEl)
      } catch {
        playLoreAudio(gameId, situationText, onNarrationEnd, null, unlockedAudioEl)
      }
    } else {
      playLoreAudio(gameId, situationText, onNarrationEnd, null, unlockedAudioEl)
    }
  }, [gameId, startedAtIso, room?.room_lore, room?.room_description, playLoreAudio, setTimerVisible])

  useEffect(() => {
    if (!gameStarted || !startedAtIso || !gameId) return
    if (hasLoreAck(gameId, startedAtIso)) return
    if (narrationUIShownForThisStartRef.current) return
    narrationUIShownForThisStartRef.current = true
    setShowNarrationButton(true)
    setLoreNarrationActive(true)
    setTimerVisible(false)
  }, [gameStarted, startedAtIso, gameId, setTimerVisible])

  const resetForNewGame = useCallback(() => {
    setShowNarrationButton(false)
    setLoreNarrationActive(false)
    lorePlayedRef.current = false
    narrationUIShownForThisStartRef.current = false
  }, [])

  return {
    showNarrationButton,
    setShowNarrationButton,
    loreNarrationActive,
    setLoreNarrationActive,
    handleNarrationClick,
    narrationInProgressRef,
    resetForNewGame,
  }
}
