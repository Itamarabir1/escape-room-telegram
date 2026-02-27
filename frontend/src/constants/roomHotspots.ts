/** Initial countdown duration in seconds (01:00:00). */
export const INITIAL_TIMER_SECONDS = 3600

/** Door opening video – served by backend from images/door_open.mp4 at same base as room image */
export function getDoorVideoSrc(roomImageUrl: string | undefined): string {
  if (!roomImageUrl) return '/room/door_open.mp4'
  return roomImageUrl.replace(/escape_room\.png$/i, 'door_open.mp4')
}

/** Hotspot shapes for room image 1280×768 – polygon points and circle (cx, cy, r) */
export const ROOM_HOTSPOT_SHAPES: Array<
  | { itemId: string; type: 'polygon'; points: string }
  | { itemId: string; type: 'circle'; cx: number; cy: number; r: number }
> = [
  { itemId: 'door', type: 'polygon', points: '753,289 890,295 895,475 850,475 849,555 755,557' },
  { itemId: 'safe_1', type: 'polygon', points: '965,523 1131,527 1185,725 990,700 961,669' },
  { itemId: 'clock_1', type: 'circle', cx: 649, cy: 248, r: 41 },
  { itemId: 'board_servers', type: 'polygon', points: '7,38 351,236 346,560 1,723' },
]

export function formatTimer(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':')
}
