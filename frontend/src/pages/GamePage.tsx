import { useCallback, useEffect, useRef, useState } from 'react'
import {
  getGameState,
  getGameWebSocketUrl,
  getLoreAudioUrl,
  reportTimeUp,
  sendGameAction,
  type ApiError,
  type GameStateResponse,
  type PuzzleSolvedEvent,
  type PuzzleResponse,
  type RoomItemResponse,
  DEMO_ROOM_WIDTH,
  DEMO_ROOM_HEIGHT,
} from '../api/client'
import '../index.css'

const MESSAGES = {
  START_IN_GROUP: 'התחל משחק בקבוצה עם /start_game ולחץ על "שחק עכשיו".',
  GAME_NOT_FOUND: 'משחק לא נמצא או שהסתיים. פתח את הלינק מההודעה של הבוט.',
  LOAD_ERROR: 'שגיאה בטעינת המשחק.',
} as const

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready?: () => void | Promise<void>
        expand?: () => void
        initDataUnsafe?: { user?: { first_name?: string } }
        sendData?: (data: string) => void
      }
    }
  }
}

function getTelegramWebApp() {
  return window.Telegram?.WebApp ?? {}
}

function getPuzzles(room: GameStateResponse | null): PuzzleResponse[] {
  if (!room) return []
  if (room.puzzles && room.puzzles.length > 0) return room.puzzles
  if (room.puzzle) return [{ ...room.puzzle, type: room.puzzle.type ?? 'unlock' }]
  return []
}

function getPuzzleByItemId(room: GameStateResponse | null, itemId: string): PuzzleResponse | undefined {
  return getPuzzles(room).find((p) => p.item_id === itemId)
}

const INITIAL_TIMER_SECONDS = 3600 // 01:00:00

