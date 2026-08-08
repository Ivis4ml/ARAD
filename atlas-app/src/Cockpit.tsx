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
  thinking?: { active: boolean; chars?: number; tail?: string }
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
  // 等待计秒本地每秒跳：只靠轮询回包，5 分钟的等待看起来就像死了
  const fetchedAt = useRef(0)
  const [, forceTick] = useState(0)
  useEffect(() => {
    const t = window.setInterval(() => forceTick((x) => x + 1), 1000)
    return () => window.clearInterval(t)
  }, [])
  // 中右栏分隔条：右栏宽度可拖，记进 localStorage（参照实现的做法）
  const [sideW, setSideW] = useState(() =>
    Number(localStorage.getItem('arad-ck-side') ?? 400))
  const dragging = useRef(false)
  useEffect(() => {
    const move = (e: MouseEvent) => {
      if (!dragging.current) return
      const w = Math.min(640, Math.max(320, window.innerWidth - e.clientX - 40))
      setSideW(w)
    }
    const up = () => {
      if (!dragging.current) return
      dragging.current = false
      document.body.style.cursor = ''
      setSideW((w) => { localStorage.setItem('arad-ck-side', String(w)); return w })
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
    return () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
  }, [])
  // 产物台分页 chips
  const [chip, setChip] = useState('全部')
  // 中栏聚焦当前运行；历史运行折叠进下拉，选中才展开那一轮的卡
  const [histRun, setHistRun] = useState('')

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
      fetchedAt.current = Date.now()
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
      intervalMs: () => (runningRef.current ? 1200 : 15000),   // 直播 1.2s，与参照一致
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

  const currentRun = state.run_id
    ?? (state.studies?.[0]?.study_id.includes('-study-')
        ? state.studies[0].study_id.slice(0, state.studies[0].study_id.indexOf('-study-'))
        : null)
  const byRun = new Map<string, StudySummary[]>()
  for (const s of state.studies ?? []) {
    const run = s.study_id.includes('-study-')
      ? s.study_id.slice(0, s.study_id.indexOf('-study-')) : '其他'
    if (!byRun.has(run)) byRun.set(run, [])
    byRun.get(run)!.push(s)
  }
  const waiting = state.running && state.last_event === 'context_assembled'
  const elapsed = Math.round(
    state.seconds_since_last_event + (fetchedAt.current ? (Date.now() - fetchedAt.current) / 1000 : 0))
  // 发现状态：candidate 数、最好一次与地板的差、离地板最近的前三条
  const withVal = state.curve.filter((c) => c.value !== null) as (CurvePt & { value: number })[]
  const best = withVal.reduce<CurvePt & { value: number } | null>(
    (a, c) => (a === null || c.value > a.value ? c : a), null)
  const nearest = [...withVal].sort(
    (a, b) => (b.value - b.null_threshold) - (a.value - a.null_threshold)).slice(0, 3)
  const nCandidate = state.verdicts.candidate ?? 0

  return (
    <div className="cockpit">
      {/* ------------------------------------------------ 顶部状态条 */}
      <header className="ck-top">
        <span className={state.running ? 'dot live-on' : 'dot live-off'} />
        <strong>{state.running ? '研究进行中' : '未在运行'}</strong>
        <span className="mono ck-dim">{state.run_id ?? '—'}</span>
        {state.running && !waiting && (
          <span className="ck-dim small">上一事件 {elapsed}s 前</span>
        )}
        {waiting && (
          <span className="ck-wait">
            等待模型返回 {elapsed}s
            <i className="ck-pulse" />
          </span>
        )}
        <span className="ck-spacer" />
        <span className="ck-stat">提案 <b>{state.denominators.proposal_denominator}</b></span>
        <span className="ck-stat">检验 <b>{state.denominators.statistical_denominator}</b></span>
        <span className="ck-stat">地板 <b>{state.price.floor_now}</b></span>
        {stale && <span className="ck-stale">读不到账本，显示上次读数</span>}
      </header>

      <div className="ck-body"
           style={{ gridTemplateColumns: `224px minmax(0,1fr) 14px ${sideW}px` }}>
        {/* ------------------------------------------------ 左栏：Study 导航 */}
        <nav className="ck-nav">
          {[...byRun.entries()].map(([run, list]) => {
            const items = list.map((s) => (
              <button key={s.study_id}
                      className={`ck-item ${selected === s.study_id ? 'sel' : ''}`}
                      onClick={() => { followRef.current = false; setSelected(s.study_id) }}>
                <i className="vdot" style={{ background: V_COLOR[s.verdict ?? ''] ?? '#30363d' }} />
                <span className="mono ck-item-id">{s.study_id.slice(s.study_id.indexOf('-study-') + 7)}</span>
                <span className="ck-item-feat">{s.feature_id ?? '…'}</span>
              </button>
            ))
            if (run === currentRun) {
              return (
                <div key={run} className="ck-run">
                  <div className="ck-run-head mono">{run} <span className="ck-dim">{list.length}</span> · 当前</div>
                  {items}
                </div>
              )
            }
            return (
              <details key={run} className="ck-run-fold">
                <summary className="mono">{run} <span className="ck-dim">{list.length}</span></summary>
                {items}
              </details>
            )
          })}
        </nav>

        {/* ------------------------------------------------ 中栏：过程与曲线 */}
        <main className="ck-main">
          {state.thinking?.active && (
            <section className="ck-card ck-live-think">
              <h4>
                模型推理中 <span className="ck-pulse" />
                <span className="ck-dim mono small">　{state.thinking.chars} 字</span>
              </h4>
              {(state.thinking.chars ?? 0) === 0 ? (
                <p className="ck-dim small" style={{ margin: '6px 0 2px' }}>
                  已连接，等待首批增量……（模型先思考再落笔，这一段可能持续几十秒）
                </p>
              ) : (
                <pre className="ck-stream mono" ref={(el) => { if (el) el.scrollTop = el.scrollHeight }}>
                  {state.thinking.tail}
                </pre>
              )}
            </section>
          )}

          <section className="ck-card ck-found">
            <h4>找到因子了吗</h4>
            <div className="ck-nums">
              <div><span className="ck-dim small">candidate</span>
                <b style={{ color: nCandidate ? '#3cc4a8' : undefined }}>{nCandidate}</b></div>
              <div><span className="ck-dim small">最好一次 |t|</span>
                <b>{best ? best.value.toFixed(3) : '—'}</b></div>
              <div><span className="ck-dim small">当前地板</span>
                <b>{state.price.floor_now}</b></div>
              <div><span className="ck-dim small">差距</span>
                <b style={{ color: best && best.value > state.price.floor_now ? '#3cc4a8' : '#f0735e' }}>
                  {best ? (best.value - state.price.floor_now).toFixed(3) : '—'}</b></div>
            </div>
            {nCandidate === 0 && (
              <p className="ck-dim small" style={{ margin: '4px 0 6px' }}>
                还没有。{state.denominators.statistical_denominator} 次检验全部为
                null / blocked / underpowered —— 这是诚实的记录，不是界面没显示。
                离地板最近的三条（点开看它为什么不算）：
              </p>
            )}
            <div className="ck-near">
              {nearest.map((c) => (
                <button key={c.study_id} className="ck-near-item mono"
                        onClick={() => { followRef.current = false; setSelected(c.study_id) }}>
                  {c.study_id}　|t| {c.value.toFixed(2)}
                  <span className="ck-dim"> vs 地板 {c.null_threshold.toFixed(2)}</span>
                </button>
              ))}
            </div>
          </section>

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
            <div className="ck-feed-head">
              <span className="ck-dim small">过程流 · {histRun || `${currentRun ?? '当前'}（进行中）`}</span>
              <select className="ck-hist mono" value={histRun}
                      onChange={(e) => setHistRun(e.target.value)}>
                <option value="">当前运行</option>
                {[...byRun.keys()].filter((r) => r !== currentRun).map((r) => (
                  <option key={r} value={r}>历史 · {r}</option>
                ))}
              </select>
            </div>
            {(state.recent ?? [])
              .filter((r) => {
                const run = r.study_id.slice(0, r.study_id.indexOf('-study-'))
                return histRun ? run === histRun : run === currentRun
              })
              .map((r, i) => (
              <button key={r.study_id}
                      style={{ animationDelay: `${Math.min(i * 45, 360)}ms` }}
                      className={`ck-beat ${selected === r.study_id ? 'sel' : ''}`}
                      onClick={() => { followRef.current = false; setSelected(r.study_id) }}>
                <div className="ck-beat-head">
                  <i className="vdot" style={{ background: V_COLOR[r.verdict ?? ''] ?? '#30363d' }} />
                  <span className="ck-feat mono">{r.feature_id ?? r.study_id}</span>
                  {r.verdict && <span className="ck-chip" style={{ borderColor: V_COLOR[r.verdict], color: V_COLOR[r.verdict] }}>{r.verdict}</span>}
                </div>
                <div className="ck-dim mono ck-meta">{r.study_id} · {r.target} · {r.universe}</div>
                {r.shape && <div className="mono small ck-shape">{r.shape}</div>}
                {r.mechanism && <p className="ck-mech">{r.mechanism.slice(0, 180)}…</p>}
                {r.audit_codes && r.audit_codes.length > 0 && (
                  <div className="ck-audit">审计拦下：{r.audit_codes.join('、')}（未读 outcome，不抬地板）</div>
                )}
              </button>
            ))}
          </section>
        </main>

        <div className="ck-handle" title="拖动调整产物台宽度"
             onMouseDown={() => { dragging.current = true; document.body.style.cursor = 'col-resize' }}>
          <i />
        </div>

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
              <div className="ck-chips">
                {['全部', '机制', '规格', '评价', '判决'].map((c) => (
                  <button key={c} className={`ck-stage-chip ${chip === c ? 'sel' : ''}`}
                          onClick={() => setChip(c)}>{c}</button>
                ))}
              </div>
              <div className="ck-detail-head">
                <span className="mono">{detail.study_id}</span>
                {detail.verdict?.verdict && (
                  <span className="ck-chip big" style={{ borderColor: V_COLOR[detail.verdict.verdict] ?? '#30363d' }}>
                    {detail.verdict.verdict}
                  </span>
                )}
              </div>

              {detail.proposal?.mechanism && ['全部', '机制'].includes(chip) && (
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

              {detail.feature?.steps && detail.feature.steps.length > 0 && ['全部', '规格'].includes(chip) && (
                <section>
                  <h5>冻结的规格 · {detail.feature.feature_id}</h5>
                  <ol className="ck-steps mono small">
                    {detail.feature.steps.map((s, i) => <li key={i}>{stepShape(s)}</li>)}
                  </ol>
                </section>
              )}

              {detail.proposal?.falsifiable_condition && ['全部', '机制'].includes(chip) && (
                <section>
                  <h5>证否条件（预注册）</h5>
                  <p className="small">{detail.proposal.falsifiable_condition}</p>
                </section>
              )}

              {detail.audit && detail.audit.length > 0 && ['全部', '评价'].includes(chip) && (
                <section>
                  <h5>语义审计</h5>
                  {detail.audit.map((a) => (
                    <p key={a.code} className="ck-audit">{a.code}：{a.explanation}</p>
                  ))}
                </section>
              )}

              {detail.evaluation && ['全部', '评价'].includes(chip) && (
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

              {detail.verdict?.rationale && ['全部', '判决'].includes(chip) && (
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
