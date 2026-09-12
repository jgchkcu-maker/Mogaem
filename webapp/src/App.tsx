import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ApiError, api } from './api'
import type {
  BattlePlayer,
  BattleResponse,
  LeaderboardEntry,
  MatchItem,
  MeResponse,
  Profile,
  RatingCandidateResponse,
  SearchGender,
} from './types'

type Tab = 'battle' | 'rate' | 'leaderboard' | 'matches' | 'profile'

const mogNames: Record<number, string> = {
  10: 'Гигачад',
  9: 'Чад',
  8: 'Чадлайт',
  7: 'HTN',
  6: 'MTN',
  5: 'LTN',
  4: 'Сабнорми',
  3: 'Инцел-тир',
  2: 'Труцел',
  1: 'Блэкпилл',
}

function haptic(kind: 'select' | 'success' | 'error' = 'select') {
  const feedback = window.Telegram?.WebApp?.HapticFeedback
  if (!feedback) return
  if (kind === 'select') feedback.selectionChanged()
  else feedback.notificationOccurred(kind)
}

function errorText(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message
  return 'Что-то пошло не так'
}

function usePhoto(userId: number | null, position = 0) {
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

function ScreenHeader({ eyebrow, title, subtitle }: { eyebrow: string; title: string; subtitle: string }) {
  return (
    <header className="screen-header">
      <span className="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </header>
  )
}

function StateCard({ children }: { children: ReactNode }) {
  return <div className="state-card">{children}</div>
}

function PlayerCard({ player, onChoose, disabled }: { player: BattlePlayer; onChoose: () => void; disabled: boolean }) {
  const photo = usePhoto(player.user_id)
  return (
    <button className="battle-card" onClick={onChoose} disabled={disabled} type="button">
      <div className="photo-shell">
        {photo ? <img src={photo} alt={player.name} /> : <div className="photo-placeholder">MOG</div>}
        <div className="elo-badge">{player.elo} ELO</div>
      </div>
      <div className="battle-card-copy">
        <strong>{player.name}, {player.age}</strong>
        <span>{player.city || 'Город не указан'}</span>
        <small>{player.calibrating ? `Калибровка · ${player.battles}/10` : `${player.wins}W · ${player.losses}L`}</small>
      </div>
    </button>
  )
}

function BattleScreen({ onStatsChanged }: { onStatsChanged: () => Promise<void> }) {
  const [battle, setBattle] = useState<BattleResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [voting, setVoting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      setBattle(await api.nextBattle())
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const vote = async (winnerId: number) => {
    if (!battle || voting) return
    setVoting(true)
    haptic('select')
    try {
      const before = winnerId === battle.left.user_id ? battle.left.elo : battle.right.elo
      const result = await api.voteBattle(battle.battle_id, winnerId)
      const delta = result.winner.elo - before
      setMessage(`${result.winner.name} MOG’ает · +${delta} ELO`)
      haptic('success')
      await onStatsChanged()
      window.setTimeout(() => { void load() }, 650)
    } catch (err) {
      setError(errorText(err))
      haptic('error')
    } finally {
      setVoting(false)
    }
  }

  return (
    <section className="screen">
      <ScreenHeader eyebrow="MOG BATTLE" title="Кто MOG’ает?" subtitle="Выбери сильнейшую внешку. Elo пересчитается сразу." />
      {loading && <StateCard>Подбираем максимально близкую пару по Elo…</StateCard>}
      {!loading && error && <StateCard><b>Не загрузилось</b><span>{error}</span><button onClick={() => void load()}>Повторить</button></StateCard>}
      {!loading && !error && !battle && <StateCard><b>Пары закончились</b><span>Нужны ещё активные анкеты одного пола или новые сочетания.</span></StateCard>}
      {!loading && battle && (
        <>
          <div className="battle-grid">
            <PlayerCard player={battle.left} disabled={voting} onChoose={() => void vote(battle.left.user_id)} />
            <div className="versus">VS</div>
            <PlayerCard player={battle.right} disabled={voting} onChoose={() => void vote(battle.right.user_id)} />
          </div>
          <div className={`battle-result ${message ? 'show' : ''}`}>{message || 'Тапни по победителю'}</div>
        </>
      )}
    </section>
  )
}

function RatingCard({ profile }: { profile: Profile }) {
  const photo = usePhoto(profile.user_id)
  return (
    <div className="rating-profile">
      <div className="rating-photo">
        {photo ? <img src={photo} alt={profile.name} /> : <div className="photo-placeholder">MOG</div>}
      </div>
      <div>
        <h2>{profile.name}, {profile.age}</h2>
        <p>{profile.city || 'Город не указан'}</p>
      </div>
    </div>
  )
}

function RateScreen({ onStatsChanged }: { onStatsChanged: () => Promise<void> }) {
  const [candidate, setCandidate] = useState<RatingCandidateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setCandidate(await api.nextRating())
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const rate = async (score: number) => {
    if (!candidate || sending) return
    setSending(true)
    haptic('select')
    try {
      await api.rate(candidate.profile.user_id, score)
      haptic('success')
      await onStatsChanged()
      await load()
    } catch (err) {
      setError(errorText(err))
      haptic('error')
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="screen">
      <ScreenHeader eyebrow="MOG SCORE" title="Оцени внешность" subtitle="Оценка 1–10 идёт в средний MOG Score и не смешивается с Battle Elo." />
      {loading && <StateCard>Ищем следующую анкету…</StateCard>}
      {!loading && error && <StateCard><b>Ошибка</b><span>{error}</span><button onClick={() => void load()}>Повторить</button></StateCard>}
      {!loading && !error && !candidate && <StateCard><b>Ты всё оценил</b><span>Новые анкеты появятся здесь автоматически.</span></StateCard>}
      {!loading && candidate && (
        <>
          <RatingCard profile={candidate.profile} />
          <div className="score-grid">
            {Array.from({ length: 10 }, (_, index) => 10 - index).map((score) => (
              <button key={score} disabled={sending} onClick={() => void rate(score)} type="button">
                <strong>{score}</strong>
                <span>{mogNames[score]}</span>
              </button>
            ))}
          </div>
          <div className="current-score">Сейчас: {candidate.mog.average.toFixed(1)}/10 · {candidate.mog.count} оценок</div>
        </>
      )}
    </section>
  )
}

function LeaderboardScreen() {
  const [gender, setGender] = useState<SearchGender>('any')
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    api.leaderboard(gender)
      .then((rows) => { if (active) setEntries(rows) })
      .catch((err) => { if (active) setError(errorText(err)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [gender])

  return (
    <section className="screen">
      <ScreenHeader eyebrow="LEADERBOARD" title="Рейтинг MOG" subtitle="Battle Elo показывает сравнительную силу, а не среднюю оценку 1–10." />
      <div className="segmented">
        {([['any', 'Все'], ['male', 'Парни'], ['female', 'Девушки']] as const).map(([value, label]) => (
          <button className={gender === value ? 'active' : ''} key={value} onClick={() => setGender(value)}>{label}</button>
        ))}
      </div>
      {loading && <StateCard>Считаем таблицу…</StateCard>}
      {!loading && error && <StateCard>{error}</StateCard>}
      {!loading && !error && entries.length === 0 && <StateCard>Пока нет анкет для рейтинга.</StateCard>}
      <div className="leaderboard-list">
        {entries.map((entry, index) => (
          <div className="leaderboard-row" key={entry.user_id}>
            <span className="rank">{entry.calibrating ? '•' : `#${entry.rank ?? index + 1}`}</span>
            <div className="leader-copy">
              <strong>{entry.name}, {entry.age}</strong>
              <small>{entry.calibrating ? `Калибровка ${entry.battles}/10` : `${entry.wins}W · ${entry.losses}L · top ${entry.percentile ?? '—'}%`}</small>
            </div>
            <b>{entry.elo}</b>
          </div>
        ))}
      </div>
    </section>
  )
}

function MatchesScreen() {
  const [matches, setMatches] = useState<MatchItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    api.matches()
      .then((rows) => { if (active) setMatches(rows) })
      .catch((err) => { if (active) setError(errorText(err)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  return (
    <section className="screen">
      <ScreenHeader eyebrow="MATCHES" title="Ваши матчи" subtitle="Здесь появляются принятые запросы. Новые запросы и уведомления пока остаются в боте." />
      {loading && <StateCard>Загружаем матчи…</StateCard>}
      {!loading && error && <StateCard>{error}</StateCard>}
      {!loading && !error && matches.length === 0 && <StateCard><b>Матчей пока нет</b><span>Взаимно оцените друг друга в основном MOG-фиде и отправьте запрос через бота.</span></StateCard>}
      <div className="match-list">
        {matches.map((match) => (
          <a className="match-row" href={match.contact_url} key={match.user_id}>
            <div>
              <strong>{match.name}, {match.age}</strong>
              <span>{match.city || 'Город не указан'}</span>
            </div>
            <b>Открыть ↗</b>
          </a>
        ))}
      </div>
    </section>
  )
}

function ProfileScreen({ me }: { me: MeResponse }) {
  const photo = usePhoto(me.profile.user_id)
  const winrate = me.battle.battles ? Math.round((me.battle.wins / me.battle.battles) * 100) : 0
  return (
    <section className="screen">
      <ScreenHeader eyebrow="PROFILE" title="Твоя MOG-карточка" subtitle="Два независимых рейтинга: средняя оценка и сравнительный Battle Elo." />
      <div className="profile-hero">
        <div className="profile-avatar">{photo ? <img src={photo} alt={me.profile.name} /> : <div className="photo-placeholder">MOG</div>}</div>
        <div>
          <h2>{me.profile.name}, {me.profile.age}</h2>
          <p>{me.profile.city || 'Город не указан'}</p>
        </div>
      </div>
      <div className="stats-grid">
        <div><span>MOG Score</span><b>{me.mog.average.toFixed(1)}/10</b><small>{me.mog.count} оценок</small></div>
        <div><span>Battle Elo</span><b>{me.battle.elo}</b><small>{me.battle.calibrating ? `Калибровка ${me.battle.battles}/10` : `${me.battle.battles} баттлов`}</small></div>
        <div><span>Победы</span><b>{me.battle.wins}</b><small>{winrate}% winrate</small></div>
        <div><span>Поражения</span><b>{me.battle.losses}</b><small>{me.battle.battles} всего</small></div>
      </div>
      <div className="profile-note">Редактирование анкеты, включение/отключение и фото пока остаются в Telegram-боте — данные уже общие с Mini App.</div>
    </section>
  )
}

const navItems: Array<{ id: Tab; icon: string; label: string }> = [
  { id: 'battle', icon: '⚔️', label: 'Battle' },
  { id: 'rate', icon: '🔥', label: 'Оценка' },
  { id: 'leaderboard', icon: '🏆', label: 'Рейтинг' },
  { id: 'matches', icon: '💘', label: 'Матчи' },
  { id: 'profile', icon: '👤', label: 'Профиль' },
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
    return <main className="boot"><div className="logo-mark">M</div><b>Mogaem</b><span>Загружаем твой рейтинг…</span></main>
  }

  if (error && !me) {
    return (
      <main className="boot error-boot">
        <div className="logo-mark">!</div>
        <b>Mini App не открылся</b>
        <span>{error}</span>
        <button onClick={() => window.location.reload()}>Попробовать снова</button>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <main className="content">{screen}</main>
      <nav className="bottom-nav">
        {navItems.map((item) => (
          <button
            className={tab === item.id ? 'active' : ''}
            key={item.id}
            onClick={() => { setTab(item.id); haptic('select') }}
            type="button"
          >
            <span>{item.icon}</span>
            <small>{item.label}</small>
          </button>
        ))}
      </nav>
    </div>
  )
}
