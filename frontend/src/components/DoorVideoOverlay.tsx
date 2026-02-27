import type { RefObject } from 'react'
import { getDoorVideoSrc } from '../constants/roomHotspots'

type DoorVideoOverlayProps = {
  roomImageUrl: string | undefined
  videoRef: RefObject<HTMLVideoElement>
  onEnded: () => void
  onError: () => void
}

export function DoorVideoOverlay(props: DoorVideoOverlayProps) {
  const { roomImageUrl, videoRef, onEnded, onError } = props
  return (
    <div className="door-video-fullscreen" role="presentation">
      <video
        ref={videoRef}
        className="door-video-fullscreen-video"
        src={getDoorVideoSrc(roomImageUrl)}
        autoPlay
        muted
        playsInline
        onEnded={onEnded}
        onError={onError}
        onLoadedData={() => videoRef.current?.play().catch(() => {})}
      />
    </div>
  )
}
