import { useEffect, useRef, useState } from 'react'
import { Chart } from './Chart'
import { startAdaptivePoll } from './livePoll'

/** 研究驾驶舱：三栏，随时点开任何细节，等待期间有东西可看。
 *
 * 左栏 = 全部 Study（按运行分组，最新在上）；中栏 = 实时过程流与曲线；
 * 右栏 = 选中 Study 的产物台（机制、规格、审计、评价、判决）。
 * 与「回放/演化」那些事后视图不同，这一屏的一切都直接读账本、实时追加。
 */

type StudySummary = {
  study_id: string; target?: string; universe?: string
  feature_id?: string; read_outcome?: boolean; verdict?: string
}
type CurvePt = {
  index: number; study_id: string; value: number | null
  running_best: number | null; null_threshold: number; verdict: string
}
type Recent = {
  study_id: string; feature_id?: string; shape?: string; mechanism?: string
  target?: string; universe?: string; direction?: number | null
  falsifiable_condition?: string; audit_codes?: string[]
  verdict?: string; rationale?: string
}
type LiveState = {
  running: boolean; run_id: string | null; current_study: string | null
  last_event: string; seconds_since_last_event: number
  step_index: number; step_total: number; events: number
  verdicts: Record<string, number>
  denominators: { proposal_denominator: number; statistical_denominator: number }
  price: { tests_spent: number; floor_now: number; floor_after_one_more: number }
  curve: CurvePt[]; recent: Recent[]; studies: StudySummary[]
}
type Detail = {
  study_id: string
  proposal?: { mechanism?: string; target?: string; universe?: string; direction?: number
               falsifiable_condition?: string; rationale?: string }
  feature?: { feature_id?: string; mechanism?: string; failure_condition?: string
              content_id?: string; steps?: Record<string, unknown>[] }
  audit?: { code: string; explanation?: string }[]
  evaluation?: { t_stat?: number; ic_spearman?: number; sharpe_annualised?: number
                 coverage?: Record<string, number>; blocked_reasons?: string[] }
  verdict?: { verdict?: string; rationale?: string; next_action?: string }
  timeline?: { seq: number; event_type: string; at: string }[]
}

const V_COLOR: Record<string, string> = {
  candidate: '#3fb950', null: '#8b949e', blocked: '#58a6ff',
  underpowered: '#d29922', error: '#f85149',
}

function stepShape(s: Record<string, unknown>): string {
  const kind = String(s.kind ?? '?')
  const inputs = (s.inputs as string[] | undefined) ?? []
  const inner = inputs.length ? inputs.join(',') : `${s.field ?? ''} ${s.op ?? ''}`.trim()
  return `${kind}(${inner})`
}

