import { useCallback, useEffect, useState } from 'react'
import { Sword, Warning } from '@phosphor-icons/react'
import { api } from '../api'
import type { BattlePlayer, BattleResponse } from '../types'
import { errorText, haptic } from '../lib'
import { Photo } from '../photo'
import { LoadingLabel, ScreenHeader, Skeleton, StateBlock } from '../ui'

type CardState = 'idle' | 'won' | 'lost'

function PlayerCard({
  player,
  onChoose,
  disabled,
  state,
}: {
  player: BattlePlayer
  onChoose: () => void
  disabled: boolean
  state: CardState
}) {
  return (
    <button
      className={`battle-card${state === 'won' ? ' won' : state === 'lost' ? ' lost' : ''}`}
      onClick={onChoose}
      disabled={disabled}
      type="button"
    >
      <Photo userId={player.user_id} alt={player.name} className="battle-photo">
        <div className="photo-scrim" aria-hidden="true" />
        <div className="elo-chip">{player.elo} ELO</div>
        <div className="battle-copy">
          <strong>{player.name}</strong>
          <span>
            {player.age} · {player.city || 'Город не указан'}
          </span>
          <small>
            {player.calibrating ? `Калибровка ${player.battles}/10` : `${player.wins}W · ${player.losses}L`}
          </small>
        </div>
      </Photo>
    </button>
  )
}

export function BattleScreen({ onStatsChanged }: { onStatsChanged: () => Promise<void> }) {
  const [battle, setBattle] = useState<BattleResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [voting, setVoting] = useState(false)
  const [votedFor, setVotedFor] = useState<number | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setMessage(null)
    setVotedFor(null)
    setVoting(false)
    try {
      setBattle(await api.nextBattle())
    } catch (err) {
      setError(errorText(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const vote = async (winnerId: number) => {
    if (!battle || voting) return
    setVoting(true)
    setVotedFor(winnerId)
    haptic('select')
    try {
      const before = winnerId === battle.left.user_id ? battle.left.elo : battle.right.elo
      const result = await api.voteBattle(battle.battle_id, winnerId)
      const delta = result.winner.elo - before
      setMessage(`${result.winner.name} MOG’ает · +${delta} ELO`)
      haptic('success')
      await onStatsChanged()
      // Stay disabled until the next pair replaces this one so a fast second
      // tap cannot re-submit the same battle.
      window.setTimeout(() => {
        void load()
      }, 950)
    } catch (err) {
      setError(errorText(err))
      haptic('error')
      setVoting(false)
      setVotedFor(null)
    }
  }

  const cardState = (player: BattlePlayer): CardState => {
    if (votedFor == null) return 'idle'
    return votedFor === player.user_id ? 'won' : 'lost'
  }

  return (
    <section className="screen">
      <ScreenHeader
        title={
          <>
            Кто <span className="tone-accent">MOG’ает?</span>
          </>
        }
        subtitle={
          <>
            Выбери сильнейшую внешку. <b>Elo</b> пересчитается сразу.
          </>
        }
      />
      {loading && (
        <div className="battle-grid" aria-busy="true">
          <LoadingLabel text="Ищем следующую пару" />
          {[0, 1].map((side) => (
            <div className="battle-card" key={side} aria-hidden="true">
              <div className="battle-photo">
                <Skeleton className="skeleton-fill" />
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
          onAction={() => void load()}
        />
      )}
      {!loading && !error && !battle && (
        <StateBlock
          icon={Sword}
          title="Пары закончились"
          body="Нужны ещё активные анкеты одного пола или новые сочетания. Загляни позже."
        />
      )}
      {!loading && battle && (
        <div className="battle-grid">
          <PlayerCard
            player={battle.left}
            disabled={voting}
            state={cardState(battle.left)}
            onChoose={() => void vote(battle.left.user_id)}
          />
          <div className="versus" aria-hidden="true">
            VS
          </div>
          <PlayerCard
            player={battle.right}
            disabled={voting}
            state={cardState(battle.right)}
            onChoose={() => void vote(battle.right.user_id)}
          />
          <div className={`battle-toast${message ? ' result' : ''}`} aria-live="polite">
            {message || ''}
          </div>
        </div>
      )}
    </section>
  )
}
