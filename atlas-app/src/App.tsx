import { useEffect, useRef, useState } from 'react'
import { Cockpit } from './Cockpit'
import { Live } from './Live'
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

const TABS = [
  { id: 'cockpit', label: '驾驶舱' },
  { id: 'live', label: '实时' },
  { id: 'replay', label: '回放' },
  { id: 'evolution', label: '演化' },
  { id: 'matrix', label: '矩阵' },
  { id: 'cards', label: '因子卡' },
  { id: 'overview', label: '总览' },
  { id: 'process', label: '过程' },
  { id: 'snapshots', label: '快照' },
] as const

export function App({ loaded }: { loaded: Loaded }) {
  const p = loaded.projection
  const [tab, setTab] = useState<(typeof TABS)[number]['id']>('cockpit')
  // 判决区滚出视野后，把它压缩成 tabs 里的一行 —— 结论不该只在第一屏存在
  const [condensed, setCondensed] = useState(false)
  const sentinel = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    const node = sentinel.current
    if (!node || typeof IntersectionObserver === 'undefined') return
    const io = new IntersectionObserver(([e]) => setCondensed(!e.isIntersecting))
    io.observe(node)
    return () => io.disconnect()
  }, [])
  return (
    <>
      <Slab p={p} />
      {loaded.mode === 'api' && loaded.runs.length > 0 && (
        <div className="col runbar" style={{ padding: 'var(--s3) var(--s5)' }}>
          <span className="muted small">运行：</span>
          <select value={loaded.runId ?? ''} onChange={(e) => switchRun(e.target.value)}>
            {loaded.runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id}　·　{r.studies} 个 Study　·　{r.cards} 张卡
              </option>
            ))}
          </select>
          <span className="muted small">共 {loaded.runs.length} 次运行</span>
        </div>
      )}
      <div ref={sentinel} aria-hidden="true" />

      <nav className="tabs" data-condensed={condensed ? 'true' : 'false'}>
        <div className="col">
          {TABS.map((t) => (
            <button key={t.id} aria-selected={tab === t.id} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
          <span className="verdict-mini">
            CANDIDATE <b>{p.verdicts.candidate ?? 0}</b>　·　
            <b>{p.denominators.statistical_denominator}</b> 次检验　·　
            链<b>{p.chain.intact ? '完整' : '断裂'}</b>
          </span>
        </div>
      </nav>

      {tab === 'cockpit' && <main className="full-bleed"><Cockpit /></main>}
      <main>
        <div className="col">
          {tab === 'replay' && <Replay p={p} />}
          {tab === 'evolution' && <Evolution p={p} />}
          {tab === 'matrix' && <Matrix p={p} />}
          {tab === 'cards' && <Cards cards={loaded.cards} />}
          {tab === 'overview' && <Overview p={p} />}
          {tab === 'live' && <Live />}
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
