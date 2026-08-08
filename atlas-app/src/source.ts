import type { Projection } from './types'

/** 数据源。两条路都要能走：
 *
 *  - **单文件自包含**：文档里注入了 `#atlas-data`，不需要服务器，整个运行一个文件带走；
 *  - **运行目录**：走 `/api/runs/...`，能看历史、能并排比较。
 *
 *  注入优先。这不是偏好问题：单文件那份是自证的，它带着数据一起走；
 *  API 那份取决于服务器指向哪个目录。
 */

export type Card = {
  feature_id: string
  content_id: string
  status: string
  taxonomy_clean: boolean
  mechanism: string
  failure_condition: string
  formula: string[]
  code: string
  sources: string[]
  required_lookback_seconds: number
  discovery: Record<string, unknown>
  sealed: Record<string, unknown> | null
  meaning: string
}

export type RunRow = {
  run_id: string
  created_at: string
  family: string | null
  studies: number
  statistical_denominator: number
  proposal_denominator: number
  headline: string
  exceeded_band: boolean
  cards: number
  chain_intact: boolean
}

export type Loaded = {
  mode: 'inline' | 'api'
  projection: Projection
  cards: Card[]
  runs: RunRow[]
  runId: string | null
}

function inline(): Projection | null {
  const node = document.getElementById('atlas-data')
  if (!node?.textContent) return null
  try {
    return JSON.parse(node.textContent) as Projection
  } catch {
    return null
  }
}

async function json<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${url} → ${res.status}`)
  return (await res.json()) as T
}

export async function load(): Promise<Loaded> {
  const injected = inline()
  if (injected) {
    return { mode: 'inline', projection: injected, cards: [], runs: [], runId: null }
  }
  const archived = await json<RunRow[]>('/api/runs').catch(() => [] as RunRow[])
  // 第一项永远是当前账本：归档快照只在服务**正常结束**时写一次，被停掉或崩溃的
  // 运行没有快照；且每个快照是当时全账本的累计投影，不是该次运行的切片。
  const runs: RunRow[] = [
    { run_id: '__live__', studies: -1, cards: 0 } as unknown as RunRow,
    ...archived,
  ]
  const wanted = new URLSearchParams(location.search).get('run')
  const runId = runs.find((r) => r.run_id === wanted)?.run_id ?? '__live__'
  if (runId === '__live__') {
    const projection = await json<Projection>('/api/live/projection')
    return { mode: 'api', projection, cards: [], runs, runId }
  }
  const [projection, cards] = await Promise.all([
    json<Projection>(`/api/runs/${runId}/atlas`),
    json<Card[]>(`/api/runs/${runId}/cards`).catch(() => [] as Card[]),
  ])
  return { mode: 'api', projection, cards, runs, runId }
}

export function switchRun(runId: string): void {
  const params = new URLSearchParams(location.search)
  params.set('run', runId)
  location.search = params.toString()
}
