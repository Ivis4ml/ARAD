import type { CurvePoint } from './types'
import { num } from './format'

/** 演化曲线。手写 SVG：不引第三方图表库，也就没有任何网络依赖。
 *
 * 三条内容缺一不可：每次尝试的点、running best、零假设带。只画前两条会系统性地
 * 骗人 —— 一条随迭代上升的曲线，正是选择在纯噪声上必然产出的形状。
 *
 * **纵轴范围一次性由全部点定死，不随回放变化。**否则每落一个点整张图都重新缩放，
 * 早期的点看起来会比它实际的位置高，那是用动画撒谎。
 */

const VERDICT_FILL: Record<string, string> = {
  candidate: '#1f6f43', null: '#5a6270', underpowered: '#8a6d1f',
  blocked: '#3f5d8a', error: '#8a2f2f',
}

type Props = {
  points: CurvePoint[]
  metric: string
  showNullBand: boolean
  selected: string | null
  onSelect: (studyId: string) => void
  /** 已出结果的点数。回放时逐步增加；静态视图传 points.length。 */
  revealed?: number
  /** 已冻结但还没出结果的那个提案 —— 画成空心待定点。 */
  pendingId?: string | null
  /** 横轴说明。**必须由调用方给**：演化视图的横轴是「第几版沿谱系」，
   *  实时视图的横轴是「本族第几次检验」，两者跨的对象不同（实测实时那条
   *  27 个点跨了 5 次运行，根本不是一条谱系）。写死一个会骗人。 */
  xCaption?: string
}

