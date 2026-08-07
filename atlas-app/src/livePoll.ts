/** 可见性自适应轮询。四条性质，每一条都对应一种实测过的失败：
 *
 * 1. **在途不重排**：一次轮询在飞时绝不另起定时器，否则会长出孤儿定时器链，
 *    页面开久了轮询频率会自己变快；
 * 2. **序号防竞态**：后发先至的响应直接丢弃，否则慢请求会用旧数据覆盖新数据；
 * 3. **回前台立即刷一次**：`visibilitychange` 触发；在途时记下，完成后补刷；
 * 4. **隐藏时退避**：页面看不见时把间隔乘几倍。轮询是给人看的，人不在就别轮。
 *
 * 失败**不清空**由调用方负责（见 Live.tsx）：把「暂时读不到」显示成「什么都没有」，
 * 与这个项目一直在修的那类错误是同一种。
 */
export type PollOptions = {
  poll: () => Promise<void>
  /** 毫秒。可以是回调，用于「有运行在跑时更快」。 */
  intervalMs: () => number
  /** 页面隐藏时的间隔。缺省为 intervalMs 的 4 倍。 */
  hiddenFactor?: number
  minMs?: number
}

export function startAdaptivePoll(opts: PollOptions): () => void {
  const minMs = opts.minMs ?? 1000
  const hiddenFactor = opts.hiddenFactor ?? 4
  let timer: number | undefined
  let stopped = false
  let running = false
  let pendingImmediate = false

  const clear = () => {
    if (timer !== undefined) { window.clearTimeout(timer); timer = undefined }
  }
  const hidden = () =>
    typeof document !== 'undefined' && document.visibilityState === 'hidden'

  const schedule = () => {
    if (stopped) return
    clear()
    const base = opts.intervalMs() * (hidden() ? hiddenFactor : 1)
    timer = window.setTimeout(tick, Math.max(minMs, base))
  }

  const tick = async () => {
    if (stopped || running) return       // 在途不重排：续期只由本次的 finally 负责
    running = true
    clear()
    try {
      await opts.poll()
    } catch {
      // 单次失败忽略，下个周期重试。**不改变调用方已有的状态。**
    } finally {
      running = false
      if (stopped) return
      if (pendingImmediate) { pendingImmediate = false; void tick() }
      else schedule()
    }
  }

  const onVisible = () => {
    if (stopped || document.visibilityState !== 'visible') return
    if (running) { pendingImmediate = true; return }
    clear()
    void tick()
  }

  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', onVisible)
  }
  void tick()

  return () => {
    stopped = true
    clear()
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', onVisible)
    }
  }
}
