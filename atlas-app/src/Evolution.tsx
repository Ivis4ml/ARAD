import { useMemo, useState } from 'react'
import type { Chain, Projection, Study } from './types'
import { Chart } from './Chart'
import { METRIC_HAS_NULL_BAND, METRIC_LABELS, num, when } from './format'
import { VerdictChip } from './Value'
import { StudyPanel } from './StudyPanel'

/** 演化层：指标沿谱系的走势。这是这个 app 的主视图。 */
export function Evolution({ p }: { p: Projection }) {
  const [metric, setMetric] = useState('abs_t')
  const [axis, setAxis] = useState<'lineage' | 'time'>('lineage')
  // 默认选**最长**的那条链，不是数组里的第一条。实测 run4 的四条链长度为
  // 1 / 7 / 14 / 6，取第一条会渲染出一大片空白加一条只有一个点的"曲线"。
  // 演化视图的全部意义在于看迭代，起始点选错就等于没有这个视图。
  const longest = [...p.lineage].sort(
    (a, b) => (b.curves?.abs_t?.length ?? 0) - (a.curves?.abs_t?.length ?? 0),
  )[0]
  const [chainId, setChainId] = useState(longest?.chain_id ?? '')
  const [selected, setSelected] = useState<string | null>(null)

  const byId = useMemo(
    () => Object.fromEntries(p.studies.map((s) => [s.study_id, s])) as Record<string, Study>,
    [p.studies],
  )

  const timeChain: Chain | null = useMemo(() => {
    if (!p.studies.length) return null
    const ordered = [...p.studies].sort((a, b) =>
      (a.decided_at || a.created_at).localeCompare(b.decided_at || b.created_at))
    let looked = 0
    let best = -Infinity
    const curves: Record<string, ReturnType<typeof Object>> = {}
    for (const m of p.curve_metrics) {
      looked = 0
      best = -Infinity
      curves[m] = ordered.map((s, i) => {
        if (s.metrics.outcome_reads) looked += 1
        const raw = (s.metrics as unknown as Record<string, number | null>)[m]
        const value = raw !== null && raw !== undefined && Number.isFinite(raw) ? raw : null
        if (value !== null && value > best) best = value
        return {
          study_id: s.study_id, verdict: s.verdict, change_summary: s.change_summary,
          value, counts_toward_denominator: Boolean(s.metrics.outcome_reads),
          index: i, tests_so_far: looked,
          running_best: Number.isFinite(best) ? best : null,
          null_threshold: null,
        }
      })
    }
    return {
      chain_id: '__time__', study_ids: ordered.map((s) => s.study_id), family: '全部',
      curves: curves as Chain['curves'],
    }
  }, [p.studies, p.curve_metrics])

  const chain = axis === 'time'
    ? timeChain
    : p.lineage.find((c) => c.chain_id === chainId) ?? longest ?? null

  if (!chain) return <p className="muted">账本里还没有任何 Study。</p>
  const points = chain.curves[metric] ?? []
  const showBand = axis === 'lineage' && (METRIC_HAS_NULL_BAND[metric] ?? false)
  const study = selected ? byId[selected] : null

  /** DSR 只在 sharpe 曲线上算过，明细表从那条曲线里取，不重算。 */
  function dsrOf(c: Chain, studyId: string): number | null {
    const point = (c.curves.sharpe ?? []).find((x) => x.study_id === studyId)
    return point?.deflated_sharpe ?? null
  }

  return (
    <>
      <section>
        <div className="section-head">
          <span className="idx">01</span>
          <h2>指标沿迭代的走势</h2>
        </div>

        <div className="panel">
          <div className="chart-title">
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
              <select value={metric} onChange={(e) => setMetric(e.target.value)}>
                {p.curve_metrics.map((m) => (
                  <option key={m} value={m}>{METRIC_LABELS[m] ?? m}</option>
                ))}
              </select>
              <select value={axis} onChange={(e) => setAxis(e.target.value as 'lineage' | 'time')}>
                <option value="lineage">横轴：谱系（父子迭代）</option>
                <option value="time">横轴：时间（全部 Study）</option>
              </select>
              {axis === 'lineage' && p.lineage.length > 1 && (
                <select value={chain.chain_id} onChange={(e) => setChainId(e.target.value)}>
                  {p.lineage.map((c) => (
                    <option key={c.chain_id} value={c.chain_id}>
                      链 {c.chain_id}（{c.study_ids.length} 版）
                    </option>
                  ))}
                </select>
              )}
            </div>
            <span className="mono small muted">
              {chain.study_ids.length} 版　·　族 {chain.family}
            </span>
          </div>

          <Chart points={points} metric={metric} showNullBand={showBand}
                 selected={selected} onSelect={setSelected} />

          <div className="legend">
            <span><i className="swatch dot" style={{ background: '#3f5d8a' }} />每一版的取值（按 verdict 着色）</span>
            <span><i className="swatch" style={{ background: '#17708a' }} />running best</span>
            {showBand && (
              <span><i className="swatch" style={{ background: '#c0392b' }} />零假设带：同样次数的搜索在噪声上的期望</span>
            )}
          </div>
        </div>

        {axis === 'time' && (
          <p className="notice">
            横轴是判决时间，不是谱系。相邻两点之间<strong>没有继承关系</strong>，
            这条线只表示先后，不表示演化。零假设带在这个视图下不画：把不同族、不同目标的
            检验混在一条线上，「看了多少次」的口径不成立。
          </p>
        )}

        {showBand ? (
          <p className="notice strong">
            零假设带是{metric === 'sharpe'
              ? '「n 次试验下 Sharpe 最大值的期望」（单侧，搜索只挑最大的那个）'
              : '「n 次独立检验下 |z| 最大值的期望」（双侧，搜索接受任一方向）'}，
            n 取本链已读 outcome 的次数。
            一条随迭代上升的曲线，正是选择在纯噪声上必然产出的形状 —— 只有在曲线
            <strong>离开</strong>这条带之后，「变好了」才有内容。该带按检验独立计算，
            而同族变体高度相关，因此它偏严：没越过带不等于确定无效。
          </p>
        ) : (
          <p className="notice">
            该指标没有配零假设带。IC 的零假设离散度不能用同一套办法从本链估出来，
            要给它配带需要另做置换分布。
          </p>
        )}

        {metric === 'sharpe' && (
          <p className="notice">
            Sharpe 的零假设带取自<strong>本链自身的 Sharpe 离散度</strong>，
            因此至少要两次有定义的试验才画得出来，第一版必然没有。
            DSR（紧缩 Sharpe）是「观测值真正超过该基准」的概率：低于 0.5 就意味着
            这个 Sharpe 与选择在噪声上挑出来的最好值无法区分。全部为 pre-cost：
            未扣交易成本与容量约束。
          </p>
        )}
      </section>

      <section>
        <div className="section-head"><span className="idx">02</span><h2>逐版明细</h2></div>
        <div className="tablewrap">
          <table>
            <thead>
              <tr>
                <th>#</th><th style={{ textAlign: 'left' }}>Study</th><th>verdict</th>
                <th>|t|</th><th>IC</th><th>Sharpe</th><th>年化</th><th>DSR</th>
                <th style={{ textAlign: 'left' }}>相对上一版改了什么</th>
              </tr>
            </thead>
            <tbody>
              {chain.study_ids.map((id, i) => {
                const s = byId[id]
                if (!s) return null
                return (
                  <tr key={id} className={`clickable${selected === id ? ' selected' : ''}`}
                      onClick={() => setSelected(id)}>
                    <td className="mono">{i + 1}</td>
                    <td style={{ textAlign: 'left' }} className="mono">{id}</td>
                    <td><VerdictChip verdict={s.verdict} /></td>
                    <td className="mono">{num(s.metrics.abs_t)}</td>
                    <td className="mono">{num(s.metrics.ic_spearman, 4)}</td>
                    <td className="mono" title={s.metrics.sharpe_undefined_reason ?? undefined}>
                      {s.metrics.sharpe === null ? '未定义' : num(s.metrics.sharpe, 4)}
                    </td>
                    <td className="mono">{num(s.metrics.sharpe_annualised)}</td>
                    <td className="mono">
                      {num(dsrOf(chain, id), 3)}
                    </td>
                    <td style={{ textAlign: 'left', whiteSpace: 'normal' }}>
                      {s.change_summary || <span className="muted">未声明</span>}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {chain.study_ids.some((id) => byId[id]?.metrics.sharpe === null) && (
          <p className="notice">
            Sharpe 显示「未定义」不是缺数据：当前 target 的 label 是已实现波动，不是有符号收益。
            对非收益 label 算 Sharpe 会得到一个数，但那个数不是 Sharpe，因此评价机拒绝出具。
          </p>
        )}
      </section>

      {study && (
        <section>
          <div className="section-head">
            <span className="idx">03</span>
            <h2>判决快照　<span className="mono small muted">{study.study_id}</span></h2>
          </div>
          <StudyPanel study={study} />
        </section>
      )}
      <p className="muted small">最近判决：{when(study?.decided_at)}</p>
    </>
  )
}
