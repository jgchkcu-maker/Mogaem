import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'

// Appearance follows the Telegram client color scheme (official WebApp
// recommendation); outside Telegram it falls back to the OS setting. The
// palette itself is Mogaem's Apple-HIG system: raw themeParams are not
// consumed, because user-made Telegram themes would break the design.
function systemScheme(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const tg = window.Telegram?.WebApp

function applyScheme() {
  const scheme = tg?.colorScheme === 'light' || tg?.colorScheme === 'dark' ? tg.colorScheme : systemScheme()
  document.documentElement.dataset.scheme = scheme
  // Chrome color matches systemBackground of the active appearance.
  const chrome = scheme === 'dark' ? '#000000' : '#f2f2f7'
  try {
    tg?.setHeaderColor?.(chrome)
    tg?.setBackgroundColor?.(chrome)
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
applyScheme()
syncSafeAreaInsets()

// Insets and appearance arrive only after the viewport settles and change on
// rotation or Telegram UI updates, so listen instead of reading them once.
for (const event of ['safeAreaChanged', 'contentSafeAreaChanged', 'viewportChanged'] as const) {
  tg?.onEvent?.(event, syncSafeAreaInsets)
}
tg?.onEvent?.('themeChanged', applyScheme)
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyScheme)

const root = document.getElementById('root')
if (!root) throw new Error('Mini App root element is missing')

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
