import { useState } from 'react'
import type { Projection } from './types'
import { Overview } from './Overview'
import { Evolution } from './Evolution'
import { Process } from './Process'
import { StudyPanel } from './StudyPanel'
import { VerdictChip } from './Value'

const TABS = [
  { id: 'evolution', label: '演化' },
  { id: 'overview', label: '总览' },
  { id: 'process', label: '过程' },
  { id: 'snapshots', label: '快照' },
] as const

export function App({ p }: { p: Projection }) {
  const [tab, setTab] = useState<(typeof TABS)[number]['id']>('evolution')
  return (
    <>
      <header className="hero">
        <div className="col">
          <span className="eyebrow">ARAD · Research Atlas</span>
          <h1 style={{ marginTop: 12 }}>研究过程的只读投影</h1>
          <p className="lede">
            Atlas 读账本，不写账本，不重算任何统计量。每个数字都来自评价机存下的记录；
            forward 段的数据与标签在这里同样不可见，只显示预约状态。
          </p>
          <div className="chips">
            <div className={`chip ${p.chain.intact ? 'ok' : 'bad'}`}>
              <span className="k">哈希链</span>
              <span className="v">{p.chain.intact ? '完整' : '断裂'}</span>
            </div>
            <div className="chip">
              <span className="k">账本事件</span><span className="v">{p.chain.events}</span>
            </div>
            <div className="chip">
              <span className="k">Study</span><span className="v">{p.studies.length}</span>
            </div>
            <div className="chip">
              <span className="k">提案分母</span>
              <span className="v">{p.denominators.proposal_denominator}</span>
            </div>
            <div className="chip">
              <span className="k">统计分母</span>
              <span className="v">{p.denominators.statistical_denominator}</span>
            </div>
            <div className="chip">
              <span className="k">演化链</span><span className="v">{p.lineage.length}</span>
            </div>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <div className="col">
          {TABS.map((t) => (
            <button key={t.id} aria-selected={tab === t.id} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      <main>
        <div className="col">
          {tab === 'evolution' && <Evolution p={p} />}
          {tab === 'overview' && <Overview p={p} />}
          {tab === 'process' && <Process p={p} />}
          {tab === 'snapshots' && (
            <>
              {p.studies.length === 0 && <p className="muted">尚无 Study。</p>}
              {p.studies.map((s) => (
                <details key={s.study_id}>
                  <summary>
                    <VerdictChip verdict={s.verdict} />{'\u3000'}
                    <span className="mono">{s.study_id}</span>　{s.mechanism.slice(0, 70)}
                  </summary>
                  <div><StudyPanel study={s} /></div>
                </details>
              ))}
            </>
          )}
        </div>
      </main>

      <footer>
        <div className="col">
          每次渲染都重算整条哈希链，Atlas 因此也是账本完整性的持续检验。
          浮点数按有效位显示，鼠标悬停可见原值；机器可读副本见同目录的 atlas.json。
          Atlas {p.atlas_version}。
        </div>
      </footer>
    </>
  )
}
