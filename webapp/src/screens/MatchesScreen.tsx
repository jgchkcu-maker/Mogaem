import { useEffect, useState } from 'react'
import { CaretRight, Heart, Warning } from '@phosphor-icons/react'
import { api } from '../api'
import type { MatchItem } from '../types'
import { errorText } from '../lib'
import { Avatar } from '../photo'
import { LoadingLabel, ScreenHeader, Skeleton, StateBlock } from '../ui'

export function MatchesScreen() {
  const [matches, setMatches] = useState<MatchItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    api
      .matches()
      .then((rows) => {
        if (active) setMatches(rows)
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
  }, [reloadToken])

  return (
    <section className="screen">
      <ScreenHeader
        title="Ваши матчи"
        subtitle="Здесь появляются принятые запросы. Новые запросы и уведомления пока остаются в боте."
      />
      {loading && (
        <div className="match-list" aria-busy="true">
          <LoadingLabel text="Загружаем матчи" />
          {Array.from({ length: 3 }, (_, row) => (
            <div className="match-row" key={row} aria-hidden="true">
              <Skeleton className="skeleton-row-avatar" />
              <div className="match-copy">
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
      {!loading && !error && matches.length === 0 && (
        <StateBlock
          icon={Heart}
          title="Матчей пока нет"
          body="Взаимно оцените друг друга в MOG-фиде и отправьте запрос через бота."
        />
      )}
      {!loading && !error && matches.length > 0 && (
        <div className="match-list">
          {matches.map((match) => (
            <a className="match-row" href={match.contact_url} key={match.user_id}>
              <Avatar userId={match.user_id} name={match.name} />
              <div className="match-copy">
                <strong>
                  {match.name}, {match.age}
                </strong>
                <span>{match.city || 'Город не указан'}</span>
              </div>
              <CaretRight size={16} weight="bold" className="row-chevron" aria-hidden={true} />
            </a>
          ))}
        </div>
      )}
    </section>
  )
}
