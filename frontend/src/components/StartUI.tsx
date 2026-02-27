type StartUIProps = {
  situationText: string
  loreNarrationActive: boolean
  onStartClick: () => void
}

export function StartUI({ situationText, loreNarrationActive, onStartClick }: StartUIProps) {
  return (
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
  )
}
