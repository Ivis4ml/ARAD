import type { Projection } from './types'
import { num } from './format'

/** 信号相关矩阵：这些想法是不是同一个想法。
 *
 *  **它不读 outcome**，因此不消耗统计分母，也不改变任何判决 —— 它只比信号之间。
 *  它存在的理由是把「零假设带偏严」那句告诫变成一个可看的数：带按检验独立绘制，
 *  而这些变体彼此高度相关。
 */
export function Matrix({ p }: { p: Projection }) {
  const m = p.signal_matrix
  if (!m || !m.defined) {
    return (
      <p className="muted small">
        这一族还没有两个以上可求值的特征，相关矩阵无从谈起。
      </p>
    )
  }
  const names = m.names
  const eff = m.effective_signals
  const short = (s: string) => s.replace(/^auto_/, '').slice(0, 30)
  const cell = (v: number) => {
    if (!Number.isFinite(v)) return { background: 'transparent', color: '#c2c8d0' }
    const a = Math.min(1, Math.abs(v))
    return {
      background: v >= 0
        ? `rgba(23,112,138,${(a * 0.72).toFixed(3)})`
        : `rgba(138,109,31,${(a * 0.72).toFixed(3)})`,
      color: a > 0.55 ? '#fff' : 'var(--ink)',
    }
  }
  return (
    <>
      <section>
        <div className="section-head">
          <span className="idx">01</span><h2>这些想法是不是同一个想法</h2>
        </div>
        <p className="muted small" style={{ maxWidth: '76ch' }}>
          搜索一共留下 <b>{names.length}</b> 个互异特征，两两之间的秩相关如下。
          这一步<strong>只比信号之间，不读 outcome</strong>，因此它不消耗统计分母，
          也不改变任何判决。
        </p>

        <div className="chips" style={{ marginTop: 'var(--s3)' }}>
          <div className="chip">
            <span className="k">互异特征</span><span className="v">{names.length}</span>
          </div>
          <div className="chip">
            <span className="k">非对角 |ρ| 均值</span>
            <span className="v">{num(m.mean_abs_offdiagonal, 3)}</span>
          </div>
          {eff?.defined && (
            <div className="chip">
              <span className="k">相当于独立信号</span>
              <span className="v">{num(eff.effective_independent_signals, 2)}</span>
            </div>
          )}
        </div>

        <div className="tablewrap" style={{ marginTop: 'var(--s4)' }}>
          <table className="matrix">
            <thead>
              <tr>
                <th />
                {names.map((_, j) => (<th key={j} className="mono">{j}</th>))}
              </tr>
            </thead>
            <tbody>
              {m.matrix.map((row, i) => (
                <tr key={i}>
                  <th className="rowhead">
                    <span className="mono muted">{i}</span> {short(names[i])}
                  </th>
                  {row.map((v, j) => (
                    <td key={j} style={cell(v)} title={`${names[i]} × ${names[j]}：${num(v, 4)}`}>
                      {Number.isFinite(v) ? num(v, 2) : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {eff?.defined && (
          <p className="notice">
            这 {names.length} 个特征相当于
            <strong> {num(eff.effective_independent_signals, 2)} </strong>
            个独立信号（{eff.method}）。
            <strong>这是关于信号的陈述，不是关于检验次数的陈述</strong>：零假设带按检验
            独立绘制因而偏严，但特征与检验并非一一对应 —— 同一个特征可能被检验多次 ——
            把两者混为一谈会把带压得过低，让一个空结果看起来像发现。因此这个数只在这里
            给出，不用来重绘那条带。
          </p>
        )}
      </section>
    </>
  )
}
