import type { Projection } from './types'
import { num } from './format'

/** 判决区：全页唯一不是卡片的元素，唯一一次 display 字号。
 *
 *  它回答的是这个 app 存在的那个问题的两半：**这一轮找到了什么**，
 *  以及**我为什么可以相信**。两半都直接来自投影，没有一处是前端算的。
 *
 *  它在 DOM 次序与字号上都排在开场抽签之前 —— 抽签够不到它。
 *  一次没有发现的搜索，与一次有发现的搜索，在这里得到完全相同的版式与字重，
 *  只有句子不同：这一轮产出的是一个可核验的否定，那是完整的结果，不是故障。
 */
export function Slab({ p }: { p: Projection }) {
  const v = p.search_verdict
  const d = p.denominators
  const order = ['candidate', 'blocked', 'null', 'underpowered', 'error']
  return (
    <header className="slab">
      <div className="col">
        <p className="eyebrow">
          <span>ARAD · RESEARCH ATLAS</span>
          <span>只读投影</span>
          <span>{v?.family ?? '—'}</span>
        </p>

        <h1 className="verdict-line">
          {v?.headline ?? '这份账本里还没有走到判决的研究。'}
        </h1>

        <p className="verdict-deck">
          共 <b>{p.studies.length}</b> 个版本沿 <b>{p.lineage.length}</b> 条链演化，
          其中 <b>{d.statistical_denominator}</b> 次读了 outcome。
        </p>

        <div className="tally">
          {order.map((k) => (
            <span key={k} className={p.verdicts[k] ? '' : 'zero'}>
              {k}<b>{p.verdicts[k] ?? 0}</b>
            </span>
          ))}
        </div>

        {v && v.null_threshold !== null && <NoiseFloor v={v} />}

        {p.key_moments.find((m) => m.label.includes('读 outcome')) && (
          <p className="foot-note">
            {p.studies.length} 个版本、{d.statistical_denominator} 次检验：
            {p.key_moments.find((m) => m.label.includes('读 outcome'))?.why}
          </p>
        )}

        {v?.stopped_because && (
          <p className="settled">
            这一轮停在 <b>{v.stopped_because}</b>
            {v.human_review_required && <>，并已<b>请求人工复核</b></>}。
            服务不会自己判定「这里没戏」——「该不该继续找」是人的判断。
          </p>
        )}

        <p className="trust">
          <span className={p.chain.intact ? '' : 'bad'}>
            哈希链{p.chain.intact ? '完整' : `断裂于 seq ${p.chain.broken_at.join(', ')}`}
          </span>
          <span>账本事件 {p.chain.events}</span>
          <span>提案分母 {d.proposal_denominator}</span>
          <span>已扫描源 {p.data_freshness.filter((s) => s.status === '已扫描').length}</span>
          <span>Atlas {p.atlas_version}</span>
        </p>
      </div>
    </header>
  )
}

/** 噪声地板对照：两个数由**位置**比较，不由文字断言谁大谁小。
 *  斜纹区读作「这一段不是观测，是期望」，与实心的观测条在材质上分开。 */
function NoiseFloor({ v }: { v: NonNullable<Projection['search_verdict']> }) {
  const best = v.best_value
  const band = v.null_threshold as number
  const W = 520
  const domain = Math.max(best, band) * 1.18 || 1
  const X = (x: number) => (x / domain) * W
  return (
    <figure className="floor">
      <figcaption className="k">
        这一族最好的一次，与同样 {v.statistical_denominator} 次检验在纯噪声上的期望
      </figcaption>
      <svg viewBox={`0 0 ${W} 48`} width="100%" role="img"
           aria-label={`最好的一次 ${num(best, 3)}；同样 ${v.statistical_denominator} 次检验在纯噪声上的期望 ${num(band, 3)}`}>
        <defs>
          <pattern id="nullhatch" width="6" height="6" patternUnits="userSpaceOnUse"
                   patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke="#737d8c" strokeWidth="1"
                  strokeOpacity=".3" />
          </pattern>
        </defs>
        <rect x={X(band)} y="6" width={W - X(band)} height="22" fill="url(#nullhatch)" />
        <rect x="0" y="6" width={X(best)} height="22" rx="1" fill="#3f5d8a" />
        <line x1={X(band)} x2={X(band)} y1="0" y2="34" stroke="#737d8c" strokeWidth="1.5"
              strokeDasharray="4 3" />
        <text x={X(best) - 7} y="23" textAnchor="end" fontSize="12.5" fill="#fff"
              fontFamily="var(--mono)">{num(best, 3)}</text>
        {/* 标签靠右时改为右对齐，否则会被 viewBox 切掉 */}
        <text x={X(band) > W * 0.62 ? X(band) - 7 : X(band) + 7} y="45"
              textAnchor={X(band) > W * 0.62 ? 'end' : 'start'}
              fontSize="11" fill="#5c6773" fontFamily="var(--mono)">
          {num(band, 3)}　纯噪声期望
        </text>
      </svg>
      <p className="foot-note" style={{ marginTop: 6 }}>{v.caveat}</p>
    </figure>
  )
}
