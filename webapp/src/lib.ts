import { ApiError } from './api'

export function haptic(kind: 'select' | 'success' | 'error' = 'select') {
  const feedback = window.Telegram?.WebApp?.HapticFeedback
  if (!feedback) return
  if (kind === 'select') feedback.selectionChanged()
  else feedback.notificationOccurred(kind)
}

export function errorText(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message
  return 'Что-то пошло не так'
}

/** Russian plural: plural(32, 'оценка', 'оценки', 'оценок') -> 'оценки'. */
export function plural(count: number, one: string, few: string, many: string): string {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few
  return many
}
