import type {
  BattleResponse,
  BattleVoteResponse,
  LeaderboardEntry,
  MatchItem,
  MeResponse,
  RatingCandidateResponse,
  SearchGender,
} from './types'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function telegramInitData(): string {
  return window.Telegram?.WebApp?.initData ?? ''
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T | null> {
  const initData = telegramInitData()
  if (!initData) {
    throw new ApiError(401, 'Открой Mogaem через кнопку в Telegram-боте')
  }

  const headers = new Headers(init.headers)
  headers.set('Authorization', `tma ${initData}`)
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(path, { ...init, headers })
  if (response.status === 204) {
    return null
  }
  if (!response.ok) {
    let message = `Ошибка ${response.status}`
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // Keep status fallback.
    }
    throw new ApiError(response.status, message)
  }
  return (await response.json()) as T
}

export const api = {
  me: async () => (await request<MeResponse>('/api/me')) as MeResponse,

  nextBattle: async () => request<BattleResponse>('/api/battle/next'),

  voteBattle: async (battleId: string, winnerId: number) =>
    (await request<BattleVoteResponse>(`/api/battle/${battleId}/vote`, {
      method: 'POST',
      body: JSON.stringify({ winner_id: winnerId }),
    })) as BattleVoteResponse,

  leaderboard: async (gender: SearchGender) => {
    const body = (await request<{ entries: LeaderboardEntry[] }>(
      `/api/leaderboard?gender=${encodeURIComponent(gender)}`,
    )) as { entries: LeaderboardEntry[] }
    return body.entries
  },

  nextRating: async () => request<RatingCandidateResponse>('/api/rate/next'),

  rate: async (targetId: number, score: number) =>
    request<{ target_id: number; score: number }>(`/api/rate/${targetId}`, {
      method: 'POST',
      body: JSON.stringify({ score }),
    }),

  matches: async () => {
    const body = (await request<{ matches: MatchItem[] }>('/api/matches')) as { matches: MatchItem[] }
    return body.matches
  },

  photoBlobUrl: async (userId: number, position = 0) => {
    const initData = telegramInitData()
    if (!initData) throw new ApiError(401, 'Открой Mogaem через Telegram')
    const response = await fetch(`/api/profiles/${userId}/photo/${position}`, {
      headers: { Authorization: `tma ${initData}` },
    })
    if (!response.ok) throw new ApiError(response.status, 'Не удалось загрузить фото')
    return URL.createObjectURL(await response.blob())
  },
}
