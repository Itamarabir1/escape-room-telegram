/** Title of the toast shown when a puzzle is solved (SSE). */
export const PUZZLE_SOLVED_TOAST_TITLE = 'חידה נפתרה'

/** Toast text when a puzzle is solved (SSE / other player). */
export function getPuzzleSolvedNotificationText(
  itemId: string,
  itemLabel?: string,
  answer?: string
): string {
  switch (itemId) {
    case 'clock_1':
      return 'השעון כוון בהצלחה'
    case 'board_servers':
      return 'לוח הבקרה נפתח בהצלחה'
    case 'safe_1':
      return 'הכספת נפתחה בהצלחה בתוכה יש מפתח'
    default:
      return itemLabel && answer != null
        ? `חידת ${itemLabel} נפתרה הפתרון הוא ${answer}`
        : PUZZLE_SOLVED_TOAST_TITLE
  }
}

/** Short success message in modal after correct unlock submit. */
export function getPuzzleSuccessMessage(itemId: string): string {
  switch (itemId) {
    case 'board_servers':
      return 'לוח הבקרה נפתח!'
    case 'safe_1':
      return 'הכספת נפתחה!'
    default:
      return 'נפתר בהצלחה!'
  }
}

/** Message when user tries an action that is blocked by dependencies. */
export function getBlockedItemMessage(shapeItemId: string): string {
  return shapeItemId === 'board_servers'
    ? 'כוונו את השעון כדי לפתוח את לוח הבקרה.'
    : 'יש לפתור קודם חידות אחרות בחדר.'
}