export function Cockpit() {
  const [state, setState] = useState<LiveState | null>(null)
  const [stale, setStale] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<Detail | null>(null)
  const seq = useRef(0)
  const runningRef = useRef(false)
  const followRef = useRef(true)   // 没手动选过 Study 时，跟随当前正在跑的那个

  useEffect(() => {
    let alive = true
    const poll = async () => {
      const mine = ++seq.current
      const res = await fetch('/api/live')
      if (!res.ok) throw new Error(String(res.status))
      const data = (await res.json()) as LiveState
      if (!alive || mine !== seq.current) return
      setState(data)
      setStale(false)
      runningRef.current = data.running
      if (followRef.current) {
        // 跟随时选**最近一条有内容的**：正在等模型的那条只有 context_assembled，
        // 右栏会空白整整一次调用（3 至 8 分钟）。有东西看永远优先于"最新"。
        const withContent = (data.recent ?? []).find((r) => r.mechanism)
        setSelected(withContent?.study_id ?? data.current_study)
      }
    }
    const stop = startAdaptivePoll({
      poll: async () => { try { await poll() } catch { if (alive) setStale(true) } },
      intervalMs: () => (runningRef.current ? 2000 : 15000),
    })
    return () => { alive = false; stop() }
  }, [])

  useEffect(() => {
    if (!selected) return
    let alive = true
    fetch(`/api/live/${selected}`)
      .then((r) => r.json())
      .then((d) => { if (alive) setDetail(d) })
      .catch(() => {})
    return () => { alive = false }
  }, [selected, state?.events])   // 账本有新事件时刷新右栏

  if (!state) return <p className="muted small">正在读取账本…</p>

  const byRun = new Map<string, StudySummary[]>()
  for (const s of state.studies ?? []) {
    const run = s.study_id.includes('-study-')
      ? s.study_id.slice(0, s.study_id.indexOf('-study-')) : '其他'
    if (!byRun.has(run)) byRun.set(run, [])
    byRun.get(run)!.push(s)
  }
  const waiting = state.running && state.last_event === 'context_assembled'

  return (
    <div className="cockpit">
      {/* ------------------------------------------------ 顶部状态条 */}
      <header className="ck-top">
        <span className={state.running ? 'dot live-on' : 'dot live-off'} />
        <strong>{state.running ? '研究进行中' : '未在运行'}</strong>
        <span className="mono ck-dim">{state.run_id ?? '—'}</span>
        {waiting && (
          <span className="ck-wait">
            等待模型返回 {Math.round(state.seconds_since_last_event)}s
            <i className="ck-pulse" />
          </span>
        )}
        <span className="ck-spacer" />
        <span className="ck-stat">提案 <b>{state.denominators.proposal_denominator}</b></span>
        <span className="ck-stat">检验 <b>{state.denominators.statistical_denominator}</b></span>
        <span className="ck-stat">地板 <b>{state.price.floor_now}</b></span>
        {stale && <span className="ck-stale">读不到账本，显示上次读数</span>}
      </header>

      <div className="ck-body">
        {/* ------------------------------------------------ 左栏：Study 导航 */}
        <nav className="ck-nav">
          {[...byRun.entries()].map(([run, list]) => (
            <div key={run} className="ck-run">
              <div className="ck-run-head mono">{run} <span className="ck-dim">{list.length}</span></div>
              {list.map((s) => (
                <button key={s.study_id}
                        className={`ck-item ${selected === s.study_id ? 'sel' : ''}`}
                        onClick={() => { followRef.current = false; setSelected(s.study_id) }}>
                  <i className="vdot" style={{ background: V_COLOR[s.verdict ?? ''] ?? '#30363d' }} />
                  <span className="mono ck-item-id">{s.study_id.slice(s.study_id.indexOf('-study-') + 7)}</span>
                  <span className="ck-item-feat">{s.feature_id ?? '…'}</span>
                </button>
              ))}
            </div>
          ))}
        </nav>

        {/* ------------------------------------------------ 中栏：过程与曲线 */}
        <main className="ck-main">
          <section className="ck-card">
            <h4>逐次检验 · 与同步抬高的地板</h4>
            <Chart
              points={state.curve.map((c) => ({
                study_id: c.study_id, verdict: c.verdict, change_summary: '',
                value: c.value, counts_toward_denominator: true, index: c.index - 1,
                tests_so_far: c.index, running_best: c.running_best,
                null_threshold: c.null_threshold,
              })) as never}
              metric="abs_t" showNullBand selected={selected}
              onSelect={(id) => { followRef.current = false; setSelected(id) }}
              xCaption="第几次检验（本族累计，跨全部运行）"
            />
          </section>

          <section className="ck-feed">
            {(state.recent ?? []).map((r) => (
              <button key={r.study_id}
                      className={`ck-beat ${selected === r.study_id ? 'sel' : ''}`}
                      onClick={() => { followRef.current = false; setSelected(r.study_id) }}>
                <div className="ck-beat-head">
                  <i className="vdot" style={{ background: V_COLOR[r.verdict ?? ''] ?? '#30363d' }} />
                  <span className="mono">{r.study_id}</span>
                  {r.verdict && <span className="ck-chip" style={{ borderColor: V_COLOR[r.verdict] }}>{r.verdict}</span>}
                  <span className="ck-dim mono small">{r.target} · {r.universe}</span>
                </div>
                {r.shape && <div className="mono small ck-shape">{r.shape}</div>}
                {r.mechanism && <p className="ck-mech">{r.mechanism.slice(0, 180)}…</p>}
                {r.audit_codes && r.audit_codes.length > 0 && (
                  <div className="ck-audit">审计拦下：{r.audit_codes.join('、')}（未读 outcome，不抬地板）</div>
                )}
              </button>
            ))}
          </section>
        </main>

        {/* ------------------------------------------------ 右栏：产物台 */}
        <aside className="ck-side">
          {!detail && <p className="ck-dim small">点左栏或中栏任何一条，这里展开它的全部产物。</p>}
          {detail && !detail.proposal && (
            <div className="ck-detail">
              <div className="ck-detail-head"><span className="mono">{detail.study_id}</span></div>
              <p className="ck-dim small">
                这一版刚开始：上下文已组装，正在等模型写出提案。
                机制、规格与判决会在它返回后立刻出现在这里。
              </p>
            </div>
          )}
          {detail && detail.proposal && (
            <div className="ck-detail" key={detail.study_id}>
              <div className="ck-detail-head">
                <span className="mono">{detail.study_id}</span>
                {detail.verdict?.verdict && (
                  <span className="ck-chip big" style={{ borderColor: V_COLOR[detail.verdict.verdict] ?? '#30363d' }}>
                    {detail.verdict.verdict}
                  </span>
                )}
              </div>

              {detail.proposal?.mechanism && (
                <section>
                  <h5>机制（模型的推理）</h5>
                  <p className="ck-think">{detail.proposal.mechanism}</p>
                  <div className="ck-kv mono small">
                    <span>{detail.proposal.target}</span>
                    <span>{detail.proposal.universe}</span>
                    <span>方向 {detail.proposal.direction != null && detail.proposal.direction > 0 ? '+1' : '-1'}</span>
                  </div>
                </section>
              )}

              {detail.feature?.steps && detail.feature.steps.length > 0 && (
                <section>
                  <h5>冻结的规格 · {detail.feature.feature_id}</h5>
                  <ol className="ck-steps mono small">
                    {detail.feature.steps.map((s, i) => <li key={i}>{stepShape(s)}</li>)}
                  </ol>
                </section>
              )}

              {detail.proposal?.falsifiable_condition && (
                <section>
                  <h5>证否条件（预注册）</h5>
                  <p className="small">{detail.proposal.falsifiable_condition}</p>
                </section>
              )}

              {detail.audit && detail.audit.length > 0 && (
                <section>
                  <h5>语义审计</h5>
                  {detail.audit.map((a) => (
                    <p key={a.code} className="ck-audit">{a.code}：{a.explanation}</p>
                  ))}
                </section>
              )}

              {detail.evaluation && (
                <section>
                  <h5>评价</h5>
                  <div className="ck-nums">
                    <div><span className="ck-dim small">t</span><b>{detail.evaluation.t_stat?.toFixed(3) ?? '—'}</b></div>
                    <div><span className="ck-dim small">IC 秩</span><b>{detail.evaluation.ic_spearman?.toFixed(4) ?? '—'}</b></div>
                    <div><span className="ck-dim small">Sharpe 年化</span><b>{detail.evaluation.sharpe_annualised?.toFixed(3) ?? '—'}</b></div>
                    <div><span className="ck-dim small">行</span><b>{detail.evaluation.coverage?.rows_submitted ?? '—'}</b></div>
                    <div><span className="ck-dim small">品种簇</span><b>{detail.evaluation.coverage?.product_clusters ?? '—'}</b></div>
                  </div>
                  {(detail.evaluation.blocked_reasons ?? []).map((b, i) => (
                    <p key={i} className="small ck-dim">· {b}</p>
                  ))}
                </section>
              )}

              {detail.verdict?.rationale && (
                <section>
                  <h5>判决理由</h5>
                  <p className="small">{detail.verdict.rationale}</p>
                </section>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
