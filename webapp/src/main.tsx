import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'

// Mogaem is deliberately dark-only: the Liquid Glass palette in styles.css is
// tuned for dark surfaces, so Telegram light themes must not re-map it.
const BRAND_BG = '#090b10'

const tg = window.Telegram?.WebApp

function applyChromeColor() {
  try {
    tg?.setHeaderColor?.(BRAND_BG)
    tg?.setBackgroundColor?.(BRAND_BG)
  } catch {
    // Older Telegram clients can ignore explicit color setters.
  }
}

function syncSafeAreaInsets() {
  if (!tg) return
  const rootStyle = document.documentElement.style
  const safe = tg.safeAreaInset
  const contentSafe = tg.contentSafeAreaInset
  rootStyle.setProperty('--tg-safe-top', `${safe?.top ?? 0}px`)
  rootStyle.setProperty('--tg-safe-right', `${safe?.right ?? 0}px`)
  rootStyle.setProperty('--tg-safe-bottom', `${safe?.bottom ?? 0}px`)
  rootStyle.setProperty('--tg-safe-left', `${safe?.left ?? 0}px`)
  rootStyle.setProperty('--tg-content-safe-top', `${contentSafe?.top ?? 0}px`)
}

tg?.ready()
tg?.expand()
applyChromeColor()
syncSafeAreaInsets()

// Insets arrive only after the viewport settles and change on rotation or
// Telegram UI updates, so listen instead of reading them once.
for (const event of ['safeAreaChanged', 'contentSafeAreaChanged', 'viewportChanged'] as const) {
  tg?.onEvent?.(event, syncSafeAreaInsets)
}
tg?.onEvent?.('themeChanged', applyChromeColor)

const root = document.getElementById('root')
if (!root) throw new Error('Mini App root element is missing')

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
