import type { RefObject } from 'react'
import type { GameStateResponse, RoomItemResponse } from '../api/client'
import { DEMO_ROOM_WIDTH, DEMO_ROOM_HEIGHT, getEffectiveRoomImageUrl } from '../api/client'
import { ROOM_HOTSPOT_SHAPES } from '../constants/roomHotspots'

type RoomViewProps = {
  room: GameStateResponse
  roomReady: boolean
  hasImage: boolean
  roomItems: RoomItemResponse[]
  gameStarted: boolean
  taskModalOpen: boolean
  panoramaRef: RefObject<HTMLDivElement>
  onRoomImageLoad: () => void
  onRoomImageError?: () => void
  onHotspotClick: (params: {
    item: RoomItemResponse
    shapeItemId: string
    allPuzzlesSolved: boolean
    solvedItemIds: string[]
  }) => void
  openTask: (item: RoomItemResponse) => void
  solvedItemIds: string[]
  allPuzzlesSolved: boolean
}

export function RoomView({
  room,
  roomReady,
  hasImage,
  roomItems,
  gameStarted,
  taskModalOpen,
  panoramaRef,
  onRoomImageLoad,
  onRoomImageError,
  onHotspotClick,
  openTask,
  solvedItemIds,
  allPuzzlesSolved,
}: RoomViewProps) {
  const roomImageSrc = getEffectiveRoomImageUrl(room.room_image_url)

  return (
    <div className={`room-section ${roomReady ? 'room-section--ready' : ''}`}>
      {hasImage ? (
        <div className="room-wrapper" ref={panoramaRef}>
          <div className="room-container">
            <img
              src={roomImageSrc}
              className="room-image"
              alt="חדר בריחה"
              onLoad={onRoomImageLoad}
              onError={(e) => {
                console.error(
                  'Room image failed to load (404/403 or wrong MIME):',
                  e.currentTarget?.src ?? room.room_image_url
                )
                onRoomImageError?.()
              }}
            />
            <svg
              className={`room-hotspots-svg ${!gameStarted ? 'room-hotspots-disabled' : ''} ${taskModalOpen ? 'room-hotspots-svg--modal-open' : ''}`}
              viewBox={`0 0 ${room?.room_image_width ?? 1280} ${room?.room_image_height ?? 768}`}
              preserveAspectRatio="xMidYMid meet"
              aria-label="מפת חדר עם אזורי לחיצה"
              role="group"
              style={{ pointerEvents: taskModalOpen ? 'none' : 'auto' }}
            >
              {ROOM_HOTSPOT_SHAPES.map((shape) => {
                const item = roomItems.find((it) => it.id === shape.itemId)
                if (!item) return null
                const handleClick = () => {
                  onHotspotClick({
                    item,
                    shapeItemId: shape.itemId,
                    allPuzzlesSolved,
                    solvedItemIds,
                  })
                }
                if (shape.type === 'polygon') {
                  return (
                    <polygon
                      key={shape.itemId}
                      points={shape.points}
                      fill="transparent"
                      stroke="transparent"
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
                    fill="transparent"
                    stroke="transparent"
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
            <p className="room-placeholder-label">
              לחץ על הפריטים – גלול ימינה/שמאלה לראות את כל החדר
            </p>
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
  )
}
