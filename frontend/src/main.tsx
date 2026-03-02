import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

window.Telegram?.WebApp?.ready?.()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)

const bootLoadingEl = document.getElementById('boot-loading')
if (bootLoadingEl) {
  requestAnimationFrame(() => {
    bootLoadingEl.classList.add('boot-loading--hidden')
    setTimeout(() => bootLoadingEl.remove(), 240)
  })
}
