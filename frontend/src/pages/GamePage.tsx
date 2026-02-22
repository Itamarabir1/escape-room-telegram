import { useCallback, useEffect, useRef, useState } from 'react'
import {
  getGameState,
  getLoreAudioUrl,
  sendGameAction,
  type ApiError,
  type GameStateResponse,
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
  const panoramaRef = useRef<HTMLDivElement>(null)
  const lorePlayedRef = useRef(false)

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
    if (gameId && room?.room_lore && !roomLoading) {
      playLoreAudio(gameId)
    }
  }, [gameId, room?.room_lore, roomLoading, playLoreAudio])

  const onRoomImageLoad = useCallback(() => {
    const wrap = panoramaRef.current
    if (wrap) wrap.scrollLeft = (wrap.scrollWidth - wrap.clientWidth) / 2
  }, [])

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
    sendGameAction(gameId, { item_id: selectedItem.id, answer: unlockAnswer.trim() })
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
            <div className="room-panorama-wrap" ref={panoramaRef}>
              <div className="room-panorama-inner">
                <img src={room!.room_image_url} alt="חדר בריחה" onLoad={onRoomImageLoad} />
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
