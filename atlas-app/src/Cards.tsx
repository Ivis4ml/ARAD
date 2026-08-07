import { useState } from 'react'
import type { Card } from './source'
import { dur, num } from './format'

const STATUS_TEXT: Record<string, string> = {
  discovery_only: '只有发现段证据',
  sealed_survived: '封闭段上保住了',
  sealed_failed: '封闭段上没保住',
  sealed_underpowered: '封闭段上判不了',
}

/** 因子卡：公式、意义、证据、以及由规格确定性生成的代码。
 *
 *  代码不是「另一份实现」，是同一份语义 —— 有合同测试钉死它与解释器逐位相同。
 *  因此这一页给出的公式与代码之间不可能各说各话。
 */
export function Cards({ cards }: { cards: Card[] }) {
  const [open, setOpen] = useState<string | null>(cards[0]?.feature_id ?? null)
  if (!cards.length) {
    return (
      <p className="muted small">
        这次运行没有因子卡。卡片由连续研究流程产出（<code>arad episode service</code>），
        单文件模式下需要经运行目录才能看到。
      </p>
    )
  }
  return (
    <section>
      <div className="section-head">
        <span className="idx">01</span><h2>因子卡</h2>
      </div>
      <p className="muted small" style={{ maxWidth: '76ch' }}>
        每张卡带三样东西：这个因子<strong>意味着什么</strong>、它的<strong>公式</strong>、
        以及由冻结规格<strong>确定性生成</strong>的代码。代码不是另一份实现，
        是同一份语义 —— 有合同测试钉死它与解释器逐位相同，因此说明与代码不可能各说各话。
      </p>

      <div className="tablewrap" style={{ marginTop: 'var(--s4)' }}>
        <table>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>因子</th><th>状态</th>
              <th>分类法</th><th>发现段 t</th><th>封闭段 t</th><th>回看</th>
            </tr>
          </thead>
          <tbody>
            {cards.map((c) => (
              <tr key={c.feature_id} className={`clickable${open === c.feature_id ? ' selected' : ''}`}
                  onClick={() => setOpen(c.feature_id)}>
                <td style={{ textAlign: 'left' }} className="mono">{c.feature_id}</td>
                <td>{STATUS_TEXT[c.status] ?? c.status}</td>
                <td>{c.taxonomy_clean ? '干净' : '不干净'}</td>
                <td className="mono">{num(c.discovery?.t_stat as number, 3)}</td>
                <td className="mono">{num((c.sealed?.t_stat as number) ?? null, 3)}</td>
                <td className="mono">{dur(c.required_lookback_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {cards.filter((c) => c.feature_id === open).map((c) => (
        <div key={c.feature_id} style={{ marginTop: 'var(--s5)' }}>
          <h3>这个因子意味着什么</h3>
          <p className="panel" style={{ marginTop: 'var(--s2)', lineHeight: 1.8 }}>
            {c.meaning}
          </p>

          <h3 style={{ marginTop: 'var(--s5)' }}>公式</h3>
          <pre className="code">{c.formula.join('\n')}</pre>

          <h3 style={{ marginTop: 'var(--s5)' }}>失败条件</h3>
          <p className="panel">{c.failure_condition}</p>

          <details style={{ marginTop: 'var(--s4)' }}>
            <summary>生成的代码（{c.code.split('\n').length} 行，可直接运行）</summary>
            <div><pre className="code">{c.code}</pre></div>
          </details>
        </div>
      ))}
    </section>
  )
}
