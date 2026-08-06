import { useEffect, useMemo, useRef, useState } from 'react'
import type { Beat, Chain, Projection, Study } from './types'
import { Chart } from './Chart'
import { SPEEDS, useReplay } from './useReplay'
import { METRIC_HAS_NULL_BAND, METRIC_LABELS, num, when } from './format'
import { Value, VerdictChip } from './Value'
import { StudyPanel } from './StudyPanel'

const STAGE_LABEL: Record<string, string> = {
  episode: 'Episode', assemble: '组装上下文', count: '计入分母', propose: '提案',
  freeze: '冻结', study: '建立 Study', spec: '特征规格', data: '数据范围',
  look: '读 outcome', evaluate: '评价', verdict: '判决', gap: '原语缺口',
  failure: '异常产出', other: '其他',
}

/** 回放层：按账本 seq 逐拍重演整个搜索过程。
 *
 *  这个页面的主张是「过程本身才是证据」：它看了多少次、每看一次零假设带涨多少、
 *  哪些轮次连点都没落下。一次性画完的图把这些全抹平了。
 */
export function Replay({ p }: { p: Projection }) {
  const [metric, setMetric] = useState('abs_t')
  const [chainId, setChainId] = useState(p.lineage[0]?.chain_id ?? '')
  const [selected, setSelected] = useState<string | null>(null)

  const chain: Chain | null =
    p.lineage.find((c) => c.chain_id === chainId) ?? p.lineage[0] ?? null
  const beats = p.replay
  const r = useReplay(beats)
  const byId = useMemo(
    () => Object.fromEntries(p.studies.map((s) => [s.study_id, s])) as Record<string, Study>,
    [p.studies],
  )

  // 事件流跟着当前拍走：播到第 47 拍还停在 #1 的列表等于没有
  const listRef = useRef<HTMLOListElement | null>(null)
  useEffect(() => {
    // 直接查 DOM，不用条件 ref：`ref={i === cursor ? ref : undefined}` 的挂载次序
    // 取决于两个元素在树里的先后，回退播放时会把 ref 置空，滚动静默失效。
    const list = listRef.current
    const item = list?.querySelector<HTMLLIElement>('li.current')
    if (!list || !item) return
    const lr = list.getBoundingClientRect()
    const ir = item.getBoundingClientRect()
    if (ir.top >= lr.top && ir.bottom <= lr.bottom) return
    // 同步赋值，不用 scrollBy({behavior:'smooth'})，也不用 rAF 补间：
    // 实测这两者都可能被静默跳过（smooth 依赖 rAF，而 rAF 在某些上下文里根本不触发，
    // delta=1687 调用后 scrollTop 仍是 0）。列表的定位是功能不是修饰，必须确定发生；
    // 动画交给曲线上的 CSS。
    const lr2 = list.getBoundingClientRect()
    list.scrollTop = Math.max(0, Math.min(
      list.scrollTop + (ir.top - lr2.top) - (lr2.height - ir.height) / 2,
      list.scrollHeight - list.clientHeight,
    ))
  }, [r.cursor])

  if (!chain || !beats.length) return <p className="muted">账本里还没有可回放的内容。</p>

  const points = chain.curves[metric] ?? []
  const showBand = METRIC_HAS_NULL_BAND[metric] ?? false

  // 已出结果的点 = 到当前这一拍为止，evaluation_result 出现过几次
  const revealedIds = new Set(
    beats.slice(0, r.cursor + 1)
      .filter((b) => b.reveal_point && b.study_id)
      .map((b) => b.study_id as string),
  )
  const revealed = points.filter((pt) => revealedIds.has(pt.study_id)).length
  const pendingBeat = [...beats.slice(0, r.cursor + 1)].reverse()
      .find((b) => b.pending_point && b.study_id)
  const pendingId = pendingBeat && !revealedIds.has(pendingBeat.study_id as string)
    ? (pendingBeat.study_id as string)
    : null
  const study = selected ? byId[selected] : null

  return (
    <>
      <section>
        <div className="section-head">
          <span className="idx">01</span>
          <h2>一个点一个点地看它怎么找</h2>
        </div>
        <p className="muted small" style={{ maxWidth: '76ch' }}>
          下面这段是<strong>账本的逐拍重演</strong>，不是动画脚本：每一拍对应一个真实事件，
          顺序就是 <code className="mono">seq</code> 的顺序。留意读 outcome 那一拍 ——
          红色的零假设带正是在那里抬高，而它抬得比曲线快还是慢，才是这张图真正在说的事。
        </p>

        <div className="panel replay">
          <div className="transport">
            <button className="primary" onClick={r.toggle}>
              {r.playing ? '暂停' : r.cursor >= beats.length - 1 ? '重放' : '播放'}
            </button>
            <button onClick={() => r.step(-1)} disabled={r.cursor === 0}>上一拍</button>
            <button onClick={() => r.step(1)} disabled={r.cursor >= beats.length - 1}>
              下一拍
            </button>
            <select value={r.speed} onChange={(e) => r.setSpeed(Number(e.target.value))}>
              {SPEEDS.map((s, i) => (<option key={s.label} value={i}>{s.label}</option>))}
            </select>
            <select value={metric} onChange={(e) => setMetric(e.target.value)}>
              {p.curve_metrics.map((m) => (
                <option key={m} value={m}>{METRIC_LABELS[m] ?? m}</option>
              ))}
            </select>
            {p.lineage.length > 1 && (
              <select value={chain.chain_id} onChange={(e) => setChainId(e.target.value)}>
                {p.lineage.map((c) => (
                  <option key={c.chain_id} value={c.chain_id}>
                    链 {c.chain_id}（{c.study_ids.length} 版）
                  </option>
                ))}
              </select>
            )}
            <span className="mono small muted seqbadge">
              第 {r.cursor + 1} / {beats.length} 拍　seq {r.beat.seq}
            </span>
          </div>

          <input className="scrub" type="range" min={0} max={beats.length - 1}
                 value={r.cursor} aria-label="回放进度"
                 onChange={(e) => { r.seek(Number(e.target.value)) }} />

          <div className="counters">
            <Counter k="提案分母" v={r.beat.proposals_so_far}
                     hint="全部提案，含被预检挡下的" />
            <Counter k="统计分母" v={r.beat.tests_so_far} accent
                     hint="真正读过 outcome 的检验次数；零假设带随它抬高" />
            <Counter k="已落点" v={revealed} hint="出了评价结果的版本" />
            <Counter k="待定" v={pendingId ? 1 : 0} hint="已冻结但还没有取值" />
          </div>

          <Chart points={points} metric={metric} showNullBand={showBand}
                 selected={selected} onSelect={setSelected}
                 revealed={revealed} pendingId={pendingId} />

          <BeatCard beat={r.beat} />

          <div className="legend">
            <span><i className="swatch dot" style={{ background: '#3f5d8a' }} />每一版的取值（按 verdict 着色）</span>
            <span><i className="swatch" style={{ background: '#17708a' }} />running best</span>
            {showBand && (
              <span><i className="swatch" style={{ background: '#c0392b' }} />零假设带：同样次数的搜索在噪声上的期望</span>
            )}
            <span><i className="swatch dot hollow" />提案已冻结，尚未取值</span>
          </div>
        </div>
      </section>

      <section>
        <div className="section-head"><span className="idx">02</span><h2>事件流</h2></div>
        <p className="muted small">点任意一拍可以跳过去。这就是账本本身，没有别的来源。</p>
        <ol className="beats" ref={listRef}>
          {beats.map((b, i) => (
            <li key={b.seq}
              className={
                `beat stage-${b.stage}` + (i === r.cursor ? ' current' : '') +
                (i < r.cursor ? ' past' : '')
              }>
              <button onClick={() => { r.seek(i) }}>
                <span className="mono seq">#{b.seq}</span>
                <span className="stage">{STAGE_LABEL[b.stage] ?? b.stage}</span>
                <span className="what">{b.headline}</span>
                <span className="mono who">{b.study_id ?? ''}</span>
              </button>
            </li>
          ))}
        </ol>
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
    </>
  )
}

function Counter({ k, v, hint, accent }: {
  k: string; v: number; hint: string; accent?: boolean
}) {
  return (
    <div className={`chip counter${accent ? ' accent' : ''}`} title={hint}>
      <span className="k">{k}</span>
      <span className="v" key={v}>{v}</span>
    </div>
  )
}

function BeatCard({ beat }: { beat: Beat }) {
  const empty = !beat.detail || Object.keys(beat.detail).length === 0
  return (
    <div className={`beatcard stage-${beat.stage}`} key={beat.seq}>
      <div className="beathead">
        <span className="stage">{STAGE_LABEL[beat.stage] ?? beat.stage}</span>
        <strong>{beat.headline}</strong>
        <span className="mono small muted">{when(beat.at)}</span>
      </div>
      {beat.study_id && (
        <p className="small muted">
          Study <code className="mono">{beat.study_id}</code>
          {beat.detail && 'verdict' in beat.detail && (
            <>　<VerdictChip verdict={String(beat.detail.verdict)} /></>
          )}
        </p>
      )}
      {!empty && <Value node={beat.detail} />}
    </div>
  )
}

export const _keep = num
