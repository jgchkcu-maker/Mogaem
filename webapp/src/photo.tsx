import { useEffect, useState, type ReactNode } from 'react'
import { api } from './api'

export function usePhoto(userId: number | null, position = 0) {
  const [url, setUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) {
      setUrl(null)
      return
    }
    let alive = true
    let objectUrl: string | null = null
    api.photoBlobUrl(userId, position)
      .then((nextUrl) => {
        objectUrl = nextUrl
        if (alive) setUrl(nextUrl)
      })
      .catch(() => {
        if (alive) setUrl(null)
      })
    return () => {
      alive = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [userId, position])

  return url
}

/**
 * Authenticated photo frame. Children render on top of the photo (scrims,
 * name overlays, stat chips); a MOG placeholder fills in while the photo is
 * missing or still loading.
 */
export function Photo({
  userId,
  alt,
  className,
  children,
}: {
  userId: number
  alt: string
  className: string
  children?: ReactNode
}) {
  const photo = usePhoto(userId)
  return (
    <div className={className}>
      {photo ? <img src={photo} alt={alt} /> : <div className="photo-placeholder">MOG</div>}
      {children}
    </div>
  )
}

export function Avatar({ userId, name }: { userId: number; name?: string }) {
  return <Photo userId={userId} alt={name ?? ''} className="row-avatar" />
}
