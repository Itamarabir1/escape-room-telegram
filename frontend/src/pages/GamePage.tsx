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

/** Hotspot shapes for room image 1280×768 – polygon points and circle (cx, cy, r) */
const ROOM_HOTSPOT_SHAPES: Array<
  | { itemId: string; type: 'polygon'; points: string }
  | { itemId: string; type: 'circle'; cx: number; cy: number; r: number }
> = [
  { itemId: 'door', type: 'polygon', points: '753,289 889,291 891,427 853,470 849,555 755,557' },
  { itemId: 'safe_1', type: 'polygon', points: '965,523 1131,527 1187,543 1184,650 965,651' },
  { itemId: 'clock_1', type: 'circle', cx: 649, cy: 248, r: 41 },
  { itemId: 'board_servers', type: 'polygon', points: '7,38 351,236 346,560 1,653' },
]

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
  const [gameStarted, setGameStarted] = useState(false)
  const [startUIVisible, setStartUIVisible] = useState(true)
  const [loreNarrationActive, setLoreNarrationActive] = useState(false)
  const panoramaRef = useRef<HTMLDivElement>(null)
  const [roomImageLoaded, setRoomImageLoaded] = useState(false)
  const lorePlayedRef = useRef(false)

  const timerStartedRef = useRef(false)
  const timeUpSentRef = useRef(false)
  const modalTTSRef = useRef<SpeechSynthesisUtterance | null>(null)

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
      const url = getLoreAudioUrl(gid)
      console.log('[audio] playLoreAudio: fetch', url)
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
      fetch(url)
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
    setRoomLoading(true)
    setRoomImageLoaded(false)
    setGameStarted(false)
    setStartUIVisible(true)
    setLoreNarrationActive(false)
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
    const hasRoomImage = !roomLoading && (room?.room_items?.length ?? 0) > 0 && Boolean(room?.room_image_url)
    if (hasRoomImage) document.body.classList.add('game-has-room')
    return () => document.body.classList.remove('game-has-room')
  }, [roomLoading, room?.room_items?.length, room?.room_image_url])

  const showTimer = (room?.room_items?.length ?? 0) > 0 && !roomLoading && gameStarted
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
    timerStartedRef.current = false
  }, [gameId])

  const onStartClick = useCallback(async () => {
    const SILENT_WAV = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA='
    const unlockedAudioEl = new Audio(SILENT_WAV)
    unlockedAudioEl.play().catch(() => {})

    const situationText = room?.room_lore || room?.room_description || ''
    console.log('[audio] onStartClick: gameId=', gameId, 'situationText length=', situationText.length)
    const onNarrationEnd = () => {
      console.log('[audio] onStartClick: narration ended, hiding button')
      setStartUIVisible(false)
      setGameStarted(true)
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
  }, [gameId, room?.room_lore, room?.room_description, playLoreAudio])

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
    setRoomImageLoaded(true)
  }, [])

  useEffect(() => {
    const hasRoomImage = !!(room?.room_image_url && (room?.room_items?.length ?? 0) > 0)
    if (!hasRoomImage || !roomImageLoaded) return
    const container = panoramaRef.current
    if (!container) return
    const centerScroll = () => {
      const el = panoramaRef.current
      if (!el) return
      const maxScroll = el.scrollWidth - el.clientWidth
      el.scrollLeft = maxScroll > 0 ? maxScroll / 2 : 0
    }
    centerScroll()
    requestAnimationFrame(() => requestAnimationFrame(centerScroll))
    const t1 = setTimeout(centerScroll, 100)
    const t2 = setTimeout(centerScroll, 400)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [room?.room_image_url, room?.room_items?.length, roomImageLoaded])

  const openTask = useCallback((item: RoomItemResponse) => {
    setSelectedItem(item)
    setTaskModalOpen(true)
    setUnlockAnswer('')
    setActionMessage(null)
  }, [])

  const closeTaskModal = useCallback(() => {
    window.speechSynthesis.cancel()
    modalTTSRef.current = null
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
      {showRoomSection && !roomLoading && startUIVisible && (
        <div className="room-start-ui">
          <button
            type="button"
            className="room-start-btn"
            onClick={onStartClick}
            disabled={loreNarrationActive}
            aria-label={loreNarrationActive ? 'מקריא את הסיפור' : 'התחל את המשחק'}
          >
            {loreNarrationActive ? 'מקריא…' : 'התחל'}
          </button>
          {situationText && (
            <p className="room-situation room-situation-below-btn" aria-live="polite">
              {situationText}
            </p>
          )}
        </div>
      )}
      {showRoomSection && !roomLoading && (
        <div className="room-section">
          {hasImage ? (
            <div className="room-wrapper" ref={panoramaRef}>
              <div className="room-container">
                <img
                  src={room!.room_image_url}
                  className="room-image"
                  alt="חדר בריחה"
                  onLoad={onRoomImageLoad}
                />
                <svg
                  className={`room-hotspots-svg ${!gameStarted ? 'room-hotspots-disabled' : ''}`}
                  viewBox={`0 0 ${room?.room_image_width ?? 1280} ${room?.room_image_height ?? 768}`}
                  preserveAspectRatio="xMidYMid meet"
                  aria-hidden
                >
                  {ROOM_HOTSPOT_SHAPES.map((shape) => {
                    const item = roomItems.find((it) => it.id === shape.itemId)
                    if (!item) return null
                    const handleClick = () => {
                      if (!gameStarted) return
                      openTask(item)
                    }
                    if (shape.type === 'polygon') {
                      return (
                        <polygon
                          key={shape.itemId}
                          points={shape.points}
                          fill="rgba(255,200,0,0.15)"
                          stroke="rgba(255,200,0,0.6)"
                          strokeWidth={2}
                          className="room-hotspot-shape"
                          onClick={handleClick}
                          onKeyDown={(e) => e.key === 'Enter' && handleClick()}
                          role="button"
                          tabIndex={0}
                          aria-label={item.label}
                        />
                      )
                    }
                    return (
                      <circle
                        key={shape.itemId}
                        cx={shape.cx}
                        cy={shape.cy}
                        r={shape.r}
                        fill="rgba(255,200,0,0.15)"
                        stroke="rgba(255,200,0,0.6)"
                        strokeWidth={2}
                        className="room-hotspot-shape"
                        onClick={handleClick}
                        onKeyDown={(e) => e.key === 'Enter' && handleClick()}
                        role="button"
                        tabIndex={0}
                        aria-label={item.label}
                      />
                    )
                  })}
                </svg>
              </div>
            </div>
          ) : (
            <div className={`room-placeholder-wrap ${!gameStarted ? 'room-hotspots-disabled' : ''}`}>
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
                    onClick={() => gameStarted && openTask(it)}
                    title={it.label}
                    disabled={!gameStarted}
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
            {selectedPuzzle.backstory != null && selectedPuzzle.backstory !== '' && (
              <p className="modal-backstory modal-text-fullwidth">{selectedPuzzle.backstory}</p>
            )}
            {selectedPuzzle.prompt_text != null && selectedPuzzle.prompt_text !== '' && (
              <p className="modal-prompt modal-text-fullwidth">{selectedPuzzle.prompt_text}</p>
            )}
            {selectedPuzzle.type === 'unlock' && (
              <>
                {selectedPuzzle.encoded_clue != null && (
                  <p className="modal-clue">
                    <strong>הקוד במסוף:</strong> <code>{selectedPuzzle.encoded_clue}</code>
                  </p>
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
