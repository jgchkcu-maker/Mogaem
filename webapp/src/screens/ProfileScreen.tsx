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
      <div className="profile-hero">
        <Photo userId={me.profile.user_id} alt={me.profile.name} className="profile-avatar" />
        <div>
          <h2>
            {me.profile.name}, {me.profile.age}
          </h2>
          <p>{me.profile.city || 'Город не указан'}</p>
        </div>
      </div>
      <div className="profile-duel">
        <div className="duel-cell">
          <span>MOG Score</span>
          <b>
            {me.mog.average.toFixed(1)}
            <small> /10</small>
          </b>
          <small>
            {me.mog.count} {plural(me.mog.count, 'оценка', 'оценки', 'оценок')}
          </small>
        </div>
        <div className="duel-divider" aria-hidden="true" />
        <div className="duel-cell">
          <span>Battle Elo</span>
          <b>{me.battle.elo}</b>
          <small>
            {me.battle.calibrating
              ? `Калибровка ${me.battle.battles}/10`
              : `${me.battle.battles} ${plural(me.battle.battles, 'баттл', 'баттла', 'баттлов')}`}
          </small>
        </div>
      </div>
      <div className="battle-record">
        <div>
          <b>{me.battle.wins}</b>
          <span>победы</span>
        </div>
        <div>
          <b>{me.battle.losses}</b>
          <span>поражения</span>
        </div>
        <div className="record-winrate">
          <b>{winrate}%</b>
          <span>winrate</span>
        </div>
      </div>
      <p className="profile-note">
        <Info size={15} aria-hidden={true} />
        Редактирование анкеты и фото пока в Telegram-боте. Данные общие с Mini App.
      </p>
    </section>
  )
}
