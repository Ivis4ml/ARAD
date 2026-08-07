import type { Study } from './types'
import { Mechanism } from './Mechanism'
import { Value, VerdictChip } from './Value'
import { num, when } from './format'

/** 快照层（决定 0003 层三）：判决时刻的完整证据。 */
export function StudyPanel({ study }: { study: Study }) {
  const snap = study.snapshot as Record<string, unknown>
  const evaluation = (snap.evaluation ?? null) as Record<string, unknown> | null
  const effects = (evaluation?.effects ?? null) as Record<string, unknown> | null
  return (
    <>
      {snap.feature_spec ? (
        <section style={{ marginBottom: 'var(--s5)' }}>
          <Mechanism spec={snap.feature_spec as never} />
        </section>
      ) : null}
    <div className="grid2">
      <div>
        <div className="panel">
          <div className="chart-title">
            <h3>{study.mechanism}</h3>
            <VerdictChip verdict={study.verdict} />
          </div>
          <dl className="kv" style={{ marginTop: 10 }}>
            <dt>next_action</dt><dd className="mono">{study.next_action || '—'}</dd>
            <dt>判决时间</dt><dd className="mono">{when(study.decided_at)}</dd>
            <dt>父版</dt>
            <dd className="mono">{study.parent_study_id ?? '（根节点）'}</dd>
            <dt>改动</dt><dd>{study.change_summary || <span className="muted">未声明</span>}</dd>
            <dt>理由</dt><dd>{study.rationale}</dd>
          </dl>
          {study.forward_reserved && (
            <p className="notice">
              forward 段：<strong>预约待裁决</strong>。forward 区间的数据与标签在 Atlas 中
              不可见，此处只显示预约状态，不显示任何尚未到期的结果。
            </p>
          )}
        </div>

        {evaluation ? (
          <>
            <h4 style={{ margin: '18px 0 6px' }}>评价机结果</h4>
            <div className="panel">
              <dl className="kv">
                <dt>slope</dt><dd className="mono">{num(effects?.slope as number, 6)}</dd>
                <dt>t_stat</dt><dd className="mono">{num(effects?.t_stat as number, 4)}</dd>
                <dt>MDE @2.8se</dt>
                <dd className="mono">{num(effects?.mde_at_2p8_se as number, 6)}</dd>
              </dl>
              <h4 style={{ marginTop: 14 }}>IC</h4>
              <Value node={effects?.ic} />
              <h4 style={{ marginTop: 14 }}>Sharpe（pre-cost）</h4>
              <Value node={effects?.performance} />
              <h4 style={{ marginTop: 14 }}>未通过的预注册闸门</h4>
              <Value node={evaluation.blocked_reasons} />
              <h4 style={{ marginTop: 14 }}>覆盖</h4>
              <Value node={evaluation.coverage} />
              <details>
                <summary>诊断与独立性</summary>
                <div><Value node={evaluation.diagnostics} /></div>
              </details>
              <p className="muted small" style={{ marginTop: 8 }}>
                以上全部数字由评价机出具并存入账本，Atlas 原样读出，不实现任何统计量。
              </p>
            </div>
          </>
        ) : (
          <p className="notice">
            本 Study 没有评价结果：它在取数或功效预检阶段就已判决。
          </p>
        )}
      </div>

      <div>
        <h4>时间线</h4>
        <div className="panel">
          <ol className="timeline">
            {study.timeline.map((t) => (
              <li key={t.seq}>
                <span className="mono muted">#{t.seq}</span>　{t.label}
              </li>
            ))}
          </ol>
        </div>
        <h4 style={{ marginTop: 16 }}>冻结的假设</h4>
        <details><summary>提案</summary><div><Value node={snap.proposal} /></div></details>
        <details><summary>Hypothesis Lock</summary>
          <div><Value node={snap.hypothesis_lock} /></div></details>
        <details><summary>Confirmatory Lock</summary>
          <div><Value node={snap.confirmatory_lock} /></div></details>
        <details><summary>规格原文与工件哈希</summary>
          <div><Value node={snap.feature_spec} /></div></details>
        <details><summary>判决当时可见的数据范围</summary>
          <div><Value node={snap.visible_data_range} /></div></details>
      </div>
    </div>
    </>
  )
}
