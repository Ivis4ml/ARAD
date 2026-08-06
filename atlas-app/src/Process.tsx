import type { Projection } from './types'
import { Value } from './Value'
import { when } from './format'

/** 过程层（决定 0003 层二）：Episode 的展开收束与不属于任何 Study 的产出。 */
export function Process({ p }: { p: Projection }) {
  return (
    <>
      <section>
        <div className="section-head"><span className="idx">01</span><h2>Search Episode</h2></div>
        {p.episodes.length === 0 && <p className="muted small">账本中尚无 Episode 记录。</p>}
        {p.episodes.map((ep) => (
          <details key={ep.episode_id} open>
            <summary>
              Episode {ep.episode_id}　
              <span className="mono small muted">
                {when(ep.started_at)} → {when(ep.ended_at) || '（未结束）'}
              </span>
            </summary>
            <div>
              {ep.summary && (
                <dl className="kv">
                  <dt>轮数</dt><dd className="mono">{String(ep.summary.rounds ?? '—')}</dd>
                  <dt>结束原因</dt><dd className="mono">{String(ep.summary.ended_because ?? '—')}</dd>
                  <dt>各类结局</dt><dd><Value node={ep.summary.outcomes} /></dd>
                  <dt>预算</dt><dd><Value node={ep.summary.budget} /></dd>
                </dl>
              )}
              <p className="muted small">
                预算耗尽只结束 Episode 并交回剩余预算，Research Service 不因此停止。
              </p>
              {ep.studies.length > 0 && (
                <p className="small">
                  触及的 Study：{ep.studies.map((s) => (
                    <code key={s} className="mono" style={{ marginRight: 8 }}>{s}</code>
                  ))}
                </p>
              )}
              {ep.events.length > 0 && (
                <>
                  <h4 style={{ marginTop: 12 }}>不属于任何 Study 的事件</h4>
                  <p className="muted small">
                    原语缺口声明与 provider 故障本来就没有 Study 归属。按 Study 分组会让
                    它们整批消失，而它们恰恰是第一版最有信息量的产出。
                  </p>
                  {ep.events.map((e) => (
                    <div key={e.seq} style={{ marginTop: 8 }}>
                      <p className="small">
                        <span className="mono muted">#{e.seq}</span>　<strong>{e.label}</strong>
                      </p>
                      <Value node={e.payload} />
                    </div>
                  ))}
                </>
              )}
            </div>
          </details>
        ))}
      </section>

      {p.aborted_rounds.length > 0 && (
        <section>
          <div className="section-head">
            <span className="idx">02</span><h2>中止轮次（未建立 Study）</h2>
          </div>
          <p className="muted small">
            这些轮次带着 study_id 入账，但没有 study_created，因而不是 Study。
            它们是预期状态，不是账本缺口。
          </p>
          <div className="tablewrap" style={{ marginTop: 8 }}>
            <table>
              <thead><tr><th>标识</th><th style={{ textAlign: 'left' }}>中止于</th><th>时间</th></tr></thead>
              <tbody>
                {p.aborted_rounds.map((a) => (
                  <tr key={a.study_id}>
                    <td className="mono">{a.study_id}</td>
                    <td style={{ textAlign: 'left', whiteSpace: 'normal' }}>{a.reason}</td>
                    <td className="mono">{when(a.at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  )
}
