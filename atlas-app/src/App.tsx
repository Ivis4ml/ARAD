import { useState } from 'react'
import { Cockpit } from './Cockpit'
import { Overview } from './Overview'
import { Evolution } from './Evolution'
import { Cards } from './Cards'
import { Matrix } from './Matrix'
import { Replay } from './Replay'
import { Process } from './Process'
import { StudyPanel } from './StudyPanel'
import type { Loaded } from './source'
import { switchRun } from './source'
import { Slab } from './Slab'
import { VerdictChip } from './Value'

/** 全屏深色工作台。驾驶舱是主视图，其余视图是左侧导航里的分析与档案。
 *
 * 旧形态是「浅色文档里嵌一块黑岛」；现在整个 app 就是驾驶舱：
 * 顶栏（品牌 + 运行选择 + 结论摘要）、左导航（224px，参照实现的原尺寸）、
 * 右侧舞台（当前视图，切换带入场动画）。旧视图靠设计变量重映射整体变暗。
 */

const NAV: { group: string; items: { id: string; label: string }[] }[] = [
  { group: '实时', items: [{ id: 'cockpit', label: '驾驶舱' }] },
  {
    group: '分析',
    items: [
      { id: 'evolution', label: '演化' },
      { id: 'matrix', label: '矩阵' },
      { id: 'cards', label: '因子卡' },
    ],
  },
  {
    group: '档案',
    items: [
      { id: 'replay', label: '回放' },
      { id: 'overview', label: '总览' },
      { id: 'process', label: '过程' },
      { id: 'snapshots', label: '快照' },
    ],
  },
]

export function App({ loaded }: { loaded: Loaded }) {
  const p = loaded.projection
  const [tab, setTab] = useState('cockpit')
  return (
    <div className="app">
      <header className="app-header">
        <span className="app-brand">ARAD</span>
        <span className="app-sub mono">research atlas</span>
        {loaded.mode === 'api' && loaded.runs.length > 0 && (
          <select className="app-run mono" value={loaded.runId ?? ''}
                  onChange={(e) => switchRun(e.target.value)}>
            {loaded.runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} · {r.studies} studies
              </option>
            ))}
          </select>
        )}
        <span className="app-spacer" />
        <span className="app-mini mono">
          CANDIDATE <b>{p.verdicts.candidate ?? 0}</b>
          <i className="sb-sep" />
          <b>{p.denominators.statistical_denominator}</b> 次检验
          <i className="sb-sep" />
          链<b>{p.chain.intact ? '完整' : '断裂'}</b>
        </span>
      </header>

      <div className="app-body">
        <nav className="app-side">
          {NAV.map((g) => (
            <div key={g.group}>
              <div className="app-nav-group">{g.group}</div>
              {g.items.map((t) => (
                <button key={t.id} className={`app-nav-item ${tab === t.id ? 'sel' : ''}`}
                        onClick={() => setTab(t.id)}>
                  {t.label}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <main className="app-stage" key={tab}>
          {tab === 'cockpit' && <Cockpit />}
          {tab === 'replay' && <div className="stage-doc"><Replay p={p} /></div>}
          {tab === 'evolution' && <div className="stage-doc"><Evolution p={p} /></div>}
          {tab === 'matrix' && <div className="stage-doc"><Matrix p={p} /></div>}
          {tab === 'cards' && <div className="stage-doc"><Cards cards={loaded.cards} /></div>}
          {tab === 'overview' && (
            <div className="stage-doc"><Slab p={p} /><Overview p={p} /></div>
          )}
          {tab === 'process' && <div className="stage-doc"><Process p={p} /></div>}
          {tab === 'snapshots' && (
            <div className="stage-doc">
              {p.studies.length === 0 && <p className="muted">尚无 Study。</p>}
              {p.studies.map((s) => (
                <details key={s.study_id}>
                  <summary>
                    <VerdictChip verdict={s.verdict} />{'　'}
                    <span className="mono">{s.study_id}</span>　{s.mechanism.slice(0, 70)}
                  </summary>
                  <div><StudyPanel study={s} /></div>
                </details>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
