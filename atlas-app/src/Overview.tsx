import type { Projection } from './types'
import { int, short, when } from './format'
import { VerdictChip } from './Value'

/** 总览层（决定 0003 层一）：两本分母、verdict 分布、库存覆盖、三源新鲜度。 */
export function Overview({ p }: { p: Projection }) {
  const d = p.denominators
  return (
    <>
      <section>
        <div className="section-head">
          <span className="idx">01</span>
          <h2>两本分母</h2>
        </div>
        <p className="muted small" style={{ maxWidth: '72ch' }}>
          提案分母计入全部提案，含被预检挡下的；统计分母只计真正读过 outcome 的检验，
          且只增不减。曲线上的零假设带随后者上升 —— 多重检验的负担来自读了多少次结果，
          不是提了多少个想法。
        </p>
        <div className="tablewrap" style={{ marginTop: 10 }}>
          <table>
            <thead>
              <tr><th>计数</th><th>值</th><th style={{ textAlign: 'left' }}>含义</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>proposal denominator</td>
                <td className="mono">{int(d.proposal_denominator)}</td>
                <td style={{ textAlign: 'left' }}>
                  全部提案，其中预检挡下 {int(d.proposals_screened_out)} 个
                </td>
              </tr>
              <tr>
                <td>statistical denominator</td>
                <td className="mono">{int(d.statistical_denominator)}</td>
                <td style={{ textAlign: 'left' }}>读过 outcome 的检验次数，只增不减</td>
              </tr>
              <tr>
                <td>Study</td>
                <td className="mono">{p.studies.length}</td>
                <td style={{ textAlign: 'left' }}>建立并留下判决的研究单元</td>
              </tr>
              <tr>
                <td>中止轮次</td>
                <td className="mono">{p.aborted_rounds.length}</td>
                <td style={{ textAlign: 'left' }}>有事件但未建立 Study（如输出无法解析）</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <div className="section-head"><span className="idx">02</span><h2>Verdict 分布</h2></div>
        <div className="chips">
          {Object.entries(p.verdicts).map(([k, v]) => (
            <div className="chip" key={k}>
              <span className="k"><VerdictChip verdict={k} /></span>
              <span className="v">{v}</span>
            </div>
          ))}
        </div>
        <p className="muted small" style={{ marginTop: 10, maxWidth: '72ch' }}>
          五种 verdict 都是合法完整产出。underpowered 与 blocked 同样是结论，不是失败；
          调度动作与 verdict 分开记录，见各 Study 的 next_action。
        </p>
      </section>

      <section>
        <div className="section-head">
          <span className="idx">03</span><h2>库存覆盖（机制族 × 数据源 × 时域）</h2>
        </div>
        {p.coverage.length ? (
          <div className="tablewrap">
            <table>
              <thead>
                <tr><th>机制族</th><th>数据源</th><th>时域</th><th>Study</th>
                  <th style={{ textAlign: 'left' }}>verdict 构成</th></tr>
              </thead>
              <tbody>
                {p.coverage.map((c, i) => (
                  <tr key={i}>
                    <td>{c.family}</td><td>{c.source}</td><td>{c.horizon}</td>
                    <td className="mono">{c.studies}</td>
                    <td style={{ textAlign: 'left' }}>
                      {Object.entries(c.verdicts).map(([k, v]) => (
                        <span key={k} style={{ marginRight: 8 }}>
                          <VerdictChip verdict={k} /> <span className="mono">{v}</span>
                        </span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (<p className="muted small">尚无已判决的 Study。</p>)}
      </section>

      <section>
        <div className="section-head"><span className="idx">04</span><h2>三源数据新鲜度</h2></div>
        <div className="tablewrap">
          <table>
            <thead>
              <tr><th>数据源</th><th>状态</th><th>覆盖末日</th><th>manifest 指纹</th>
                <th>扫描时间</th><th>findings</th></tr>
            </thead>
            <tbody>
              {p.data_freshness.map((s) => (
                <tr key={s.source_id}>
                  <td>{s.source_id}</td><td>{s.status}</td>
                  <td className="mono">{s.coverage_end ?? '—'}</td>
                  <td className="mono">{short(s.fingerprint)}</td>
                  <td className="mono">{when(s.scanned_at)}</td>
                  <td className="mono">{s.findings ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted small" style={{ marginTop: 8 }}>
          新鲜度取自 M1 manifest 自身记录的指纹与覆盖末日；Atlas 不扫描源数据目录，
          也不触发采集。
        </p>
      </section>

      {p.service && (
        <section>
          <div className="section-head"><span className="idx">05</span><h2>Research Service</h2></div>
          <div className="panel">
            <dl className="kv">
              {Object.entries(p.service).map(([k, v]) => (
                <div key={k} style={{ display: 'contents' }}>
                  <dt>{k}</dt>
                  <dd>{typeof v === 'object' ? JSON.stringify(v) : String(v ?? '—')}</dd>
                </div>
              ))}
            </dl>
            <p className="muted small" style={{ marginTop: 8 }}>
              Service 只有 running / paused / shutdown 三态，没有 completed：
              研究服务不会「完成」，只会被人停下。
            </p>
          </div>
        </section>
      )}

      <section>
        <div className="section-head"><span className="idx">06</span><h2>账本完整性</h2></div>
        <div className="panel">
          <dl className="kv">
            <dt>事件数</dt><dd className="mono">{p.chain.events}</dd>
            <dt>哈希链</dt>
            <dd>{p.chain.intact ? '完整' : `断裂于 seq ${p.chain.broken_at.join(', ')}`}</dd>
            <dt>Atlas 版本</dt><dd className="mono">{p.atlas_version}</dd>
          </dl>
          <p className="muted small" style={{ marginTop: 8 }}>{p.chain.note}</p>
        </div>
      </section>
    </>
  )
}
