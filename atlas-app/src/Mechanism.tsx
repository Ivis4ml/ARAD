import { dur } from './format'

/** 特征规格的机制图。
 *
 *  规格是一个小 DAG，此前被渲染成嵌套键值表，读不出运算。这里把它画出来：
 *  左边是取数窗口，右边是把它们合成一个数的算子，下面是一把共享的时间标尺 ——
 *  各个窗口伸向过去多远，一眼可比。
 *
 *  **它只排版，不计算。**秒数整除才升单位（除不尽退回原始秒数），
 *  规格里没有的数一律不画：缺席就是不出现，不写「—」，更不补默认值。
 */

type Step = {
  name: string; kind: string; source: string | null; field: string | null
  op: string | null; window_seconds: number | null; offset_seconds: number
  baseline_seconds: number | null; inputs: string[]; controls: string[]
  sample_every_seconds: number | null; min_samples: number | null
}

type Spec = {
  feature_id: string; mechanism: string; steps: Step[]; output_step: string
  required_lookback_seconds: number; failure_condition: string
}

const KIND_RAIL: Record<string, string> = {
  window: '#17708a', innovation: '#8a6d1f', difference: '#8a6d1f', ratio: '#8a6d1f',
  zscore: '#3f5d8a', residualise: '#5c6773',
}
const GLYPH: Record<string, string> = {
  difference: '−', ratio: '÷', innovation: '⟿', zscore: 'z', residualise: '⊥',
}

const PAD_T = 14, NH = 52, ROW_H = 68, GUT = 52
const RX0 = 96, RX1 = 704

/** 分层：叶子在第 0 层，其余为「全部输入所在层的最大值 + 1」。
 *  层内先按声明次序，再按输入的重心上移，最后消重叠并把重心平移回去。 */
function layout(steps: Step[]) {
  const byName = new Map(steps.map((s) => [s.name, s]))
  const decl = new Map(steps.map((s, i) => [s.name, i]))
  const layer = new Map<string, number>()
  // 账本按「输入先于引用」生成，但那不是写进合同的东西，因此这里防御性地迭代收敛
  for (let pass = 0; pass < steps.length + 1; pass += 1) {
    let moved = false
    for (const s of steps) {
      const want = s.inputs.length
        ? 1 + Math.max(...s.inputs.map((i) => layer.get(i) ?? 0))
        : 0
      if (layer.get(s.name) !== want) { layer.set(s.name, want); moved = true }
    }
    if (!moved) break
  }
  const L = Math.max(...steps.map((s) => layer.get(s.name) ?? 0)) + 1
  const NW = L <= 3 ? 156 : Math.max(96, Math.floor((684 - (L - 1) * GUT) / L))
  const CX = (l: number) => 20 + l * (NW + GUT)

  const ytop = new Map<string, number>()
  for (let l = 0; l < L; l += 1) {
    const col = steps.filter((s) => layer.get(s.name) === l)
      .sort((a, b) => (decl.get(a.name)! - decl.get(b.name)!))
    col.forEach((s, k) => ytop.set(s.name, PAD_T + k * ROW_H))
    if (l > 0) {
      for (const s of col) {
        const ins = s.inputs.map((i) => ytop.get(i)).filter((v): v is number => v !== undefined)
        if (ins.length) ytop.set(s.name, ins.reduce((a, b) => a + b, 0) / ins.length)
      }
      col.sort((a, b) => (ytop.get(a.name)! - ytop.get(b.name)!)
        || (decl.get(a.name)! - decl.get(b.name)!))
      const before = col.reduce((a, s) => a + ytop.get(s.name)!, 0) / col.length
      for (let k = 1; k < col.length; k += 1) {
        ytop.set(col[k].name,
          Math.max(ytop.get(col[k].name)!, ytop.get(col[k - 1].name)! + ROW_H))
      }
      const after = col.reduce((a, s) => a + ytop.get(s.name)!, 0) / col.length
      for (const s of col) ytop.set(s.name, ytop.get(s.name)! + (before - after))
    }
  }
  const top = Math.min(...steps.map((s) => ytop.get(s.name)!))
  for (const s of steps) ytop.set(s.name, ytop.get(s.name)! + PAD_T - top)
  const dagH = Math.max(...steps.map((s) => ytop.get(s.name)!)) + NH + 14
  return { byName, layer, L, NW, CX, ytop, dagH }
}

