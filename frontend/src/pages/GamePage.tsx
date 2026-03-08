import { useCallback, useEffect, useRef, useState } from 'react'
import {
  getGameState,
  notifyDoorOpened,
  sendGameAction,
  type ApiError,
  type GameStateResponse,
  type RoomItemResponse,
} from '../api/client'
import { MESSAGES } from '../constants/messages'
import { getBlockedItemMessage, getPuzzleSuccessMessage } from '../constants/puzzleMessages'
import { Banners } from '../components/Banners'
import { DoorVideoOverlay } from '../components/DoorVideoOverlay'
import { RoomView } from '../components/RoomView'
import { ScienceLabRoom } from '../components/ScienceLabRoom'
import { TaskModal } from '../components/TaskModal'
import { useCenterScrollOnLoad } from '../hooks/useCenterScrollOnLoad'
import { useGameStateSync } from '../hooks/useGameStateSync'
import { useGameSSE } from '../hooks/useGameSSE'
import { useGameTimer } from '../hooks/useGameTimer'
import { useNarration } from '../hooks/useNarration'
import { getPuzzleByItemId, getPuzzles } from '../utils/gameHelpers'

function getTelegramWebApp() {
  return window.Telegram?.WebApp ?? {}
}

export default function GamePage() {
  const [gameId, setGameId] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('')
  const [statusError, setStatusError] = useState(false)
  const [roomLoading, setRoomLoading] = useState(true)
  const [room, setRoom] = useState<GameStateResponse | null>(null)
  const [gameStarted, setGameStarted] = useState(false)
  const [startedAtIso, setStartedAtIso] = useState<string | null>(null)
  const [roomImageLoaded, setRoomImageLoaded] = useState(false)
  const [solvedItemIds, setSolvedItemIds] = useState<string[]>([])
  const [doorVideoPlaying, setDoorVideoPlaying] = useState(false)
  const [showScienceLabRoom, setShowScienceLabRoom] = useState(false)
  const [scienceLabImageLoaded, setScienceLabImageLoaded] = useState(false)
  const [doorLockedMessage, setDoorLockedMessage] = useState(false)
  const [blockedItemMessage, setBlockedItemMessage] = useState<string | null>(null)
  const [puzzleSolvedNotification, setPuzzleSolvedNotification] = useState<string | null>(null)

  const [taskModalOpen, setTaskModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<RoomItemResponse | null>(null)
  const [unlockAnswer, setUnlockAnswer] = useState('')
  const [actionMessage, setActionMessage] = useState<{ text: string; isSuccess: boolean } | null>(null)
  const [actionSubmitting, setActionSubmitting] = useState(false)

  const panoramaRef = useRef<HTMLDivElement>(null)
  const scienceLabPanoramaRef = useRef<HTMLDivElement>(null)
  const modalTTSRef = useRef<SpeechSynthesisUtterance | null>(null)
  const doorVideoRef = useRef<HTMLVideoElement | null>(null)
  const closeModalRef = useRef<() => void>(() => {})
  const pollCleanupRef = useRef<(() => void) | null>(null)

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

  const timer = useGameTimer(gameId)
  const narration = useNarration(
    gameId,
    gameStarted,
    startedAtIso,
    room,
    timer.setTimerVisible
  )
  const sync = useGameStateSync({
    gameId,
    setRoom,
    setSolvedItemIds,
    setDoorVideoPlaying,
    setScienceLabImageLoaded,
    setShowScienceLabRoom,
    setGameStarted,
    setStartedAtIso,
    setTimerVisible: timer.setTimerVisible,
    setLoreNarrationActive: narration.setLoreNarrationActive,
    setShowNarrationButton: narration.setShowNarrationButton,
    stopTimerAndSetGameOver: timer.stopTimerAndSetGameOver,
    startTimerFromServerTime: timer.startTimerFromServerTime,
    narrationInProgressRef: narration.narrationInProgressRef,
  })

  useGameSSE({
    gameId,
    applyStartedState: sync.applyStartedState,
    syncGameStateFromServer: sync.syncGameStateFromServer,
    stopTimerAndSetGameOver: timer.stopTimerAndSetGameOver,
    setSolvedItemIds,
    setDoorVideoPlaying,
    setPuzzleSolvedNotification,
  })

  useEffect(() => {
    if (!gameId) {
      setRoomLoading(false)
      showStatus(MESSAGES.START_IN_GROUP, false)
      return
    }
    timer.clearTimer()
    pollCleanupRef.current?.()
    pollCleanupRef.current = null
    setRoomLoading(true)
    setRoomImageLoaded(false)
    setSolvedItemIds([])
    setGameStarted(false)
    setStartedAtIso(null)
    timer.setTimerVisible(false)
    narration.resetForNewGame()
    getGameState(gameId)
      .then((data) => {
        setRoomLoading(false)
        showStatus('', false)
        sync.applyGameStateFromServer(data)
        if (!data.started_at) {
          pollCleanupRef.current = sync.waitForStart()
        }
      })
      .catch((e: ApiError) => {
        setRoomLoading(false)
        setRoom(null)
        const msg = e?.detail ?? (e?.status === 404 ? MESSAGES.GAME_NOT_FOUND : MESSAGES.LOAD_ERROR)
        showStatus(msg, true)
      })
    return () => {
      pollCleanupRef.current?.()
      pollCleanupRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- only re-run when gameId changes
  }, [gameId])

  const hasRoomImage = !!(room?.room_image_url && (room?.room_items?.length ?? 0) > 0)
  useEffect(() => {
    if (!roomLoading && hasRoomImage) document.body.classList.add('game-has-room')
    return () => document.body.classList.remove('game-has-room')
  }, [roomLoading, hasRoomImage])

  const onRoomImageLoad = useCallback(() => setRoomImageLoaded(true), [])
  const onRoomImageError = useCallback(() => setRoomImageLoaded(true), [])

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
    const synth = typeof window !== 'undefined' ? window.speechSynthesis : null
    if (synth && document.hasFocus?.() && (synth.speaking || synth.pending)) synth.cancel()
    modalTTSRef.current = null
    setTaskModalOpen(false)
    setSelectedItem(null)
    setUnlockAnswer('')
    setActionMessage(null)
  }, [])

  const closeTaskModal = useCallback((e?: React.MouseEvent | React.PointerEvent) => {
    e?.preventDefault?.()
    e?.stopPropagation?.()
    closeModalState()
  }, [closeModalState])

  const handleCloseModal = useCallback(() => {
    const synth = typeof window !== 'undefined' ? window.speechSynthesis : null
    if (synth && document.hasFocus?.() && (synth.speaking || synth.pending)) synth.cancel()
    closeModalState()
  }, [closeModalState])
  closeModalRef.current = handleCloseModal

  useEffect(() => {
    const backBtn = window.Telegram?.WebApp?.BackButton
    const version = window.Telegram?.WebApp?.version ?? ''
    if (!backBtn || version.startsWith('6.0')) return
    if (!taskModalOpen) {
      try { backBtn.hide() } catch { /* unsupported */ }
      return
    }
    const onBack = () => {
      closeModalRef.current?.()
      try { backBtn.hide(); backBtn.offClick(onBack) } catch { /* ignore */ }
    }
    try {
      backBtn.onClick(onBack)
      backBtn.show()
    } catch { return }
    return () => {
      try { backBtn.hide(); backBtn.offClick(onBack) } catch { /* ignore */ }
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
        const successText = getPuzzleSuccessMessage(selectedItem?.id ?? '')
        setActionMessage({
          text: res.message ?? (res.correct ? successText : 'סיסמה שגויה.'),
          isSuccess: !!res.correct,
        })
        if (res.correct) {
          setSolvedItemIds((prev) => (prev.includes(selectedItem.id) ? prev : [...prev, selectedItem.id]))
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
  const roomReady = !roomLoading && (hasImage ? roomImageLoaded : true)
  const showLoadingOverlay = roomLoading || (gameStarted && !roomReady)

  const handleHotspotClick = useCallback(
    (params: {
      item: RoomItemResponse
      shapeItemId: string
      allPuzzlesSolved: boolean
      solvedItemIds: string[]
    }) => {
      const { item, shapeItemId, allPuzzlesSolved: allSolved, solvedItemIds: solved } = params
      if (!gameStarted || narration.loreNarrationActive) return
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
      const deps = room?.puzzle_dependencies?.[shapeItemId]
      const depsNotMet = deps?.length
        ? !deps.every((id) => solved.includes(id))
        : shapeItemId === 'board_servers' && !solved.includes('clock_1')
      if (depsNotMet) {
        setBlockedItemMessage(getBlockedItemMessage(shapeItemId))
        setTimeout(() => setBlockedItemMessage(null), 4000)
        return
      }
      openTask(item)
    },
    [gameStarted, narration.loreNarrationActive, gameId, room?.puzzle_dependencies, openTask]
  )

  const handleDoorVideoEnded = useCallback(() => {
    setTimeout(() => {
      setDoorVideoPlaying(false)
      setScienceLabImageLoaded(false)
      setShowScienceLabRoom(true)
    }, 450)
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
        showTimer={timer.timerVisible}
        gameOver={timer.gameOver}
        secondsLeft={timer.secondsLeft}
        puzzleSolvedNotification={puzzleSolvedNotification}
        doorLockedMessage={doorLockedMessage}
        blockedItemMessage={blockedItemMessage}
        status={status}
        statusError={statusError}
      />
      {room && !roomLoading && !gameStarted && !showLoadingOverlay && (
        <div className="waiting-screen">
          <p>⏳ ממתין שהמשחק יתחיל...</p>
        </div>
      )}
      {narration.showNarrationButton && gameStarted && (
        <button type="button" className="narration-button" onClick={narration.handleNarrationClick}>
          🔊 התחל והאזן לסיפור
        </button>
      )}
      {showRoomSection && !roomLoading && room && gameStarted && (
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
