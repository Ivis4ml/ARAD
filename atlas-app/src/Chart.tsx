import type { CurvePoint } from './types'
import { num } from './format'

/** 演化曲线。手写 SVG：不引第三方图表库，也就没有任何网络依赖。
 *
 * 三条内容缺一不可：
 *  - 每次尝试的点（含未读 outcome 的轮次，它们是提案分母的一部分）
 *  - running best
 *  - 零假设带：同样次数的搜索在纯噪声上能达到的水平
 *
 * 只画前两条会系统性地骗人 —— 一条随迭代上升的曲线，正是选择在噪声上必然产出的形状。
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
}

export function Chart({ points, metric, showNullBand, selected, onSelect }: Props) {
  const W = 720
  const H = 300
  const pad = { top: 18, right: 18, bottom: 46, left: 52 }
  const innerW = W - pad.left - pad.right
  const innerH = H - pad.top - pad.bottom

  const values: number[] = []
  points.forEach((p) => {
    if (p.value !== null && Number.isFinite(p.value)) values.push(p.value)
    if (p.running_best !== null && Number.isFinite(p.running_best)) values.push(p.running_best)
    if (showNullBand && p.null_threshold !== null) values.push(p.null_threshold)
  })
  if (!values.length) {
    return (
      <p className="muted small">
        本链在该指标上没有任何有定义的取值。这不是渲染问题：判决未走到评价的
        Study 没有这个数，Atlas 不会替它补一个。
      </p>
    )
  }
  const lo = Math.min(0, ...values)
  const hi = Math.max(...values)
  const span = hi - lo || 1
  const yMin = lo - span * 0.08
  const yMax = hi + span * 0.12
  const x = (i: number) =>
    pad.left + (points.length === 1 ? innerW / 2 : (i / (points.length - 1)) * innerW)
  const y = (v: number) => pad.top + innerH - ((v - yMin) / (yMax - yMin)) * innerH

  const ticks = 4
  const gridY = Array.from({ length: ticks + 1 }, (_, i) => yMin + ((yMax - yMin) * i) / ticks)

  const line = (accessor: (p: CurvePoint) => number | null) => {
    const segs: string[] = []
    let open = false
    points.forEach((p, i) => {
      const v = accessor(p)
      if (v === null || !Number.isFinite(v)) { open = false; return }
      segs.push(`${open ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
      open = true
    })
    return segs.join(' ')
  }

  const bandPath = (() => {
    if (!showNullBand) return ''
    const top: string[] = []
    points.forEach((p, i) => {
      if (p.null_threshold === null) return
      top.push(`${top.length ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.null_threshold).toFixed(1)}`)
    })
    if (!top.length) return ''
    const first = points.findIndex((p) => p.null_threshold !== null)
    const last = points.length - 1 - [...points].reverse().findIndex((p) => p.null_threshold !== null)
    return `${top.join(' ')} L${x(last).toFixed(1)},${y(yMin).toFixed(1)} L${x(first).toFixed(1)},${y(yMin).toFixed(1)} Z`
  })()

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
         aria-label={`${metric} 随迭代的走势，含 running best 与零假设带`}>
      {gridY.map((v, i) => (
        <g key={i}>
          <line x1={pad.left} x2={W - pad.right} y1={y(v)} y2={y(v)}
                stroke="#edf0f4" strokeWidth={1} />
          <text x={pad.left - 8} y={y(v) + 4} textAnchor="end"
                fontSize={10.5} fill="#5c6773" fontFamily="var(--mono)">
            {num(v, Math.abs(yMax) < 1 ? 3 : 1)}
          </text>
        </g>
      ))}
      {bandPath && <path d={bandPath} fill="#c0392b" fillOpacity={0.07} />}
      {showNullBand && (
        <path d={line((p) => p.null_threshold)} fill="none" stroke="#c0392b"
              strokeWidth={1.5} strokeDasharray="5 4" />
      )}
      <path d={line((p) => p.running_best)} fill="none" stroke="#17708a" strokeWidth={2} />
      {points.map((p, i) =>
        p.value === null || !Number.isFinite(p.value) ? null : (
          <g key={p.study_id} onClick={() => onSelect(p.study_id)} style={{ cursor: 'pointer' }}>
            <circle cx={x(i)} cy={y(p.value)} r={selected === p.study_id ? 7 : 5}
                    fill={VERDICT_FILL[p.verdict] ?? '#5a6270'}
                    stroke="#fff" strokeWidth={selected === p.study_id ? 2.5 : 1.5} />
            <title>
              {`${p.study_id}\n${p.verdict}\n值 ${num(p.value, 4)}\n已读 outcome ${p.tests_so_far} 次` +
                (p.change_summary ? `\n改动：${p.change_summary}` : '')}
            </title>
          </g>
        ),
      )}
      {points.map((p, i) => (
        <text key={`x${p.study_id}`} x={x(i)} y={H - pad.bottom + 16} textAnchor="middle"
              fontSize={10.5} fill={selected === p.study_id ? '#131a22' : '#5c6773'}
              fontFamily="var(--mono)" fontWeight={selected === p.study_id ? 700 : 400}>
          {i + 1}
        </text>
      ))}
      <text x={pad.left + innerW / 2} y={H - 8} textAnchor="middle" fontSize={11} fill="#5c6773">
        第几版（沿谱系）　·　点开一个点看它的判决快照
      </text>
    </svg>
  )
}
