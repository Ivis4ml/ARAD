import { useEffect, useRef, useState } from 'react'
import type { Beat } from './types'
import { startAdaptivePoll } from './livePoll'

/** 增量拉取账本节拍。开启后回放的数据源由「静态快照」变为「追加的实时流」。
 *
 * 只拉 `since` 之后的新拍：每次从头重算会让轮询随运行时间变慢，
 * 而那正是最需要它的时候。累计量（提案分母、统计分母）由服务端在边界处取一次，
 * 再在新拍上往后累加，因此跨批次接得上。
 */
export function useLiveBeats(enabled: boolean) {
  const [beats, setBeats] = useState<Beat[]>([])
  const [head, setHead] = useState(0)
  const [stale, setStale] = useState(false)
  const lastSeq = useRef(0)

  useEffect(() => {
    if (!enabled) return undefined
    let alive = true
    const pull = async () => {
      // 一次轮询里把落后的拍全部追上：服务端每次最多给一批，
      // 落后很多时不能只前进一批，否则永远追不上正在跑的运行。
      for (let guard = 0; guard < 20; guard += 1) {
        const res = await fetch(`/api/live/beats?since=${lastSeq.current}`)
        if (!res.ok) throw new Error(String(res.status))
        const data = await res.json()
        if (!alive) return
        setHead(data.head ?? 0)
        if (!data.beats?.length) break
        lastSeq.current = data.beats[data.beats.length - 1].seq
        setBeats((prev) => [...prev, ...data.beats])
        if (!data.more) break
      }
      if (alive) setStale(false)
    }
    const stop = startAdaptivePoll({
      poll: async () => {
        try { await pull() } catch { if (alive) setStale(true) }   // 失败不清空已有的拍
      },
      intervalMs: () => 4000,
    })
    return () => { alive = false; stop() }
  }, [enabled])

  return { beats, head, stale }
}
