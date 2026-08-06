import { useCallback, useEffect, useRef, useState } from 'react'
import type { Beat } from './types'

/** 回放的播放控制。
 *
 *  刻意**不追求快**：默认每拍 1.1 秒。这个页面要讲的是「它看了多少次才挑出一个点」，
 *  一次性画完的图把这件事整个抹平。停顿本身是内容。
 */
export const SPEEDS = [
  { label: '0.5×', ms: 2200 },
  { label: '1×', ms: 1100 },
  { label: '2×', ms: 550 },
  { label: '4×', ms: 275 },
]

export function useReplay(beats: Beat[], start = 0) {
  const [cursor, setCursor] = useState(start)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const timer = useRef<number | null>(null)

  const stop = useCallback(() => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current)
      timer.current = null
    }
  }, [])

  useEffect(() => {
    if (!playing) return stop
    if (cursor >= beats.length - 1) {
      setPlaying(false)
      return stop
    }
    // 在「读 outcome」这一拍多停一会儿：零假设带正是在这里抬高，
    // 而那是整个页面最该被看见的一步
    const extra = beats[cursor + 1]?.stage === 'look' ? 1.6 : 1
    timer.current = window.setTimeout(
      () => setCursor((c) => Math.min(c + 1, beats.length - 1)),
      SPEEDS[speed].ms * extra,
    )
    return stop
  }, [playing, cursor, speed, beats, stop])

  const seek = useCallback((i: number) => {
    setCursor(Math.max(0, Math.min(i, beats.length - 1)))
  }, [beats.length])

  return {
    cursor,
    beat: beats[cursor],
    playing,
    speed,
    setSpeed,
    seek,
    step: (d: number) => { setPlaying(false); seek(cursor + d) },
    toggle: () => {
      if (cursor >= beats.length - 1) setCursor(start)
      setPlaying((p) => !p)
    },
    restart: () => { setCursor(start); setPlaying(true) },
  }
}
