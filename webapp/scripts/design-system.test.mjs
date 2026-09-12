import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const app = await readFile(new URL('../src/App.tsx', import.meta.url), 'utf8')
const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')
const bootstrap = await readFile(new URL('../src/main.tsx', import.meta.url), 'utf8')

test('typography follows HIG: per-platform system fonts, no bundled webfonts', () => {
  assert.match(styles, /font-family: -apple-system, BlinkMacSystemFont/)
  assert.doesNotMatch(styles, /@font-face/)
  assert.doesNotMatch(styles, /\/fonts\//)
  assert.doesNotMatch(styles, /Unbounded|Golos Text|JetBrains Mono/)
})

test('both appearances ship with full iOS system palettes', () => {
  assert.match(styles, /--tint: #007aff/)  // light systemBlue
  assert.match(styles, /--tint: #0a84ff/)  // dark systemBlue
  assert.match(styles, /--bg: #f2f2f7/)    // systemGroupedBackground light
  assert.match(styles, /--bg: #000000/)    // systemBackground dark
  assert.match(styles, /--label: #000000/)
  assert.match(styles, /--label: #ffffff/)
  assert.match(styles, /data-scheme='dark'/)
  // The palette is Mogaem's: raw Telegram theme colors are not consumed.
  assert.doesNotMatch(styles, /--tg-theme-/)
})

test('appearance switches with the Telegram client and falls back to the OS', () => {
  assert.match(bootstrap, /colorScheme/)
  assert.match(bootstrap, /dataset\.scheme/)
  assert.match(bootstrap, /themeChanged/)
  assert.match(bootstrap, /prefers-color-scheme: dark/)
})

test('tint is the single accent; system colors stay semantic', () => {
  assert.doesNotMatch(styles, /7c62ff|ff5a98|cdf34f|ff2a2a/i)
  assert.match(styles, /--red: #/)   // destructive only
  assert.match(styles, /--green: #/) // success only
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

test('corner radii stay inside the documented iOS set', () => {
  // 7px segmented segment, 8px small thumbnails, 9px segmented control,
  // 12px cards/cells, 13px app-icon boot mark, 999px capsule chips
  const allowed = new Set(['7px', '8px', '9px', '12px', '13px', '999px'])
  const radii = [...styles.matchAll(/border-radius:\s*([^;]+);/g)].map((match) => match[1].trim())
  assert.ok(radii.length > 0, 'expected explicit border-radius declarations')
  for (const radius of radii) {
    assert.ok(allowed.has(radius), `unexpected radius "${radius}", allowed: ${[...allowed].join(', ')}`)
  }
})

test('no decorative gradients or glass helpers', () => {
  assert.doesNotMatch(styles, /(linear|radial|conic)-gradient\(/)
  assert.doesNotMatch(styles, /liquid-glass/)
  assert.doesNotMatch(app, /className="[^"]*\bglass/)
})

test('transitions interpolate and never use linear or ease-in-out', () => {
  const transitions = [...styles.matchAll(/transition:[^;]+;/g)].map((match) => match[0])
  assert.ok(transitions.length > 0, 'expected explicit transition declarations')
  for (const transition of transitions) {
    assert.doesNotMatch(transition, /ease-in-out/)
    assert.doesNotMatch(transition, /[\s:,]all[\s,;]/)
    assert.match(transition, /ease-out|var\(--press-ease\)/)
  }
})

test('the UI has a reduced-motion fallback and visible focus', () => {
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/)
  assert.match(styles, /:focus-visible/)
})

test('bottom navigation uses a vector icon library, not emoji glyphs', () => {
  assert.match(app, /@phosphor-icons\/react/)
  assert.match(app, /function NavIcon/)
  assert.doesNotMatch(app, /icon: '[⚔🔥🏆💘👤️]'/u)
})

test('matches disclose navigation with an iOS chevron', () => {
  assert.match(app, /row-chevron/)
  assert.match(app, /CaretRight/)
  assert.doesNotMatch(app, /match-open/)
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
  assert.match(app, /function Avatar/)
  assert.match(app, /<Avatar userId=\{entry\.user_id\} \/>/)
  assert.match(app, /<Avatar userId=\{match\.user_id\} \/>/)
  assert.match(app, /api\.photoBlobUrl/)
})
