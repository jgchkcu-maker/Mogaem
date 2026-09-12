import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'

const tg = window.Telegram?.WebApp
tg?.ready()
tg?.expand()
try {
  tg?.setHeaderColor?.('#0b0d12')
  tg?.setBackgroundColor?.('#0b0d12')
} catch {
  // Older Telegram clients can ignore explicit color setters.
}

const root = document.getElementById('root')
if (!root) throw new Error('Mini App root element is missing')

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
