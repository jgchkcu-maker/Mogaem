import { useEffect, useState } from 'react'
import { Trophy, Warning } from '@phosphor-icons/react'
import { api } from '../api'
import type { LeaderboardEntry, SearchGender } from '../types'
import { errorText } from '../lib'
import { Avatar } from '../photo'
import { LoadingLabel, ScreenHeader, Skeleton, StateBlock } from '../ui'

export function LeaderboardScreen() {
  const [gender, setGender] = useState<SearchGender>('any')
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    api
      .leaderboard(gender)
      .then((rows) => {
        if (active) setEntries(rows)
      })
      .catch((err) => {
        if (active) setError(errorText(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [gender, reloadToken])

  const podiumClass = (entry: LeaderboardEntry) => {
    if (entry.calibrating || !entry.rank || entry.rank > 3) return ''
    return ` podium-${entry.rank}`
  }

  return (
    <section className="screen">
      <ScreenHeader
        title={
          <>
            Рейтинг <span className="tone-accent">MOG</span>
          </>
        }
        subtitle={
          <>
            <b>Battle Elo</b> показывает сравнительную силу, а не среднюю оценку 1-10.
          </>
        }
      />
      <div className="segmented" role="group" aria-label="Фильтр рейтинга">
        {(
          [
            ['any', 'Все'],
            ['male', 'Парни'],
            ['female', 'Девушки'],
          ] as const
        ).map(([value, label]) => (
          <button
            className={gender === value ? 'active' : ''}
            key={value}
            onClick={() => setGender(value)}
            type="button"
            aria-pressed={gender === value}
          >
            {label}
          </button>
        ))}
      </div>
      {loading && (
        <div className="leaderboard-list" aria-busy="true">
          <LoadingLabel text="Считаем таблицу" />
          {Array.from({ length: 6 }, (_, row) => (
            <div className="leaderboard-row" key={row} aria-hidden="true">
              <Skeleton className="skeleton-rank" />
              <Skeleton className="skeleton-row-avatar" />
              <div className="leader-copy">
                <Skeleton className="skeleton-line" />
                <Skeleton className="skeleton-line short" />
              </div>
            </div>
          ))}
        </div>
      )}
      {!loading && error && (
        <StateBlock
          icon={Warning}
          title="Не загрузилось"
          body={error}
          action="Повторить"
          onAction={() => setReloadToken((token) => token + 1)}
        />
      )}
      {!loading && !error && entries.length === 0 && (
        <StateBlock icon={Trophy} title="Пока пусто" body="Сыграй пару битв, чтобы открыть рейтинг." />
      )}
      {!loading && !error && entries.length > 0 && (
        <div className="leaderboard-list">
          {entries.map((entry, index) => (
            <div
              className={`leaderboard-row${podiumClass(entry)}`}
              key={entry.user_id}
              style={{ animationDelay: `${Math.min(index, 8) * 30}ms` }}
            >
              <span className="rank">{entry.calibrating ? '-' : `#${entry.rank ?? index + 1}`}</span>
              <Avatar userId={entry.user_id} name={entry.name} />
              <div className="leader-copy">
                <strong>
                  {entry.name}, {entry.age}
                </strong>
                <small>
                  {entry.calibrating
                    ? `Калибровка ${entry.battles}/10`
                    : `${entry.wins}W · ${entry.losses}L${
                        entry.percentile == null ? '' : `, top ${entry.percentile}%`
                      }`}
                </small>
              </div>
              <b className="leader-elo">{entry.elo}</b>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