function formatTimer(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':')
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
  const panoramaRef = useRef<HTMLDivElement>(null)
  const lorePlayedRef = useRef(false)
  const timerStartedRef = useRef(false)
  const timeUpSentRef = useRef(false)

  const tg = getTelegramWebApp()
  if (tg.expand) tg.expand()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    setGameId(params.get('game_id'))
  }, [])

  const showStatus = useCallback((text: string, isError: boolean) => {
    setStatus(text)
    setStatusError(isError)
  }, [])

  const playLoreAudio = useCallback((gid: string) => {
    if (lorePlayedRef.current) return
    lorePlayedRef.current = true
    fetch(getLoreAudioUrl(gid))
      .then((r) => (r.ok ? r.blob() : null))
      .then((blob) => {
        if (!blob) return
        const audio = new Audio(URL.createObjectURL(blob))
        audio.play()
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!gameId) {
      showStatus(MESSAGES.START_IN_GROUP, false)
      return
    }
    setRoomLoading(true)
    lorePlayedRef.current = false
    getGameState(gameId)
      .then((data) => {
        setRoomLoading(false)
        showStatus('', false)
        setRoom(data)
      })
      .catch((e: ApiError) => {
        setRoomLoading(false)
        setRoom(null)
        const msg = e?.detail ?? (e?.status === 404 ? MESSAGES.GAME_NOT_FOUND : MESSAGES.LOAD_ERROR)
        showStatus(msg, true)
      })
  }, [gameId, showStatus])

  useEffect(() => {
    if (!gameId || !room?.room_lore || roomLoading || room?.room_image_url) return
    playLoreAudio(gameId)
  }, [gameId, room?.room_lore, room?.room_image_url, roomLoading, playLoreAudio])

  useEffect(() => {
    const hasRoomImage = !roomLoading && (room?.room_items?.length ?? 0) > 0 && Boolean(room?.room_image_url)
    if (hasRoomImage) document.body.classList.add('game-has-room')
    return () => document.body.classList.remove('game-has-room')
  }, [roomLoading, room?.room_items?.length, room?.room_image_url])

  const showTimer = (room?.room_items?.length ?? 0) > 0 && !roomLoading
  useEffect(() => {
    if (!showTimer) return
    if (!timerStartedRef.current) {
      timerStartedRef.current = true
      setSecondsLeft(INITIAL_TIMER_SECONDS)
    }
    const id = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(id)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(id)
  }, [showTimer])

  useEffect(() => {
    if (!showTimer || !gameId || secondsLeft > 0 || timeUpSentRef.current) return
    timeUpSentRef.current = true
    reportTimeUp(gameId).catch(() => {})
  }, [showTimer, gameId, secondsLeft])

  useEffect(() => {
    if (!showTimer) timerStartedRef.current = false
  }, [showTimer])

  useEffect(() => {
    timeUpSentRef.current = false
  }, [gameId])

  const puzzleSolvedTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(() => {
    if (!gameId || !room) return
    const url = getGameWebSocketUrl(gameId)
    const ws = new WebSocket(url)
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as PuzzleSolvedEvent | { event: string }
        if (data.event === 'game_over') {
          setGameOver(true)
          return
        }
        if (data.event !== 'puzzle_solved') return
        const text = (data as PuzzleSolvedEvent).solver_name
          ? `${(data as PuzzleSolvedEvent).solver_name} פתח/ה את ${(data as PuzzleSolvedEvent).item_label}. הפתרון: ${(data as PuzzleSolvedEvent).answer}`
          : `${(data as PuzzleSolvedEvent).item_label} נפתח/ה. הפתרון: ${(data as PuzzleSolvedEvent).answer}`
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
  }, [gameId, room])

  const onRoomImageLoad = useCallback(() => {
    const wrap = panoramaRef.current
    if (!wrap) return
    const centerScroll = () => {
      if (!panoramaRef.current) return
      const w = panoramaRef.current
      const maxScroll = w.scrollWidth - w.clientWidth
      w.scrollLeft = maxScroll > 0 ? maxScroll / 2 : 0
    }
    requestAnimationFrame(() => requestAnimationFrame(centerScroll))
    setTimeout(centerScroll, 150)
    if (gameId && room?.room_lore) playLoreAudio(gameId)
  }, [gameId, room?.room_lore, playLoreAudio])

  const openTask = useCallback((item: RoomItemResponse) => {
    setSelectedItem(item)
    setTaskModalOpen(true)
    setUnlockAnswer('')
    setActionMessage(null)
  }, [])

  const closeTaskModal = useCallback(() => {
    setTaskModalOpen(false)
    setSelectedItem(null)
    setUnlockAnswer('')
    setActionMessage(null)
  }, [])

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
        setActionMessage({
          text: res.message ?? (res.correct ? 'הכספת נפתחה!' : 'סיסמה שגויה.'),
          isSuccess: !!res.correct,
        })
        if (res.correct) setTimeout(closeTaskModal, 2000)
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

  return (
    <div className="game-container">
      {gameOver && (
        <div className="game-over-overlay" role="alert">
          <h2 className="game-over-title">Game Over</h2>
          <p className="game-over-text">הזמן נגמר. המשחק הסתיים.</p>
          <p className="game-over-hint">כתבו /start_game בקבוצה כדי להתחיל מחדש.</p>
        </div>
      )}
      {showTimer && !gameOver && (
        <div className="room-timer" aria-live="polite">
          {formatTimer(secondsLeft)}
        </div>
      )}
      {puzzleSolvedNotification && (
        <div className="puzzle-solved-banner" role="alert">
          {puzzleSolvedNotification}
        </div>
      )}
      {roomLoading && <p className="room-loading">טוען…</p>}
      {status && (
        <p className={statusError ? 'error' : 'status'} id="game-status">
          {status}
        </p>
      )}
      {showRoomSection && !roomLoading && (
        <div className="room-section">
          {situationText && (
            <p className="room-situation" aria-live="polite">
              {situationText}
            </p>
          )}
          {hasImage ? (
            <div className="room-wrapper" ref={panoramaRef}>
              <div className="room-container">
                <img
                  src={room!.room_image_url}
                  className="room-image"
                  alt="חדר בריחה"
                  onLoad={onRoomImageLoad}
                />
                {roomItems.map((it) => {
                  const imgW = room?.room_image_width ?? DEMO_ROOM_WIDTH
                  const imgH = room?.room_image_height ?? DEMO_ROOM_HEIGHT
                  const leftPct = (it.x / imgW) * 100
                  const topPct = (it.y / imgH) * 100
                  const hotspotW = 14
                  const hotspotH = 18
                  return (
                    <button
                      key={it.id}
                      type="button"
                      className="room-hotspot"
                      style={{
                        left: `${leftPct}%`,
                        top: `${topPct}%`,
                        width: `${hotspotW}%`,
                        height: `${hotspotH}%`,
                        transform: 'translate(-50%, -50%)',
                      }}
                      onClick={() => openTask(it)}
                      title={it.label}
                    >
                      <span className="room-hotspot-label">{it.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="room-placeholder-wrap">
              <div
                className="room-placeholder"
                style={{ width: DEMO_ROOM_WIDTH, height: DEMO_ROOM_HEIGHT }}
              >
                <p className="room-placeholder-label">לחץ על הפריטים – גלול ימינה/שמאלה לראות את כל החדר</p>
                {roomItems.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="room-item-hotspot"
                    style={{ left: it.x, top: it.y }}
                    onClick={() => openTask(it)}
                    title={it.label}
                  >
                    {it.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      {taskModalOpen && selectedItem && selectedPuzzle && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="task-modal-title"
        >
          <div className="modal-content">
            <h2 id="task-modal-title">{selectedItem.label}</h2>
            <p className="modal-backstory">{selectedPuzzle.backstory}</p>
            {selectedPuzzle.type === 'unlock' && (
              <>
                {selectedPuzzle.encoded_clue != null && (
                  <p className="modal-clue">
                    <strong>הקוד במסוף:</strong> <code>{selectedPuzzle.encoded_clue}</code>
                  </p>
                )}
                {selectedPuzzle.prompt_text != null && (
                  <p className="modal-prompt">{selectedPuzzle.prompt_text}</p>
                )}
                <input
                  type="text"
                  className="modal-input"
                  value={unlockAnswer}
                  onChange={(e) => setUnlockAnswer(e.target.value)}
                  placeholder="הכנס את הסיסמה שפיענחת"
                  dir="ltr"
                  autoComplete="off"
                  onKeyDown={(e) => e.key === 'Enter' && submitUnlockAnswer()}
                />
                {actionMessage && (
                  <p className={actionMessage.isSuccess ? 'modal-success' : 'modal-error'}>
                    {actionMessage.text}
                  </p>
                )}
                <div className="modal-actions">
                  <button
                    type="button"
                    onClick={submitUnlockAnswer}
                    disabled={actionSubmitting}
                  >
                    {actionSubmitting ? 'שולח…' : 'בדוק'}
                  </button>
                  <button type="button" onClick={closeTaskModal}>
                    סגור
                  </button>
                </div>
              </>
            )}
            {selectedPuzzle.type === 'examine' && (
              <div className="modal-actions">
                <button type="button" onClick={closeTaskModal}>
                  סגור
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