export function Chart({
  points, metric, showNullBand, selected, onSelect,
  revealed, pendingId, xCaption,
}: Props) {
  const W = 720
  const H = 320
  const pad = { top: 20, right: 18, bottom: 50, left: 56 }
  const innerW = W - pad.left - pad.right
  const innerH = H - pad.top - pad.bottom
  const shown = revealed === undefined ? points.length : revealed

  const values: number[] = []
  points.forEach((p) => {
    if (p.value !== null && Number.isFinite(p.value)) values.push(p.value)
    if (p.running_best !== null && Number.isFinite(p.running_best)) values.push(p.running_best)
    if (showNullBand && p.null_threshold !== null) values.push(p.null_threshold)
  })
  if (!values.length) {
    return (
      <p className="muted small">
        本链在该指标上没有任何有定义的取值。这不是渲染问题：判决未走到评价的 Study
        没有这个数，Atlas 不会替它补一个。
      </p>
    )
  }
  const lo = Math.min(0, ...values)
  const hi = Math.max(...values)
  const span = hi - lo || 1
  const yMin = lo - span * 0.1
  const yMax = hi + span * 0.14
  const x = (i: number) =>
    pad.left + (points.length === 1 ? innerW / 2 : (i / (points.length - 1)) * innerW)
  const y = (v: number) => pad.top + innerH - ((v - yMin) / (yMax - yMin)) * innerH

  const ticks = 4
  const gridY = Array.from({ length: ticks + 1 }, (_, i) => yMin + ((yMax - yMin) * i) / ticks)

  const line = (accessor: (p: CurvePoint) => number | null, limit: number) => {
    const segs: string[] = []
    let open = false
    points.slice(0, limit).forEach((p, i) => {
      const v = accessor(p)
      if (v === null || !Number.isFinite(v)) { open = false; return }
      segs.push(`${open ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
      open = true
    })
    return segs.join(' ')
  }

  const bandPath = (() => {
    if (!showNullBand) return ''
    const visible = points.slice(0, shown)
    const idx = visible.map((p, i) => [p, i] as const).filter(([p]) => p.null_threshold !== null)
    if (!idx.length) return ''
    const top = idx.map(([p, i], k) =>
      `${k ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.null_threshold!).toFixed(1)}`).join(' ')
    const first = idx[0][1]
    const last = idx[idx.length - 1][1]
    return `${top} L${x(last).toFixed(1)},${y(yMin).toFixed(1)} L${x(first).toFixed(1)},${y(yMin).toFixed(1)} Z`
  })()

  const pendingIndex = pendingId ? points.findIndex((p) => p.study_id === pendingId) : -1

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" className="curve"
         aria-label={`${metric} 随迭代的走势，含 running best 与零假设带`}>
      {gridY.map((v, i) => (
        <g key={i}>
          <line x1={pad.left} x2={W - pad.right} y1={y(v)} y2={y(v)}
                className="grid" strokeWidth={1} />
          <text x={pad.left - 8} y={y(v) + 4} textAnchor="end"
                fontSize={10.5} className="axis" fontFamily="var(--mono)">
            {num(v, Math.abs(yMax) < 1 ? 3 : 1)}
          </text>
        </g>
      ))}

      {bandPath && <path d={bandPath} className="band-fill" />}
      {showNullBand && (
        <path d={line((p) => p.null_threshold, shown)} fill="none" className="band-line"
              strokeWidth={1.5} strokeDasharray="5 4" />
      )}
      <path d={line((p) => p.running_best, shown)} fill="none" className="best-line"
            strokeWidth={2} strokeLinecap="round" />

      {pendingIndex >= 0 && pendingIndex >= shown && (
        <g className="pending">
          <line x1={x(pendingIndex)} x2={x(pendingIndex)} y1={pad.top} y2={pad.top + innerH}
                stroke="#8a6d1f" strokeWidth={1} strokeDasharray="3 4" opacity={0.55} />
          <circle cx={x(pendingIndex)} cy={pad.top + innerH} r={5.5}
                  fill="none" stroke="#8a6d1f" strokeWidth={2} />
          <text x={x(pendingIndex)} y={pad.top + innerH - 12} textAnchor="middle"
                fontSize={10.5} fill="#8a6d1f">提案已冻结，尚未取值</text>
        </g>
      )}

      {/* 已落下但没有取值的版本。不画它，用户只会以为图坏了；画成实心点，
          又等于伪造一个不存在的取值。因此画在轴上，空心，明说它没有取值。
          实测：run3-study-0 那条 14 点的链前 6 点全部如此 —— 它们被语义审计拦下，
          根本没读 outcome，因此地板不因它们抬高。那是审计在替我们省预算的证据，
          此前在图上完全看不见。 */}
      {points.slice(0, shown).map((p, i) =>
        p.value !== null && Number.isFinite(p.value) ? null : (
          <g key={`novalue-${p.study_id}`} onClick={() => onSelect(p.study_id)}
             style={{ cursor: 'pointer' }} className="point novalue">
            <line x1={x(i)} y1={pad.top + innerH - 7} x2={x(i)} y2={pad.top + innerH + 7}
                  stroke={VERDICT_FILL[p.verdict] ?? '#8a8f98'} strokeWidth={2}
                  opacity={0.75} />
            <circle cx={x(i)} cy={pad.top + innerH} r={4} fill="none"
                    stroke={VERDICT_FILL[p.verdict] ?? '#8a8f98'} strokeWidth={1.5} />
            <title>
              {`${p.study_id}\n${p.verdict}\n这一版没有取值：未读 outcome，`
                + `因此不计入统计分母，零假设带不因它抬高`}
            </title>
          </g>
        ),
      )}

      {points.slice(0, shown).map((p, i) =>
        p.value === null || !Number.isFinite(p.value) ? null : (
          <g key={p.study_id} onClick={() => onSelect(p.study_id)}
             style={{ cursor: 'pointer' }}
             className={i === shown - 1 ? 'point landed' : 'point'}>
            <circle cx={x(i)} cy={y(p.value)} r={selected === p.study_id ? 7 : 5}
                    fill={VERDICT_FILL[p.verdict] ?? '#5a6270'}
                    className="pt-ring" strokeWidth={selected === p.study_id ? 2.5 : 1.5} />
            <title>
              {`${p.study_id}\n${p.verdict}\n值 ${num(p.value, 4)}\n已读 outcome ${p.tests_so_far} 次` +
                (p.change_summary ? `\n改动：${p.change_summary}` : '')}
            </title>
          </g>
        ),
      )}

      {points.map((p, i) => (
        <text key={`x${p.study_id}`} x={x(i)} y={H - pad.bottom + 18} textAnchor="middle"
              fontSize={10.5} className={i < shown ? 'axis' : 'axis dimmer'}
              fontFamily="var(--mono)"
              fontWeight={selected === p.study_id ? 700 : 400}>
          {i + 1}
        </text>
      ))}
      <text x={pad.left + innerW / 2} y={H - 10} textAnchor="middle" fontSize={11} className="axis">
        {xCaption ?? '第几版（沿谱系）　·　点开一个点看它的判决快照'}
      </text>
    </svg>
  )
}
