import type { PuzzleResponse, RoomItemResponse } from '../api/client'

function ModalCloseButton({ onClose }: { onClose: () => void }) {
  return (
    <button
      type="button"
      className="modal-close-btn-wrapper"
      aria-label="סגור"
      onClick={onClose}
      onTouchEnd={() => onClose()}
    >
      סגור
    </button>
  )
}

type TaskModalProps = {
  selectedItem: RoomItemResponse
  selectedPuzzle: PuzzleResponse
  unlockAnswer: string
  setUnlockAnswer: (value: string) => void
  actionMessage: { text: string; isSuccess: boolean } | null
  actionSubmitting: boolean
  submitUnlockAnswer: () => void
  closeTaskModal: (e?: React.MouseEvent | React.PointerEvent) => void
  handleCloseModal: () => void
}

export function TaskModal({
  selectedItem,
  selectedPuzzle,
  unlockAnswer,
  setUnlockAnswer,
  actionMessage,
  actionSubmitting,
  submitUnlockAnswer,
  closeTaskModal,
  handleCloseModal,
}: TaskModalProps) {
  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="task-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) closeTaskModal(e)
      }}
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
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
              <>
                <p className="modal-clue">
                  <strong>הקוד במסוף:</strong> <code>{selectedPuzzle.encoded_clue}</code>
                </p>
                {selectedItem.id === 'safe_1' && (
                  <p className="modal-clue modal-secret-hint">השתמשו גם במספר הסודי</p>
                )}
              </>
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
              <ModalCloseButton onClose={handleCloseModal} />
            </div>
          </>
        )}
        {selectedPuzzle.type === 'examine' && (
          <div className="modal-actions">
            <ModalCloseButton onClose={handleCloseModal} />
          </div>
        )}
        {selectedPuzzle.type !== 'unlock' && selectedPuzzle.type !== 'examine' && (
          <div className="modal-actions">
            <ModalCloseButton onClose={handleCloseModal} />
          </div>
        )}
      </div>
    </div>
  )
}
