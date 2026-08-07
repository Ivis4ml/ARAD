import { useEffect, useRef, useState } from 'react'
import { startAdaptivePoll } from './livePoll'

/** 一个 Study 固定走的 11 步。中文名只用于显示，判定一律按事件类型。 */
const STEP_LABELS: Record<string, string> = {
  context_assembled: '组装盲化上下文',
  proposal_locked: '冻结提案',
  hypothesis_locked: '冻结假设',
  confirmatory_locked: '冻结检验规格',
  study_created: '建立 Study',
  feature_spec_locked: '冻结特征规格',
  semantic_audit: '语义审计（读 outcome 之前）',
  visible_data_range: '声明可见数据范围',
  outcome_read: '读取 outcome（统计分母加一）',
  evaluation_result: '评价机出具结果',
  verdict_recorded: '判决入账',
}

type Step = { step: string; seq: number | null; done: boolean }
type LiveState = {
  running: boolean
  run_id: string | null
  current_study: string | null
  last_event: string
  seconds_since_last_event: number
  pipeline: Step[]
  step_index: number
  step_total: number
  events: number
  verdicts: Record<string, number>
  denominators: { proposal_denominator: number; statistical_denominator: number }
  price: { tests_spent: number; floor_now: number; floor_after_one_more: number }
}

export function Live() {
  const [state, setState] = useState<LiveState | null>(null)
  const [stale, setStale] = useState(false)
  const seq = useRef(0)
  const running = useRef(false)

  useEffect(() => {
    let alive = true
    const poll = async () => {
      const mine = ++seq.current
      const res = await fetch('/api/live')
      if (!res.ok) throw new Error(String(res.status))
      const data = (await res.json()) as LiveState
      // 后发先至的响应丢弃；已卸载也丢弃
      if (!alive || mine !== seq.current) return
      setState(data)
      setStale(false)
      running.current = data.running
    }
    const wrapped = async () => {
      try { await poll() } catch { if (alive) setStale(true) }   // 失败只标记，不清空已有状态
    }
    const stop = startAdaptivePoll({
      poll: wrapped,
      intervalMs: () => (running.current ? 4000 : 30000),
    })
    return () => { alive = false; stop() }
  }, [])

  if (!state) {
    return <p className="muted small">正在读取账本…</p>
  }
  const pct = state.step_total ? (state.step_index / state.step_total) * 100 : 0
  return (
    <section className="live">
      <div className="live-head">
        <span className={state.running ? 'dot live-on' : 'dot live-off'} />
        <strong>{state.running ? '研究进行中' : '未在运行'}</strong>
        <span className="mono small muted">
          {state.run_id ?? '—'}　·　{state.current_study ?? '—'}
        </span>
        {stale && (
          <span className="small warn">
            读不到账本，显示的是上一次成功的读数
          </span>
        )}
      </div>

      <div className="live-bar" aria-label={`第 ${state.step_index} / ${state.step_total} 步`}>
        <i style={{ width: `${pct}%` }} />
      </div>
      <p className="small muted">
        当前 Study 第 <strong>{state.step_index}</strong> / {state.step_total} 步　·
        最后一个事件 <code>{state.last_event}</code>，
        {Math.round(state.seconds_since_last_event)} 秒前
      </p>

      <ol className="live-steps">
        {state.pipeline.map((s) => (
          <li key={s.step} className={s.done ? 'done' : 'todo'}>
            <span className="mark">{s.done ? '✓' : '·'}</span>
            <span className="label">{STEP_LABELS[s.step] ?? s.step}</span>
            <code className="small muted">{s.step}</code>
          </li>
        ))}
      </ol>

      <div className="live-facts">
        <div><span className="muted small">提案分母</span><b>{state.denominators.proposal_denominator}</b></div>
        <div><span className="muted small">统计分母</span><b>{state.denominators.statistical_denominator}</b></div>
        <div><span className="muted small">当前地板</span><b>{state.price.floor_now}</b></div>
        <div><span className="muted small">再问一个</span><b>{state.price.floor_after_one_more}</b></div>
      </div>

      <p className="notice small">
        这一栏<strong>不显示任何效应量</strong>。进度是「跑到哪了」，不是「结果如何」——
        运行期间盯着效应看，会让「要不要继续找」这个判断变成事后选择，
        而那正是零假设带在度量的东西。结果在运行结束后的判决视图里看。
      </p>
    </section>
  )
}
