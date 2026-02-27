import { formatTimer } from '../constants/roomHotspots'

type BannersProps = {
  showTimer: boolean
  gameOver: boolean
  secondsLeft: number
  puzzleSolvedNotification: string | null
  doorLockedMessage: boolean
  blockedItemMessage: string | null
  status: string
  statusError: boolean
}

export function Banners({
  showTimer,
  gameOver,
  secondsLeft,
  puzzleSolvedNotification,
  doorLockedMessage,
  blockedItemMessage,
  status,
  statusError,
}: BannersProps) {
  return (
    <>
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
      {doorLockedMessage && (
        <div className="door-locked-banner" role="alert">
          הדלת נעולה, עדיין לא השגתם את המפתח לדלת.
        </div>
      )}
      {blockedItemMessage && (
        <div className="door-locked-banner" role="alert">
          {blockedItemMessage}
        </div>
      )}
      {status && (
        <p className={statusError ? 'error' : 'status'} id="game-status">
          {status}
        </p>
      )}
    </>
  )
}
