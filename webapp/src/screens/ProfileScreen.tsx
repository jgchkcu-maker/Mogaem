import { Info } from '@phosphor-icons/react'
import type { MeResponse } from '../types'
import { plural } from '../lib'
import { Photo } from '../photo'
import { ScreenHeader } from '../ui'

export function ProfileScreen({ me }: { me: MeResponse }) {
  const winrate = me.battle.battles ? Math.round((me.battle.wins / me.battle.battles) * 100) : 0
  return (
    <section className="screen">
      <ScreenHeader
        title={
          <>
            Твоя <span className="tone-accent">MOG-карточка</span>
          </>
        }
        subtitle={
          <>
            Два независимых рейтинга: средняя оценка и сравнительный <b>Battle Elo</b>.
          </>
        }
      />
      <div className="profile-grid">
        <div className="tile profile-hero">
          <Photo userId={me.profile.user_id} alt={me.profile.name} className="profile-avatar" />
          <div>
            <h2>
              {me.profile.name}, {me.profile.age}
            </h2>
            <p>{me.profile.city || 'Город не указан'}</p>
          </div>
        </div>
        <div className="tile duel-tile tile-accent">
          <span className="tile-label">MOG Score</span>
          <b>
            {me.mog.average.toFixed(1)}
            <small> /10</small>
          </b>
          <small className="tile-sub">
            {me.mog.count} {plural(me.mog.count, 'оценка', 'оценки', 'оценок')}
          </small>
        </div>
        <div className="tile duel-tile tile-brown">
          <span className="tile-label">Battle Elo</span>
          <b>{me.battle.elo}</b>
          <small className="tile-sub">
            {me.battle.calibrating
              ? `Калибровка ${me.battle.battles}/10`
              : `${me.battle.battles} ${plural(me.battle.battles, 'баттл', 'баттла', 'баттлов')}`}
          </small>
        </div>
        <div className="tile stat-tile">
          <b>{me.battle.wins}</b>
          <span className="tile-sub">победы</span>
        </div>
        <div className="tile stat-tile">
          <b>{me.battle.losses}</b>
          <span className="tile-sub">поражения</span>
        </div>
        <div className="tile stat-tile">
          <b className="stat-accent">{winrate}%</b>
          <span className="tile-sub">winrate</span>
        </div>
      </div>
      <p className="profile-note">
        <Info size={15} aria-hidden={true} />
        Редактирование анкеты и фото пока в Telegram-боте. Данные общие с Mini App.
      </p>
    </section>
  )
}