export function Mechanism({ spec }: { spec: Spec }) {
  const steps = spec.steps
  if (!steps.length) return <p className="muted small">这条规格没有步骤。</p>
  const { layer, NW, CX, ytop, dagH } = layout(steps)

  const timed = steps.filter((s) => s.window_seconds)
    .sort((a, b) => (layer.get(a.name)! - layer.get(b.name)!))
  const domainDays = [30, 60, 90, 120, 180, 270, 365]
  const need = spec.required_lookback_seconds || 86400
  const DOMAIN = 86400 * (domainDays.find((d) => d * 86400 >= need) ?? 365)
  const RY0 = dagH + 34
  const H = RY0 + 15 * timed.length + 14
  const X = (ago: number) => RX1 - (ago * (RX1 - RX0)) / DOMAIN

  return (
    <figure className="mechanism">
      <figcaption>
        <code className="mono">{spec.feature_id}</code>
        <span className="muted small">{spec.mechanism}</span>
      </figcaption>
      <svg viewBox={`0 0 720 ${H}`} width="100%" role="img"
           aria-label={`特征 ${spec.feature_id} 的计算图`}>
        {steps.flatMap((s) =>
          s.inputs.map((i) => {
            const x1 = CX(layer.get(i)!) + NW
            const y1 = ytop.get(i)! + NH / 2
            const x2 = CX(layer.get(s.name)!)
            const y2 = ytop.get(s.name)! + NH / 2
            const mid = (x1 + x2) / 2
            return (
              <path key={`${i}->${s.name}`}
                    d={`M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`}
                    fill="none" stroke="#cfd6de" strokeWidth={1.5} />
            )
          }),
        )}

        {steps.map((s) => {
          const x = CX(layer.get(s.name)!)
          const y = ytop.get(s.name)!
          const isOut = s.name === spec.output_step
          return (
            <g key={s.name}>
              <rect x={x} y={y} width={NW} height={NH} rx={7} fill="#fff"
                    stroke={isOut ? '#131a22' : '#e2e6ec'} strokeWidth={isOut ? 2 : 1} />
              <rect x={x} y={y} width={3} height={NH} rx={1.5}
                    fill={KIND_RAIL[s.kind] ?? '#5c6773'} />
              <text x={x + 12} y={y + 19} fontSize={12.5} fontWeight={650} fill="#131a22">
                {s.op ? s.op.toUpperCase() : (GLYPH[s.kind] ?? s.kind)}
                {s.kind === 'zscore' && <tspan fontSize={11} fontWeight={400}> (x−μ)/σ</tspan>}
              </text>
              <text x={x + 12} y={y + 35} fontSize={11} fill="#5c6773"
                    fontFamily="var(--mono)">
                {s.field ?? s.inputs.join(s.kind === 'ratio' ? ' ÷ ' : ' − ')}
              </text>
              <text x={x + 12} y={y + 47} fontSize={10} fill="#8b95a1"
                    fontFamily="var(--mono)">{s.name}</text>
              {s.window_seconds && (
                <text x={x + NW - 10} y={y + 19} textAnchor="end" fontSize={11}
                      fill="#17708a" fontFamily="var(--mono)">
                  <title>{`${s.window_seconds} 秒`}</title>
                  {dur(s.window_seconds)}
                </text>
              )}
              {s.baseline_seconds && (
                <text x={x + NW - 10} y={y + 33} textAnchor="end" fontSize={10}
                      fill="#8a6d1f" fontFamily="var(--mono)">
                  基线 {dur(s.baseline_seconds)}
                </text>
              )}
              {s.sample_every_seconds && (
                <text x={x + NW - 10} y={y + 47} textAnchor="end" fontSize={10}
                      fill="#8b95a1" fontFamily="var(--mono)">
                  每 {dur(s.sample_every_seconds)} 取样 · 至少 {s.min_samples} 个
                </text>
              )}
            </g>
          )
        })}

        <line x1={RX0} x2={RX1} y1={RY0 - 16} y2={RY0 - 16} stroke="#e2e6ec" />
        <text x={RX1} y={RY0 - 22} textAnchor="end" fontSize={10} fill="#8b95a1"
              fontFamily="var(--mono)">决策时点</text>
        <text x={RX0} y={RY0 - 22} fontSize={10} fill="#8b95a1" fontFamily="var(--mono)">
          {dur(DOMAIN)}前
        </text>
        {timed.map((s, k) => (
          <g key={`r-${s.name}`}>
            <text x={RX0 - 8} y={RY0 + k * 15 + 4} textAnchor="end" fontSize={10}
                  fill="#5c6773" fontFamily="var(--mono)">{s.name}</text>
            <rect x={X(s.window_seconds! + s.offset_seconds)} y={RY0 + k * 15 - 5}
                  width={Math.max(3, X(s.offset_seconds) - X(s.window_seconds! + s.offset_seconds))}
                  height={8} rx={2} fill={KIND_RAIL[s.kind] ?? '#5c6773'} fillOpacity={0.75} />
            {s.baseline_seconds && (
              <rect x={X(s.baseline_seconds + s.offset_seconds)} y={RY0 + k * 15 - 5}
                    width={Math.max(3, X(s.offset_seconds) - X(s.baseline_seconds + s.offset_seconds))}
                    height={8} rx={2} fill="none" stroke="#8a6d1f" strokeWidth={1} />
            )}
          </g>
        ))}
      </svg>
      <p className="foot-note">
        窗口一律结束于决策时点之前，图上向左即向过去。这些是墙钟秒数，不是 session 数；
        本特征最早触及 <span className="mono">{dur(spec.required_lookback_seconds)}</span> 前的数据。
        失败条件：{spec.failure_condition}
      </p>
    </figure>
  )
}
