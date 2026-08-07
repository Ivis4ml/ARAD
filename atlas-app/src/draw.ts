import type { Projection } from './types'

/** 开场抽签。
 *
 *  **随机只落在入口，不落在结论上。**同一份账本，两个人打开必须得到同一个判决 ——
 *  判决区在 DOM 次序与字号上都排在抽签之前，抽签够不到它。抽签能决定的只有
 *  「你从哪一拍走进这个过程」，而每一拍都是账本里的真实事件，看哪一拍都不改变结论。
 *
 *  页面是 (产物, 种子) 的纯函数：种子写在地址栏里就能逐像素复现，因此这不是暗箱。
 *  抽取次序是兼容性契约 —— 中间插一次抽取会改掉所有既有种子对应的页面。
 */

export type Draw = {
  seed: number
  pinned: boolean
  entry: Projection['key_moments'][number] | null
  tempo: number
}

export function seedHex(seed: number): string {
  return seed.toString(16).toUpperCase().padStart(4, '0')
}

function readSeed(): { seed: number; pinned: boolean } {
  const q = new URLSearchParams(location.search).get('seed')
  if (q && /^[0-9a-fA-F]{4}$/.test(q)) return { seed: parseInt(q, 16), pinned: true }
  const buf = new Uint16Array(1)
  crypto.getRandomValues(buf)          // file:// 上可用；crypto.subtle 不可用
  return { seed: buf[0], pinned: false }
}

function prng(seed: number): () => number {
  let a = (seed ^ 0x9e3779b9) >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function makeDraw(moments: Projection['key_moments']): Draw {
  const { seed, pinned } = readSeed()
  const rnd = prng(seed)
  // 抽取次序固定：1) 入口 2) 节奏。
  const entry = moments.length ? moments[Math.floor(rnd() * moments.length)] : null
  const tempo = 0.92 + rnd() * 0.2
  return { seed, pinned, entry, tempo }
}

export function redraw(): void {
  location.href = location.pathname
}

export function pin(seed: number): boolean {
  try {
    history.replaceState(null, '', `?seed=${seedHex(seed)}`)
    return true
  } catch {
    return false      // file:// 上 replaceState 可能抛 SecurityError
  }
}
