import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const app = await readFile(new URL('../src/App.tsx', import.meta.url), 'utf8')
const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')

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
