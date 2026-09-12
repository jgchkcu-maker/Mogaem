import { useCallback, useEffect, useState, type CSSProperties } from 'react'
import { Checks, Warning } from '@phosphor-icons/react'
import { api } from '../api'
import type { RatingCandidateResponse } from '../types'
import { errorText, haptic, plural } from '../lib'
import { Photo } from '../photo'
import { LoadingLabel, ScreenHeader, Skeleton, StateBlock } from '../ui'

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

// Tier hue walks from red (score 1) to acid lime (score 10).
function tierHue(score: number): number {
  return Math.round(4 + ((score - 1) / 9) * 72)
}

export function RateScreen({ onStatsChanged }: { onStatsChanged: () => Promise<void> }) {
  const [candidate, setCandidate] = useState<RatingCandidateResponse | null>(null)
  const [score, setScore] = useState(5)
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

  useEffect(() => {
    void load()
  }, [load])

  const rate = async () => {
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
      <ScreenHeader
        title="Оцени внешность"
        subtitle="Оценка 1-10 идёт в средний MOG Score и не смешивается с Battle Elo."
      />
      {loading && (
        <div aria-busy="true">
          <div className="rate-hero" aria-hidden="true">
            <Skeleton className="skeleton-fill" />
          </div>
          <div className="rate-panel" aria-hidden="true">
            <Skeleton className="skeleton-line" />
            <Skeleton className="skeleton-slider" />
            <Skeleton className="skeleton-button" />
          </div>
          <LoadingLabel text="Ищем следующую анкету" />
        </div>
      )}
      {!loading && error && (
        <StateBlock
          icon={Warning}
          title="Ошибка"
          body={error}
          action="Повторить"
          onAction={() => void load()}
        />
      )}
      {!loading && !error && !candidate && (
        <StateBlock
          icon={Checks}
          title="Ты всё оценил"
          body="Новые анкеты появятся здесь автоматически."
        />
      )}
      {!loading && candidate && (
        <>
          <div className="rate-hero">
            <Photo userId={candidate.profile.user_id} alt={candidate.profile.name} className="rate-photo">
              <div className="photo-scrim" aria-hidden="true" />
              <div className="stat-chip">
                {candidate.mog.average.toFixed(1)}/10 · {candidate.mog.count}{' '}
                {plural(candidate.mog.count, 'оценка', 'оценки', 'оценок')}
              </div>
              <div className="rate-copy">
                <strong>
                  {candidate.profile.name}, {candidate.profile.age}
                </strong>
                <span>{candidate.profile.city || 'Город не указан'}</span>
              </div>
            </Photo>
          </div>
          <div className="rate-panel">
            <div className="score-readout" style={{ '--tier-hue': tierHue(score) } as CSSProperties}>
              <b>{score}</b>
              <span className="tier">{mogNames[score]}</span>
            </div>
            <input
              className="score-slider"
              type="range"
              min={1}
              max={10}
              step={1}
              value={score}
              disabled={sending}
              aria-label="Оценка внешности"
              aria-valuetext={`${score} из 10 — ${mogNames[score]}`}
              style={{ '--val': `${((score - 1) / 9) * 100}%` } as CSSProperties}
              onChange={(event) => {
                const next = Number(event.target.value)
                if (next !== score) {
                  setScore(next)
                  haptic('select')
                }
              }}
            />
            <button className="rate-submit" disabled={sending} onClick={() => void rate()} type="button">
              {sending ? 'Отправляем…' : `Оценить на ${score}`}
            </button>
          </div>
        </>
      )}
    </section>
  )
}
