import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const app = await readFile(new URL('../src/App.tsx', import.meta.url), 'utf8')
const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')
const bootstrap = await readFile(new URL('../src/main.tsx', import.meta.url), 'utf8')
const html = await readFile(new URL('../index.html', import.meta.url), 'utf8')
const photo = await readFile(new URL('../src/photo.tsx', import.meta.url), 'utf8')
const battle = await readFile(new URL('../src/screens/BattleScreen.tsx', import.meta.url), 'utf8')
const rate = await readFile(new URL('../src/screens/RateScreen.tsx', import.meta.url), 'utf8')
const leaderboard = await readFile(new URL('../src/screens/LeaderboardScreen.tsx', import.meta.url), 'utf8')
const matches = await readFile(new URL('../src/screens/MatchesScreen.tsx', import.meta.url), 'utf8')
const profile = await readFile(new URL('../src/screens/ProfileScreen.tsx', import.meta.url), 'utf8')

function cssBlocks(source) {
  const blocks = []
  for (const match of source.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    blocks.push({ selector: match[1].trim(), body: match[2] })
  }
  return blocks
}

test('typography is the Mogaem identity: Unbounded display + Golos Text UI, self-hosted', () => {
  assert.match(bootstrap, /@fontsource\/golos-text\/400\.css/)
  assert.match(bootstrap, /@fontsource\/golos-text\/500\.css/)
  assert.match(bootstrap, /@fontsource\/golos-text\/600\.css/)
  assert.match(bootstrap, /@fontsource\/unbounded\/600\.css/)
  assert.match(bootstrap, /@fontsource\/unbounded\/700\.css/)
  assert.match(styles, /--font-display: 'Unbounded', 'Golos Text'/)
  assert.match(styles, /--font-text: 'Golos Text'/)
  // The old per-platform system stack is no longer the primary face.
  assert.doesNotMatch(styles, /font-family: -apple-system/)
})

