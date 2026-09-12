import { useCallback, useEffect, useMemo, useState, type CSSProperties } from 'react'
import { ArrowClockwise, Flame, Heart, Sword, Trophy, UserCircle, WarningCircle } from '@phosphor-icons/react'
import { api } from './api'
import { errorText, haptic } from './lib'
import type { MeResponse } from './types'
import { BattleScreen } from './screens/BattleScreen'
import { LeaderboardScreen } from './screens/LeaderboardScreen'
import { MatchesScreen } from './screens/MatchesScreen'
import { ProfileScreen } from './screens/ProfileScreen'
import { RateScreen } from './screens/RateScreen'

type Tab = 'battle' | 'rate' | 'leaderboard' | 'matches' | 'profile'

function NavIcon({ tab, active }: { tab: Tab; active: boolean }) {
  // Outline at rest, filled when the tab is active.
  const weight = active ? 'fill' : 'regular'
  const iconProps = {
    className: 'nav-icon',
    size: 26,
    weight,
    'aria-hidden': true,
  } as const

  if (tab === 'battle') return <Sword {...iconProps} />
  if (tab === 'rate') return <Flame {...iconProps} />
  if (tab === 'leaderboard') return <Trophy {...iconProps} />
  if (tab === 'matches') return <Heart {...iconProps} />
  return <UserCircle {...iconProps} />
}

const navItems: Array<{ id: Tab; label: string }> = [
  { id: 'battle', label: 'Battle' },
  { id: 'rate', label: 'Оценка' },
  { id: 'leaderboard', label: 'Рейтинг' },
  { id: 'matches', label: 'Матчи' },
  { id: 'profile', label: 'Профиль' },
]

export default function App() {
  const [tab, setTab] = useState<Tab>('battle')
  const [me, setMe] = useState<MeResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshMe = useCallback(async () => {
    try {
      setMe(await api.me())
      setError(null)
    } catch (err) {
      setError(errorText(err))
      throw err
    }
  }, [])

  useEffect(() => {
    refreshMe()
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [refreshMe])

  const screen = useMemo(() => {
    if (!me) return null
    if (tab === 'battle') return <BattleScreen onStatsChanged={refreshMe} />
    if (tab === 'rate') return <RateScreen onStatsChanged={refreshMe} />
    if (tab === 'leaderboard') return <LeaderboardScreen />
    if (tab === 'matches') return <MatchesScreen />
    return <ProfileScreen me={me} />
  }, [me, tab, refreshMe])

  if (loading) {
    return (
      <main className="boot">
        <div className="logo-mark">M</div>
        <b>Mogaem</b>
        <span>Загружаем твой рейтинг…</span>
      </main>
    )
  }

  if (error && !me) {
    return (
      <main className="boot error-boot">
        <div className="logo-mark">!</div>
        <b>Mini App не открылся</b>
        <span>{error}</span>
        <button onClick={() => window.location.reload()} type="button">
          <span>Попробовать снова</span>
          <span className="btn-orb" aria-hidden="true">
            <ArrowClockwise size={13} weight="bold" />
          </span>
        </button>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <main className="content">{screen}</main>
      <nav className="bottom-nav" aria-label="Основная навигация">
        <div className="nav-track">
          <span
            aria-hidden="true"
            className="nav-thumb"
            style={{ '--nav-index': navItems.findIndex((item) => item.id === tab) } as CSSProperties}
          />
          {navItems.map((item) => (
            <button
              className={tab === item.id ? 'active' : ''}
              key={item.id}
              onClick={() => {
                setTab(item.id)
                haptic('select')
              }}
              type="button"
              aria-current={tab === item.id ? 'page' : undefined}
            >
              <NavIcon tab={item.id} active={tab === item.id} />
              {/* Section name lives in the screen header; the bar is
                  icon-only, the label stays for screen readers. */}
              <small className="visually-hidden">{item.label}</small>
            </button>
          ))}
        </div>
      </nav>
    </div>
  )
}
