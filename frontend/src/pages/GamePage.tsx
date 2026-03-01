import { useCallback, useEffect, useRef, useState } from 'react'
import type { DependencyList, RefObject } from 'react'
import {
  getGameState,
  getGameWebSocketUrl,
  fetchLoreAudio,
  notifyDoorOpened,
  reportTimeUp,
  sendGameAction,
  startGame,
  type ApiError,
  type GameStateResponse,
  type PuzzleSolvedEvent,
  type RoomItemResponse,
} from '../api/client'
import { MESSAGES } from '../constants/messages'
import { INITIAL_TIMER_SECONDS } from '../constants/roomHotspots'
import { getPuzzleByItemId, getPuzzles } from '../utils/gameHelpers'
import { Banners } from '../components/Banners'
import { DoorVideoOverlay } from '../components/DoorVideoOverlay'
import { RoomView } from '../components/RoomView'
import { ScienceLabRoom } from '../components/ScienceLabRoom'
import { StartUI } from '../components/StartUI'
import { TaskModal } from '../components/TaskModal'
import '../index.css'

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        version?: string
        ready?: () => void | Promise<void>
        expand?: () => void
        initDataUnsafe?: { user?: { first_name?: string }; start_param?: string }
        sendData?: (data: string) => void
        BackButton?: {
          show: () => void
          hide: () => void
          onClick: (callback: () => void) => void
          offClick: (callback: () => void) => void
        }
        onEvent?: (eventType: string, callback: () => void) => void
        offEvent?: (eventType: string, callback: () => void) => void
      }
    }
  }
}

function getTelegramWebApp() {
  return window.Telegram?.WebApp ?? {}
}