test('both appearances ship the arena palette with the single hot accent', () => {
  assert.match(styles, /--accent: #ff6d29/) // light
  assert.match(styles, /--accent: #ff6d29/) // dark
  assert.match(styles, /--accent-ink: #161316/)
  assert.match(styles, /--accent-text: #b8410c/) // light: darkened orange for contrast
  assert.match(styles, /--bg: #f4f2ee/) // light warm off-white
  assert.match(styles, /--bg: #161316/) // dark warm near-black
  assert.match(styles, /--label: #1b161a/)
  assert.match(styles, /--label: #f5f2f0/)
  // Brown is a spot tone, never the page base.
  assert.match(styles, /--brown: #453027/)
  assert.match(styles, /--seg-thumb: #453027/)
  assert.match(styles, /data-scheme='dark'/)
  // The palette is Mogaem's: no stock iOS tints, no raw Telegram themes,
  // and the previous lime identity is gone.
  assert.doesNotMatch(styles, /007aff|0a84ff|c9f24b/)
  assert.doesNotMatch(styles, /--tg-theme-/)
})

test('appearance switches with the Telegram client and falls back to the OS', () => {
  assert.match(bootstrap, /colorScheme/)
  assert.match(bootstrap, /dataset\.scheme/)
  assert.match(bootstrap, /themeChanged/)
  assert.match(bootstrap, /prefers-color-scheme: dark/)
  // Chrome colors match the page backgrounds of both appearances.
  assert.match(bootstrap, /#161316/)
  assert.match(bootstrap, /#f4f2ee/)
})

test('index.html chrome matches the tokens', () => {
  assert.match(html, /content="#f4f2ee"/)
  assert.match(html, /content="#161316"/)
  assert.match(html, /fill='%23ff6d29'/)
  assert.match(html, /fill='%23161316'/)
})

test('gradients are reserved for photo scrims and the slider track', () => {
  const blocks = cssBlocks(styles)
  const withGradients = blocks.filter((block) => /(linear|radial|conic)-gradient\(/.test(block.body))
  assert.ok(withGradients.length >= 2, 'expected scrim + slider track gradients')
  for (const block of withGradients) {
    assert.match(
      block.selector,
      /photo-scrim|slider-runnable-track/,
      `gradient in unexpected block: ${block.selector}`,
    )
  }
})

test('corner radii stay inside the documented scale', () => {
  // 0 = square corner of a split panel, 10 small elements, 14 buttons/avatars,
  // 20 cards/logo mark, 999 capsules.
  const allowed = new Set(['0', '10px', '14px', '20px', '999px'])
  const radii = [...styles.matchAll(/border-radius:\s*([^;]+);/g)].map((match) => match[1].trim())
  assert.ok(radii.length > 0, 'expected explicit border-radius declarations')
  for (const radius of radii) {
    for (const token of radius.split(/\s+/)) {
      assert.ok(allowed.has(token), `unexpected radius "${token}" in "${radius}", allowed: ${[...allowed].join(', ')}`)
    }
  }
})

test('transitions interpolate and never use linear or ease-in-out', () => {
  const transitions = [...styles.matchAll(/transition:[^;]+;/g)].map((match) => match[0])
  assert.ok(transitions.length > 0, 'expected explicit transition declarations')
  for (const transition of transitions) {
    assert.doesNotMatch(transition, /ease-in-out/)
    assert.doesNotMatch(transition, /[\s:,]all[\s,;]/)
    assert.match(transition, /ease-out|var\(--ease\)/)
  }
})

test('the UI has a reduced-motion fallback and visible focus', () => {
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/)
  assert.match(styles, /:focus-visible/)
})

test('boot screen carries the cropped brand wordmark as texture', () => {
  assert.match(styles, /content: "MOGAEM"/)
  assert.match(styles, /opacity: 0\.05/)
})

test('rating is a discrete slider with live tier feedback, not a button wall', () => {
  assert.match(rate, /type="range"/)
  assert.match(rate, /min=\{1\}/)
  assert.match(rate, /max=\{10\}/)
  assert.match(rate, /aria-valuetext=/)
  assert.match(rate, /mogNames\[/)
  assert.match(rate, /score-slider/)
  assert.match(rate, /rate-submit/)
  // Haptic tick on every step change.
  assert.match(rate, /haptic\('select'\)/)
  // No wall of ten buttons.
  assert.doesNotMatch(rate, /score-button/)
  const slider = styles.match(/\.score-slider \{[\s\S]*?\}/)?.[0] ?? ''
  assert.match(slider, /appearance: none/)
  // Primary pill CTAs carry a circular icon orb.
  assert.match(rate, /btn-orb/)
  assert.match(rate, /ArrowRight/)
  assert.match(styles, /\.btn-orb/)
})

test('two-tone headlines carry the identity', () => {
  assert.match(battle, /tone-accent/)
  assert.match(rate, /tone-dim/)
  assert.match(leaderboard, /tone-accent/)
  assert.match(profile, /tone-accent/)
  assert.match(styles, /\.tone-accent/)
  assert.match(styles, /\.tone-dim/)
  // Subtitles emphasize product terms.
  assert.match(rate, /<b>MOG Score<\/b>/)
  assert.match(leaderboard, /<b>Battle Elo<\/b>/)
})

test('battle verdict is announced and accent-marked', () => {
  assert.match(battle, /battle-toast/)
  assert.match(battle, /aria-live="polite"/)
  assert.match(battle, /battle-card\.won|className=\{`battle-card\$\{/) // won/lost states
  assert.match(battle, /'won' : 'lost'/)
})

test('bottom navigation uses a vector icon library, not emoji glyphs', () => {
  assert.match(app, /@phosphor-icons\/react/)
  assert.match(app, /function NavIcon/)
  assert.doesNotMatch(app, /icon: '[⚔🔥🏆💘👤️]'/u)
})

test('matches disclose navigation with a circular arrow chip', () => {
  assert.match(matches, /row-orb/)
  assert.match(matches, /ArrowUpRight/)
})

test('leaderboard highlights the podium with semantic metals only', () => {
  assert.match(leaderboard, /podium-\$\{entry\.rank\}/)
  assert.match(styles, /--silver:/)
  assert.match(styles, /--bronze:/)
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

test('leaderboard and matches reuse the authenticated photo proxy for avatars', () => {
  assert.match(photo, /export function Avatar/)
  assert.match(leaderboard, /<Avatar userId=\{entry\.user_id\} name=\{entry\.name\} \/>/)
  assert.match(matches, /<Avatar userId=\{match\.user_id\} name=\{match\.name\} \/>/)
  assert.match(photo, /api\.photoBlobUrl/)
})

test('translucent material is reserved for the tab bar', () => {
  const navBlock = styles.match(/\.bottom-nav \{[\s\S]*?\}/)?.[0] ?? ''
  assert.match(navBlock, /backdrop-filter/)
  // every backdrop-filter occurrence is either the tab bar (with webkit
  // prefix) or the @supports guard that provides the opaque fallback
  for (const match of styles.matchAll(/backdrop-filter/g)) {
    const { index } = match
    const inNav = index !== undefined && index >= styles.indexOf('.bottom-nav {') && index <= styles.indexOf('.bottom-nav {') + navBlock.length
    const inSupports = styles.lastIndexOf('@supports', index) > styles.lastIndexOf('}', index)
    assert.ok(inNav || inSupports, 'backdrop-filter used outside the tab bar material')
  }
})

test('data screens fetch through the shared api client; no local state libs', () => {
  // Profile receives `me` from the shell; the other screens fetch themselves.
  for (const source of [battle, rate, leaderboard, matches]) {
    assert.match(source, /from '\.\.\/api'/)
  }
  assert.doesNotMatch(app, /from '(zustand|jotai|redux|@reduxjs|framer-motion|motion\/react)'/)
})
