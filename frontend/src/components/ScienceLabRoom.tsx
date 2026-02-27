import type { RefObject } from 'react'

type ScienceLabRoomProps = {
  panoramaRef: RefObject<HTMLDivElement>
  onImageLoad: () => void
}

export function ScienceLabRoom(props: ScienceLabRoomProps) {
  const { panoramaRef, onImageLoad } = props
  return (
    <div className="science-lab-room" role="region" aria-label="חדר המעבדה">
      <div className="room-wrapper science-lab-room-panorama" ref={panoramaRef}>
        <div className="room-container">
          <img
            src="/room/science_lab_room.png"
            alt="מעבדה"
            className="room-image"
            onLoad={onImageLoad}
          />
        </div>
      </div>
    </div>
  )
}
