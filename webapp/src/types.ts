export type Gender = 'male' | 'female'
export type SearchGender = Gender | 'any'

export interface Profile {
  user_id: number
  name: string
  age: number
  gender: Gender
  search_gender: SearchGender
  city: string | null
  bio: string
  photo_count: number
}

export interface MogStats {
  average: number
  count: number
}

export interface BattlePlayer {
  user_id: number
  name: string
  age: number
  gender: Gender
  city: string | null
  elo: number
  battles: number
  wins: number
  losses: number
  calibrating: boolean
  photo_count: number
}

export interface MeResponse {
  profile: Profile
  mog: MogStats
  battle: BattlePlayer
}

export interface BattleResponse {
  battle_id: string
  left: BattlePlayer
  right: BattlePlayer
}

export interface BattleVoteResponse {
  battle_id: string
  winner: BattlePlayer
  loser: BattlePlayer
}

export interface RatingCandidateResponse {
  profile: Profile
  mog: MogStats
}

export interface LeaderboardEntry {
  user_id: number
  name: string
  age: number
  gender: Gender
  city: string | null
  elo: number
  battles: number
  wins: number
  losses: number
  calibrating: boolean
  rank: number | null
  percentile: number | null
}

export interface MatchItem {
  user_id: number
  name: string
  age: number
  city: string | null
  contact_url: string
  created_at: string
}

export interface TelegramInsets {
  top?: number
  right?: number
  bottom?: number
  left?: number
}

export type TelegramWebAppEvent =
  | 'safeAreaChanged'
  | 'contentSafeAreaChanged'
  | 'viewportChanged'
  | 'themeChanged'

export interface TelegramWebApp {
  initData: string
  colorScheme?: 'light' | 'dark'
  ready: () => void
  expand: () => void
  setHeaderColor?: (color: string) => void
  setBackgroundColor?: (color: string) => void
  safeAreaInset?: TelegramInsets
  contentSafeAreaInset?: TelegramInsets
  onEvent?: (event: TelegramWebAppEvent, handler: () => void) => void
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
    selectionChanged: () => void
  }
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp
    }
  }
}
