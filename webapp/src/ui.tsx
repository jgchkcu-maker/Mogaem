import { ArrowClockwise } from '@phosphor-icons/react'
import type { Icon } from '@phosphor-icons/react'
import type { ReactNode } from 'react'

export function ScreenHeader({ title, subtitle }: { title: ReactNode; subtitle: ReactNode }) {
  return (
    <header className="screen-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </header>
  )
}

export function StateBlock({
  icon: Icon,
  title,
  body,
  action,
  onAction,
}: {
  icon: Icon
  title: string
  body?: string
  action?: string
  onAction?: () => void
}) {
  return (
    <div className="state-block">
      <div className="state-icon" aria-hidden="true">
        <Icon size={22} weight="duotone" />
      </div>
      <b>{title}</b>
      {body && <span>{body}</span>}
      {action && onAction && (
        <button onClick={onAction} type="button">
          <span>{action}</span>
          <span className="btn-orb" aria-hidden="true">
            <ArrowClockwise size={13} weight="bold" />
          </span>
        </button>
      )}
    </div>
  )
}

export function LoadingLabel({ text }: { text: string }) {
  return <span className="visually-hidden">{text}</span>
}

export function Skeleton({ className }: { className: string }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />
}
