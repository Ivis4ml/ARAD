/** 通用 payload 渲染：把账本里存的任意结构显示成嵌套列表。
 *  数字按位数显示，原值保留在 title 里；Atlas 不改变任何数值。 */
export function Value({ node }: { node: unknown }): JSX.Element {
  if (node === null || node === undefined) return <span className="muted">—</span>
  if (typeof node === 'boolean') return <span className="mono">{node ? 'true' : 'false'}</span>
  if (typeof node === 'number') {
    const text = Number.isInteger(node) ? String(node) : node.toPrecision(6)
    return <span className="mono" title={String(node)}>{text}</span>
  }
  if (typeof node === 'string') {
    return node.length === 64 ? <span className="mono">{node}</span> : <>{node}</>
  }
  if (Array.isArray(node)) {
    if (!node.length) return <span className="muted">（空）</span>
    return (
      <ul className="tree">
        {node.map((v, i) => (<li key={i}><Value node={v} /></li>))}
      </ul>
    )
  }
  return (
    <ul className="tree">
      {Object.entries(node as Record<string, unknown>).map(([k, v]) => (
        <li key={k}><span className="k">{k}：</span><Value node={v} /></li>
      ))}
    </ul>
  )
}

export function VerdictChip({ verdict }: { verdict: string }): JSX.Element {
  if (!verdict) return <span className="muted small">未判决</span>
  return <span className={`verdict v-${verdict}`}>{verdict}</span>
}
