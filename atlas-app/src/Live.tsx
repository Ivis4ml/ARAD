import { useEffect, useRef, useState } from 'react'
import { Chart } from './Chart'
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
type Recent = {
  study_id: string; feature_id?: string; shape?: string
  mechanism?: string; target?: string; universe?: string
  direction?: number | null; falsifiable_condition?: string
  audit_codes?: string[]; verdict?: string; rationale?: string
}
type CurvePt = {
  index: number; study_id: string; value: number | null
  running_best: number | null; null_threshold: number; verdict: string
}
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
  curve: CurvePt[]
  recent: Recent[]
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

      <h3 className="small">逐次检验的 |t| 与同步抬高的地板</h3>
      <Chart
        points={state.curve.map((c) => ({
          study_id: c.study_id, verdict: c.verdict, change_summary: '',
          value: c.value, counts_toward_denominator: true, index: c.index - 1,
          tests_so_far: c.index, running_best: c.running_best,
          null_threshold: c.null_threshold,
        })) as never}
        metric="abs_t" showNullBand selected={null} onSelect={() => {}}
      />
      <p className="notice small">
        曲线<strong>绝不单独出现</strong>：一条随迭代上升的曲线，本身就是选择在纯噪声上
        必然产出的形状。要看的是它有没有跑赢那条<strong>同步抬高</strong>的地板 ——
        每多问一个会被评价的假设，地板就往上走一格，而它对已有的与将来的全部结论同时生效。
      </p>
      <h3 className="small">最近几版的中间结论</h3>
      <ol className="live-feed">
        {(state.recent ?? []).map((r) => (
          <li key={r.study_id}>
            <div className="feed-head">
              <code>{r.study_id}</code>
              {r.verdict && <span className={`chip v-${r.verdict}`}>{r.verdict}</span>}
              <span className="mono small muted">
                {r.target}　·　{r.universe}
                {r.direction ? `　·　方向 ${r.direction > 0 ? '+1' : '-1'}` : ''}
              </span>
            </div>
            {r.shape && <p className="mono small muted">{r.feature_id}：{r.shape}</p>}
            {r.mechanism && <p className="small">{r.mechanism}</p>}
            {r.falsifiable_condition && (
              <p className="small muted">证否条件：{r.falsifiable_condition}</p>
            )}
            {r.audit_codes && r.audit_codes.length > 0 && (
              <p className="small warn">
                语义审计拦下：{r.audit_codes.join('、')}　
                <span className="muted">未读 outcome，因此不抬高地板</span>
              </p>
            )}
            {r.rationale && <p className="small muted">判决理由：{r.rationale}</p>}
          </li>
        ))}
      </ol>

      <p className="notice small">
        看着结果决定何时停，会让停止时点与结果相关。零假设带按<strong>已花掉的</strong>
        检验次数计价，早停不会把已花的退回来，因此它不制造额外的多重检验偏差；
        真正的风险是「看着不错就停」—— 而缓解手段正是把地板画在旁边，
        使「不错」是相对于那根横杠判断的，不是相对于零。
      </p>
    </section>
  )
}