function useCenterScrollOnLoad(
  ref: RefObject<HTMLDivElement | null>,
  active: boolean,
  deps: DependencyList
) {
  useEffect(() => {
    if (!active) return
    const run = () => {
      const el = ref.current
      if (!el) return
      const maxScroll = el.scrollWidth - el.clientWidth
      el.scrollLeft = maxScroll > 0 ? maxScroll / 2 : 0
    }
    run()
    requestAnimationFrame(() => requestAnimationFrame(run))
    const t1 = setTimeout(run, 100)
    const t2 = setTimeout(run, 400)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [active, ref, ...deps])
}

export default function GamePage() {
  const [gameId, setGameId] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('')
  const [statusError, setStatusError] = useState(false)
  const [roomLoading, setRoomLoading] = useState(false)
  const [room, setRoom] = useState<GameStateResponse | null>(null)
  const [taskModalOpen, setTaskModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<RoomItemResponse | null>(null)
  const [unlockAnswer, setUnlockAnswer] = useState('')
  const [actionMessage, setActionMessage] = useState<{ text: string; isSuccess: boolean } | null>(null)
  const [actionSubmitting, setActionSubmitting] = useState(false)
  const [puzzleSolvedNotification, setPuzzleSolvedNotification] = useState<string | null>(null)
  const [secondsLeft, setSecondsLeft] = useState(INITIAL_TIMER_SECONDS)
  const [gameOver, setGameOver] = useState(false)
  const [gameStarted, setGameStarted] = useState(false)
  const [startUIVisible, setStartUIVisible] = useState(true)
  const [loreNarrationActive, setLoreNarrationActive] = useState(false)
  const panoramaRef = useRef<HTMLDivElement>(null)
  const scienceLabPanoramaRef = useRef<HTMLDivElement>(null)
  const [roomImageLoaded, setRoomImageLoaded] = useState(false)
  const [solvedItemIds, setSolvedItemIds] = useState<string[]>([])
  const [doorVideoPlaying, setDoorVideoPlaying] = useState(false)
  const [showScienceLabRoom, setShowScienceLabRoom] = useState(false)
  const [scienceLabImageLoaded, setScienceLabImageLoaded] = useState(false)
  const [doorLockedMessage, setDoorLockedMessage] = useState(false)
  const [blockedItemMessage, setBlockedItemMessage] = useState<string | null>(null)
  const lorePlayedRef = useRef(false)

  const timerIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const timeUpSentRef = useRef(false)
  const modalTTSRef = useRef<SpeechSynthesisUtterance | null>(null)
  const doorVideoRef = useRef<HTMLVideoElement | null>(null)
  const closeModalRef = useRef<() => void>(() => {})

  const tg = getTelegramWebApp()
  if (tg.expand) tg.expand()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const fromUrl = params.get('game_id')
    if (fromUrl) {
      setGameId(fromUrl)
      return
    }
    const fromStartParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param
    if (fromStartParam) setGameId(fromStartParam)
  }, [])

  const showStatus = useCallback((text: string, isError: boolean) => {
    setStatus(text)
    setStatusError(isError)
  }, [])

  const handleTimeUp = useCallback(() => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current)
      timerIntervalRef.current = null
    }
    setGameOver(true)
    if (gameId && !timeUpSentRef.current) {
      timeUpSentRef.current = true
      reportTimeUp(gameId).catch(() => {})
    }
  }, [gameId])

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

  const speakWithBrowserTTS = useCallback((text: string, onEnd?: () => void) => {
    if (!text.trim()) {
      console.log('[audio] speakWithBrowserTTS: no text, calling onEnd')
      onEnd?.()
      return
    }
    if (!window.speechSynthesis) {
      console.warn('[audio] speakWithBrowserTTS: speechSynthesis not available')
      onEnd?.()
      return
    }
    console.log('[audio] speakWithBrowserTTS: starting, text length=', text.length)
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'he-IL'
    u.rate = 0.95
    if (onEnd) u.onend = () => { console.log('[audio] speakWithBrowserTTS: ended'); onEnd() }
    u.onerror = (e) => { console.warn('[audio] speakWithBrowserTTS: error', e); onEnd?.() }
    window.speechSynthesis.speak(u)
  }, [])

  const playLoreAudio = useCallback(
    (gid: string, loreTextForFallback?: string, onNarrationEnd?: () => void, audioContext?: AudioContext | null, audioElementForFallback?: HTMLAudioElement | null) => {
      if (lorePlayedRef.current) {
        console.log('[audio] playLoreAudio: already played this session, skip')
        onNarrationEnd?.()
        return
      }
      lorePlayedRef.current = true
      console.log('[audio] playLoreAudio: fetch lore/audio for', gid)
      const tryFallback = () => {
        console.log('[audio] playLoreAudio: using browser TTS fallback, hasText=', !!loreTextForFallback?.trim())
        if (loreTextForFallback?.trim()) {
          speakWithBrowserTTS(loreTextForFallback, onNarrationEnd)
        } else {
          console.log('[audio] playLoreAudio: no fallback text, calling onNarrationEnd')
          onNarrationEnd?.()
        }
        lorePlayedRef.current = false
      }
      const playWithAudioElement = (blob: Blob, audioEl: HTMLAudioElement) => {
        const objectUrl = URL.createObjectURL(blob)
        const cleanup = () => URL.revokeObjectURL(objectUrl)
        const onEnded = () => {
          console.log('[audio] playLoreAudio: playback ended')
          cleanup()
          onNarrationEnd?.()
        }
        const onPlayFailed = (err: unknown) => {
          console.warn('[audio] playLoreAudio: play() failed:', err)
          cleanup()
          tryFallback()
        }
        const onError = () => onPlayFailed(null)
        if (audioEl.src && audioEl.src.startsWith('blob:')) URL.revokeObjectURL(audioEl.src)
        audioEl.src = objectUrl
        audioEl.load()
        audioEl.removeEventListener('ended', onEnded)
        audioEl.removeEventListener('error', onError)
        audioEl.addEventListener('ended', onEnded)
        audioEl.addEventListener('error', onError)
        audioEl.play()
          .then(() => console.log('[audio] playLoreAudio: play() started'))
          .catch(onPlayFailed)
      }
      fetchLoreAudio(gid)
        .then((r) => {
          console.log('[audio] playLoreAudio: response status=', r.status, r.statusText)
          return r.ok ? r.blob() : null
        })
        .then(async (blob) => {
          if (!blob) {
            console.warn('[audio] playLoreAudio: no blob (backend error or 404/503), fallback')
            tryFallback()
            return
          }
          console.log('[audio] playLoreAudio: got blob size=', blob.size)
          if (audioContext && audioContext.state !== 'closed') {
            try {
              const arrayBuffer = await blob.arrayBuffer()
              const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
              const source = audioContext.createBufferSource()
              source.buffer = audioBuffer
              source.connect(audioContext.destination)
              source.onended = () => {
                console.log('[audio] playLoreAudio: Web Audio playback ended')
                onNarrationEnd?.()
              }
              source.start(0)
              console.log('[audio] playLoreAudio: Web Audio play() started')
              return
            } catch (e) {
              console.warn('[audio] playLoreAudio: Web Audio failed, fallback to Audio element:', e)
            }
          }
          if (audioElementForFallback) {
            playWithAudioElement(blob, audioElementForFallback)
          } else {
            tryFallback()
          }
        })
        .catch((err) => {
          console.warn('[audio] playLoreAudio: fetch failed (network/CORS):', err)
          tryFallback()
        })
    },
    [speakWithBrowserTTS]
  )

  useEffect(() => {
    if (!gameId) {
      showStatus(MESSAGES.START_IN_GROUP, false)
      return
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current)
      timerIntervalRef.current = null
    }
    setRoomLoading(true)
    setRoomImageLoaded(false)
    setSolvedItemIds([])
    setGameStarted(false)
    setStartUIVisible(true)
    setLoreNarrationActive(false)
    lorePlayedRef.current = false
    getGameState(gameId)
      .then((data) => {
        setRoomLoading(false)
        showStatus('', false)
        setRoom(data)
        setSolvedItemIds(data.solved_item_ids ?? [])
        // If the door was already opened in this game (persisted on backend),
        // resume directly in the second room (science lab) without replaying the video.
        if (data.door_opened) {
          setDoorVideoPlaying(false)
          setScienceLabImageLoaded(false)
          setShowScienceLabRoom(true)
        }
        if (data.started_at) {
          setGameStarted(true)
          setStartUIVisible(false)
          startTimerFromServerTime(data.started_at)
        }
      })
      .catch((e: ApiError) => {
        setRoomLoading(false)
        setRoom(null)
        const msg = e?.detail ?? (e?.status === 404 ? MESSAGES.GAME_NOT_FOUND : MESSAGES.LOAD_ERROR)
        showStatus(msg, true)
      })
  }, [gameId, showStatus, startTimerFromServerTime])

  const hasRoomImage = !!(room?.room_image_url && (room?.room_items?.length ?? 0) > 0)
  useEffect(() => {
    if (!roomLoading && hasRoomImage) document.body.classList.add('game-has-room')
    return () => document.body.classList.remove('game-has-room')
  }, [roomLoading, hasRoomImage])

  const showTimer = (room?.room_items?.length ?? 0) > 0 && !roomLoading && gameStarted

  useEffect(() => {
    timeUpSentRef.current = false
  }, [gameId])

  const onStartClick = useCallback(async () => {
    if (gameId) {
      startGame(gameId)
        .then((res) => {
          if (res.started_at) {
            startTimerFromServerTime(res.started_at)
            setGameStarted(true)
            setStartUIVisible(false)
          }
        })
        .catch(() => {})
    }
    const SILENT_WAV = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA='
    const unlockedAudioEl = new Audio(SILENT_WAV)
    unlockedAudioEl.play().catch(() => {})

    const situationText = room?.room_lore || room?.room_description || ''
    console.log('[audio] onStartClick: gameId=', gameId, 'situationText length=', situationText.length)
    const onNarrationEnd = () => {
      console.log('[audio] onStartClick: narration ended')
      setLoreNarrationActive(false)
    }
    setLoreNarrationActive(true)
    if (!gameId || !situationText) {
      console.log('[audio] onStartClick: no gameId or situationText, hiding button immediately')
      onNarrationEnd()
      return
    }
    let ctx: AudioContext | null = null
    const AudioContextClass = typeof window !== 'undefined' && (window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)
    if (AudioContextClass) {
      try {
        ctx = new AudioContextClass()
        await ctx.resume()
        console.log('[audio] onStartClick: AudioContext resumed, state=', ctx.state)
      } catch (e) {
        console.warn('[audio] onStartClick: AudioContext resume failed', e)
        ctx = null
      }
    }
    playLoreAudio(gameId, situationText, onNarrationEnd, ctx, unlockedAudioEl)
  }, [gameId, room?.room_lore, room?.room_description, playLoreAudio, startTimerFromServerTime])

  const puzzleSolvedTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(() => {
    if (!gameId || !room) return
    const url = getGameWebSocketUrl(gameId)
    const ws = new WebSocket(url)
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as {
          event?: string
          type?: string
          started_at?: string
          reason?: string
          item_id?: string
          item_label?: string
          answer?: string
          solver_name?: string
        }
        if (data.type === 'game_started' && data.started_at) {
          startTimerFromServerTime(data.started_at)
          setGameStarted(true)
          setStartUIVisible(false)
          return
        }
        if (data.type === 'game_over' || data.event === 'game_over') {
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current)
            timerIntervalRef.current = null
          }
          setGameOver(true)
          return
        }
        if (data.event === 'door_opened') {
          setDoorVideoPlaying(true)
          return
        }
        if (data.event !== 'puzzle_solved') return
        const payload = data as PuzzleSolvedEvent
        setSolvedItemIds((prev) => (prev.includes(payload.item_id) ? prev : [...prev, payload.item_id]))
        const text =
          payload.item_id === 'clock_1'
            ? 'השעון כוון בהצלחה'
            : payload.item_id === 'board_servers'
              ? 'לוח הבקרה נפתח בהצלחה'
              : payload.item_id === 'safe_1'
                ? 'הכספת נפתחה בהצלחה בתוכה יש מפתח'
                : `חידת ${payload.item_label} נפתרה הפתרון הוא ${payload.answer}`
        if (puzzleSolvedTimeoutRef.current) clearTimeout(puzzleSolvedTimeoutRef.current)
        setPuzzleSolvedNotification(text)
        puzzleSolvedTimeoutRef.current = setTimeout(() => setPuzzleSolvedNotification(null), 8000)
      } catch {
        // ignore non-JSON or unknown shape
      }
    }
    return () => {
      ws.close()
      if (puzzleSolvedTimeoutRef.current) {
        clearTimeout(puzzleSolvedTimeoutRef.current)
        puzzleSolvedTimeoutRef.current = null
      }
    }
  }, [gameId, room, startTimerFromServerTime])

  const onRoomImageLoad = useCallback(() => {
    setRoomImageLoaded(true)
  }, [])

  const onRoomImageError = useCallback(() => {
    setRoomImageLoaded(true)
  }, [])

  useCenterScrollOnLoad(panoramaRef, hasRoomImage && roomImageLoaded, [
    room?.room_image_url,
    room?.room_items?.length,
    roomImageLoaded,
  ])
  useCenterScrollOnLoad(scienceLabPanoramaRef, showScienceLabRoom && scienceLabImageLoaded, [
    showScienceLabRoom,
    scienceLabImageLoaded,
  ])

  const unlockItemIds = (room && getPuzzles(room).filter((p) => p.type === 'unlock').map((p) => p.item_id)) ?? []
  const allPuzzlesSolved = unlockItemIds.length > 0 && unlockItemIds.every((id) => solvedItemIds.includes(id))

  const openTask = useCallback((item: RoomItemResponse) => {
    setSelectedItem(item)
    setTaskModalOpen(true)
    setUnlockAnswer('')
    setActionMessage(null)
  }, [])

  const closeModalState = useCallback(() => {
    window.speechSynthesis.cancel()
    modalTTSRef.current = null
    setTaskModalOpen(false)
    setSelectedItem(null)
    setUnlockAnswer('')
    setActionMessage(null)
  }, [])

  const closeTaskModal = useCallback((e?: React.MouseEvent | React.PointerEvent) => {
    e?.preventDefault()
    e?.stopPropagation()
    closeModalState()
  }, [closeModalState])

  const handleCloseModal = useCallback(() => {
    const synth = window.speechSynthesis
    if (synth && document.hasFocus?.() && (synth.speaking || synth.pending)) {
      synth.cancel()
    }
    closeModalState()
  }, [closeModalState])
  closeModalRef.current = handleCloseModal

  /** Telegram BackButton: when modal is open, show header back button; on press, close modal.
   * Skip on clients where BackButton is not supported (e.g. WebApp version 6.0), to avoid
   * overlay/conflict with the in-modal "סגור" button. */
  useEffect(() => {
    const backBtn = window.Telegram?.WebApp?.BackButton
    const version = window.Telegram?.WebApp?.version ?? ''
    const backButtonUnsupported = version.startsWith('6.0')
    if (!backBtn || backButtonUnsupported) return
    if (!taskModalOpen) {
      try {
        backBtn.hide()
      } catch {
        // BackButton not supported on this client
      }
      return
    }
    const onBack = () => {
      closeModalRef.current?.()
      try {
        backBtn.hide()
        backBtn.offClick(onBack)
      } catch {
        // ignore
      }
    }
    try {
      backBtn.onClick(onBack)
      backBtn.show()
    } catch {
      return
    }
    return () => {
      try {
        backBtn.hide()
        backBtn.offClick(onBack)
      } catch {
        // ignore
      }
    }
  }, [taskModalOpen])

  const submitUnlockAnswer = useCallback(() => {
    if (!gameId || !selectedItem) return
    const puzzle = getPuzzleByItemId(room, selectedItem.id)
    if (!puzzle || puzzle.type !== 'unlock' || !unlockAnswer.trim()) return
    setActionSubmitting(true)
    setActionMessage(null)
    const solverName = getTelegramWebApp().initDataUnsafe?.user?.first_name ?? undefined
    sendGameAction(gameId, {
      item_id: selectedItem.id,
      answer: unlockAnswer.trim(),
      ...(solverName ? { solver_name: solverName } : {}),
    })
      .then((res) => {
        const successText =
          selectedItem?.id === 'board_servers'
            ? 'לוח הבקרה נפתח!'
            : selectedItem?.id === 'safe_1'
              ? 'הכספת נפתחה!'
              : res.message ?? 'נפתר בהצלחה!'
        setActionMessage({
          text: res.message ?? (res.correct ? successText : 'סיסמה שגויה.'),
          isSuccess: !!res.correct,
        })
        if (res.correct) {
          if (selectedItem) setSolvedItemIds((prev) => (prev.includes(selectedItem.id) ? prev : [...prev, selectedItem.id]))
          setTimeout(closeTaskModal, 2000)
        }
      })
      .catch((e: ApiError) => {
        setActionMessage({ text: e?.detail ?? 'שגיאה בשליחת התשובה.', isSuccess: false })
      })
      .finally(() => setActionSubmitting(false))
  }, [gameId, room, selectedItem, unlockAnswer, closeTaskModal])

  const showRoomSection = (room?.room_items?.length ?? 0) > 0
  const roomItems = room?.room_items ?? []
  const selectedPuzzle = selectedItem ? getPuzzleByItemId(room, selectedItem.id) : null
  const hasImage = Boolean(room?.room_image_url)
  const situationText = room?.room_lore || room?.room_description || ''
  const roomReady = !roomLoading && (hasImage ? roomImageLoaded : true)
  const showLoadingOverlay = showRoomSection || roomLoading

  const handleHotspotClick = useCallback(
    (params: {
      item: RoomItemResponse
      shapeItemId: string
      allPuzzlesSolved: boolean
      solvedItemIds: string[]
    }) => {
      const { item, shapeItemId, allPuzzlesSolved: allSolved, solvedItemIds: solved } = params
      if (!gameStarted) return
      if (shapeItemId === 'door') {
        if (!allSolved) {
          setDoorLockedMessage(true)
          setTimeout(() => setDoorLockedMessage(false), 4000)
          return
        }
        setDoorVideoPlaying(true)
        if (gameId) notifyDoorOpened(gameId).catch(() => {})
        return
      }
      if (shapeItemId === 'board_servers' && !solved.includes('clock_1')) {
        setBlockedItemMessage('כוונו את השעון כדי לפתוח את לוח הבקרה.')
        setTimeout(() => setBlockedItemMessage(null), 4000)
        return
      }
      openTask(item)
    },
    [gameStarted, gameId, openTask]
  )

  const handleDoorVideoEnded = useCallback(() => {
    const transitionAfterEnd = () => {
      setDoorVideoPlaying(false)
      setScienceLabImageLoaded(false)
      setShowScienceLabRoom(true)
    }
    setTimeout(transitionAfterEnd, 450)
  }, [])

  const handleDoorVideoError = useCallback(() => {
    setDoorVideoPlaying(false)
    setScienceLabImageLoaded(false)
    setShowScienceLabRoom(true)
  }, [])

  return (
    <div className="game-container">
      {showLoadingOverlay && (
        <div
          className={`room-loading-overlay ${roomReady ? 'room-loading-overlay--hidden' : ''}`}
          aria-hidden={roomReady}
          aria-live="polite"
        >
          <div className="room-loading-spinner" aria-hidden />
          <p className="room-loading-overlay-text">טוען…</p>
        </div>
      )}
      <Banners
        showTimer={showTimer}
        gameOver={gameOver}
        secondsLeft={secondsLeft}
        puzzleSolvedNotification={puzzleSolvedNotification}
        doorLockedMessage={doorLockedMessage}
        blockedItemMessage={blockedItemMessage}
        status={status}
        statusError={statusError}
      />
      {showRoomSection && roomReady && startUIVisible && (
        <StartUI
          situationText={situationText}
          loreNarrationActive={loreNarrationActive}
          onStartClick={onStartClick}
        />
      )}
      {showRoomSection && !roomLoading && room && (
        <RoomView
          room={room}
          roomReady={roomReady}
          hasImage={hasImage}
          roomItems={roomItems}
          gameStarted={gameStarted}
          taskModalOpen={taskModalOpen}
          panoramaRef={panoramaRef}
          onRoomImageLoad={onRoomImageLoad}
          onRoomImageError={onRoomImageError}
          onHotspotClick={handleHotspotClick}
          openTask={openTask}
          solvedItemIds={solvedItemIds}
          allPuzzlesSolved={allPuzzlesSolved}
        />
      )}
      {doorVideoPlaying && gameStarted && (
        <DoorVideoOverlay
          roomImageUrl={room?.room_image_url}
          videoRef={doorVideoRef}
          onEnded={handleDoorVideoEnded}
          onError={handleDoorVideoError}
        />
      )}
      {showScienceLabRoom && (
        <ScienceLabRoom
          panoramaRef={scienceLabPanoramaRef}
          onImageLoad={() => setScienceLabImageLoaded(true)}
        />
      )}
      {taskModalOpen && selectedItem && selectedPuzzle && (
        <TaskModal
          selectedItem={selectedItem}
          selectedPuzzle={selectedPuzzle}
          unlockAnswer={unlockAnswer}
          setUnlockAnswer={setUnlockAnswer}
          actionMessage={actionMessage}
          actionSubmitting={actionSubmitting}
          submitUnlockAnswer={submitUnlockAnswer}
          closeTaskModal={closeTaskModal}
          handleCloseModal={handleCloseModal}
        />
      )}
    </div>
  )
}
