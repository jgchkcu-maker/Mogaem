import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const app = await readFile(new URL('../src/App.tsx', import.meta.url), 'utf8')
const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')
const bootstrap = await readFile(new URL('../src/main.tsx', import.meta.url), 'utf8')

test('navigation uses a dedicated Liquid Glass functional layer', () => {
  assert.match(app, /className="bottom-nav liquid-glass"/)
  assert.match(styles, /\.liquid-glass\s*\{/)
  assert.match(styles, /--glass-regular-fill:/)
  assert.match(styles, /--glass-specular:/)
  assert.match(styles, /-webkit-backdrop-filter:/)
  assert.match(styles, /backdrop-filter:/)
})

test('interactive controls use glass styling without turning content cards into glass', () => {
  assert.match(app, /className="segmented glass-control"/)
  assert.match(app, /className="score-button glass-control"/)
  assert.match(styles, /\.glass-control\s*\{/)
  assert.match(styles, /\.content-surface\s*\{/)
})

test('the UI has accessibility fallbacks for transparency and motion', () => {
  assert.match(styles, /@media \(prefers-reduced-transparency: reduce\)/)
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/)
})

test('bottom navigation uses vector icons rather than emoji glyphs', () => {
  assert.match(app, /function NavIcon/)
  assert.doesNotMatch(app, /icon: '[⚔🔥🏆💘👤️]'/u)
})

test('safe areas combine CSS env() with synchronized Telegram insets', () => {
  assert.match(styles, /--safe-top:.*max\(env\(safe-area-inset-top/)
  assert.match(styles, /--safe-bottom:.*max\(env\(safe-area-inset-bottom/)
  assert.match(styles, /var\(--tg-safe-top/)
  assert.match(styles, /var\(--tg-content-safe-top/)
  assert.match(bootstrap, /safeAreaChanged/)
  assert.match(bootstrap, /contentSafeAreaChanged/)
  assert.match(bootstrap, /syncSafeAreaInsets/)
})

test('the product is deliberately dark-only and does not follow Telegram themes', () => {
  assert.match(styles, /color-scheme: dark/)
  assert.doesNotMatch(styles, /--tg-theme-/)
  assert.match(bootstrap, /themeChanged/)
})

test('leaderboard and matches reuse the authenticated photo proxy for avatars', () => {
  assert.match(app, /function Avatar/)
  assert.match(app, /<Avatar userId=\{entry\.user_id\} \/>/)
  assert.match(app, /<Avatar userId=\{match\.user_id\} \/>/)
  assert.match(app, /api\.photoBlobUrl/)
})
